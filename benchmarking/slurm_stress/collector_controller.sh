#!/bin/bash
# collector_controller.sh
#
# This script runs on the Slurm controller node to collect scheduling and
# system load statistics.
#
# USAGE:
# 1. Save this script as "collector_controller.sh" on your Slurm controller.
# 2. Make it executable: chmod +x collector_controller.sh
# 3. Before starting your first pipeline, run it in the background:
#    nohup ./collector_controller.sh > collector.log 2>&1 &
# 4. After your last pipeline finishes, stop the script by finding its
#    Process ID (ps aux | grep collector_controller) and using kill.
#    Or, more simply: pkill -f collector_controller.sh

# --- CONFIGURATION ---
# Set the interval for data collection, in seconds.
# A 15-30 second interval is reasonable for long-running pipelines.
SLEEP_INTERVAL=15

# Define the output CSV file names.
SDIAG_OUT="slurm_schedule_stats.csv"
NODE_OUT="slurm_node_stats.csv"

# --- SCRIPT START ---
echo "Starting Slurm data collector..."
echo "Press Ctrl+C to stop."

# --- INITIALIZE CSV FILES ---
# Create the sdiag file with headers if it doesn't exist.
# We will parse the key-value pairs from sdiag into columns.
if [ ! -f "$SDIAG_OUT" ]; then
    # Get a sample line to dynamically create headers
    HEADERS="timestamp,"$(sdiag | grep "Main schedule" | head -n1 | sed -e 's/Main schedule statistics (microseconds): //' -e 's/:/ /g' | awk '{for(i=1; i<=NF; i+=2) printf "%s,", $i}' | sed 's/,$//')
    echo "$HEADERS" > "$SDIAG_OUT"
    echo "Created $SDIAG_OUT with headers."
fi

# Create the node stats file with headers if it doesn't exist.
if [ ! -f "$NODE_OUT" ]; then
    echo "timestamp,cpu_user,cpu_system,cpu_idle,cpu_iowait,mem_free_kb,mem_used_kb,load_avg_1m,load_avg_5m,load_avg_15m" > "$NODE_OUT"
    echo "Created $NODE_OUT with headers."
fi


# --- MAIN COLLECTION LOOP ---
while true; do
    # Get a high-precision timestamp (ISO 8601 format)
    TIMESTAMP=$(date --iso-8601=seconds)

    # --- 1. Collect Slurm sdiag Statistics ---
    SDIAG_LINE=$(sdiag | grep "Main schedule")

    if [ -n "$SDIAG_LINE" ]; then
        # Use sed and awk to parse the key:value format into just values.
        # This is robust to changes in the order of stats.
        VALUES=$(echo "$SDIAG_LINE" | sed -e 's/Main schedule statistics (microseconds): //' -e 's/:/ /g' | awk '{for(i=2; i<=NF; i+=2) printf "%s,", $i}' | sed 's/,$//')
        echo "$TIMESTAMP,$VALUES" >> "$SDIAG_OUT"
    fi

    # --- 2. Collect Node Statistics ---
    # We use `vmstat` and `uptime` for a comprehensive, low-overhead snapshot.

    # Get CPU and Memory stats from vmstat.
    # We run it twice with a 1-sec delay to get a proper reading, not an average since boot.
    VMSTAT_DATA=$(vmstat -n 1 2 | tail -n1)
    CPU_USER=$(echo "$VMSTAT_DATA" | awk '{print $13}')
    CPU_SYSTEM=$(echo "$VMSTAT_DATA" | awk '{print $14}')
    CPU_IDLE=$(echo "$VMSTAT_DATA" | awk '{print $15}')
    CPU_IOWAIT=$(echo "$VMSTAT_DATA" | awk '{print $16}')
    MEM_FREE=$(echo "$VMSTAT_DATA" | awk '{print $4}')
    MEM_USED=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    MEM_USED=$((MEM_USED - MEM_FREE))


    # Get Load Average from uptime
    LOAD_AVG=$(uptime | awk -F'load average: ' '{print $2}')
    LOAD_1M=$(echo "$LOAD_AVG" | awk -F, '{print $1}')
    LOAD_5M=$(echo "$LOAD_AVG" | awk -F, '{print $2}')
    LOAD_15M=$(echo "$LOAD_AVG" | awk -F, '{print $3}')

    echo "$TIMESTAMP,$CPU_USER,$CPU_SYSTEM,$CPU_IDLE,$CPU_IOWAIT,$MEM_FREE,$MEM_USED,$LOAD_1M,$LOAD_5M,$LOAD_15M" >> "$NODE_OUT"

    # --- Wait for the next interval ---
    sleep $SLEEP_INTERVAL
done

