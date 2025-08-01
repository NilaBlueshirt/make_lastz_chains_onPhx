#!/bin/bash
# slurm_monitor.sh (Corrected Version)
#
# This script runs on the Slurm controller node to collect sdiag scheduling
# statistics and the CPU time of a specified process. It correctly handles
# multi-line output from the sdiag command.
#
# USAGE:
# 1. Save this script as "slurm_monitor.sh" on your Slurm controller.
# 2. Make it executable: chmod +x slurm_monitor.sh
# 3. Run it in the background. The filename will be generated automatically.
#
#    To run WITHOUT process CPU time monitoring:
#    nohup ./slurm_monitor.sh > slurm_monitor.log 2>&1 &
#
#    To run WITH process CPU time monitoring (provide the PID):
#    nohup ./slurm_monitor.sh <PID> > slurm_monitor.log 2>&1 &
#    (e.g., nohup ./slurm_monitor.sh 4170117 > slurm_monitor.log 2>&1 &)
#
# 4. After your collection period, stop the script: pkill -f slurm_monitor.sh

# --- CONFIGURATION ---
# Set the interval for data collection, in seconds.
SLEEP_INTERVAL=15

# The process PID is taken from the first command-line argument.
TARGET_PID="$1"

# --- SCRIPT START ---
# Generate a single output filename based on the current date and time.
DATETIME=$(date +'%Y%m%d_%H%M%S')
OUTPUT_CSV="batch_${DATETIME}.csv"

echo "Starting Slurm monitor..."
echo "Output will be saved to: $OUTPUT_CSV"
if [ -n "$TARGET_PID" ]; then
    echo "Monitoring PID: $TARGET_PID for CPU time."
else
    echo "No PID provided. CPU time will not be collected."
fi
echo "Press Ctrl+C to stop."


# --- HEADER SETUP ---
# Use a robust awk command to extract the block of stats following the "Main schedule" line.
# This works even if the stats are on multiple lines.
# awk logic: set flag 'f' on match, then for subsequent non-empty lines print them, unset flag on empty line.
SDIAG_STATS_BLOCK_FOR_HEADER=$(sdiag | awk '/Main schedule statistics/{f=1;next} f&&NF{print} !NF{f=0}')

SDIAG_HEADERS=""
if [ -n "$SDIAG_STATS_BLOCK_FOR_HEADER" ]; then
    # For headers: cut the part before the ':', trim whitespace, replace space with underscore, and join with commas.
    SDIAG_HEADERS=$(echo "$SDIAG_STATS_BLOCK_FOR_HEADER" | cut -d':' -f1 | sed 's/^[ \t]*//;s/[ \t]*$//' | sed 's/ /_/g' | paste -sd, -)
else
    echo "Warning: Could not get sdiag output for header generation. sdiag stats will be skipped."
fi

# Build the final header string
FINAL_HEADER="timestamp"
if [ -n "$SDIAG_HEADERS" ]; then
    FINAL_HEADER+=",$SDIAG_HEADERS"
fi
# Conditionally add the cputime header
if [ -n "$TARGET_PID" ]; then
    FINAL_HEADER+=",cputime_s"
fi
echo "$FINAL_HEADER" > "$OUTPUT_CSV"


# --- MAIN COLLECTION LOOP ---
while true; do
    # Get a high-precision timestamp (ISO 8601 format)
    TIMESTAMP=$(date --iso-8601=seconds)

    # --- 1. Collect Slurm sdiag Statistics ---
    SDIAG_VALUES=""
    if [ -n "$SDIAG_HEADERS" ]; then # Only try to get values if we have headers
        # Use the same robust awk command to get the block of stats
        SDIAG_STATS_BLOCK=$(sdiag | awk '/Main schedule statistics/{f=1;next} f&&NF{print} !NF{f=0}')

        if [ -n "$SDIAG_STATS_BLOCK" ]; then
            # For values: cut the part after the ':', trim whitespace, and join with commas.
            SDIAG_VALUES=$(echo "$SDIAG_STATS_BLOCK" | cut -d':' -f2 | sed 's/^[ \t]*//;s/[ \t]*$//' | paste -sd, -)
        else
            # If sdiag fails, create empty placeholders to keep CSV structure
            NUM_COMMAS=$(echo "$SDIAG_HEADERS" | tr -cd ',' | wc -c)
            SDIAG_VALUES=$(printf ',%.0s' $(seq 1 $NUM_COMMAS))
        fi
    fi

    # --- 2. Conditionally Collect Process CPU Time ---
    CPU_TIME_VALUE=""
    if [ -n "$TARGET_PID" ]; then
        CPU_TIME_STR=$(ps -p $TARGET_PID -o cputime --no-headers | xargs)

        CPU_SECONDS=$(echo "$CPU_TIME_STR" | awk -F'[-:]' '{
            if (NF==4) { print $1*86400 + $2*3600 + $3*60 + $4 }      # DD-HH:MM:SS
            else if (NF==3) { print $1*3600 + $2*60 + $3 }           # HH:MM:SS
            else if (NF==2) { print $1*60 + $2 }                       # MM:SS
            else if (NF==1 && $1 ~ /^[0-9.]+$/) { print $1 }          # SS
            else { print 0 } # Default to 0 if format is unexpected or process not found
        }')
        CPU_TIME_VALUE=",$CPU_SECONDS"
    fi

    # --- 3. Build and write the final data line ---
    FINAL_LINE="$TIMESTAMP"
    if [ -n "$SDIAG_VALUES" ]; then
        FINAL_LINE+=",$SDIAG_VALUES"
    fi
    FINAL_LINE+="$CPU_TIME_VALUE"
    echo "$FINAL_LINE" >> "$OUTPUT_CSV"

    # --- Wait for the next interval ---
    sleep $SLEEP_INTERVAL
done

