#!/bin/bash
# monitor_fairshare.sh

# Output file with timestamp
output_file="fairshare_monitoring_$(date +%Y%m%d_%H%M%S).csv"

# Write header
echo "timestamp,realfairshare,running_jobs" > "$output_file"

echo "Starting fairshare monitoring..."
echo "Data will be saved to: $output_file"
echo "Press Ctrl+C to stop monitoring"

while true; do
    # Get current timestamp
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    # Get fairshare data (6th column where 2nd column matches username)
    realfairshare=$(myfairshare 2>/dev/null | awk -v user="$USER" '$2 == user {print $6}')
    
    # If empty or invalid, set to 0
    if [[ -z "$realfairshare" || ! "$realfairshare" =~ ^[0-9]+\.?[0-9]*$ ]]; then
        realfairshare="0"
    fi
    
    # Get number of running jobs
    running_jobs=$(squeue -u $USER -t RUNNING -h | wc -l)
    
    # Append to CSV
    echo "$timestamp,$realfairshare,$running_jobs" >> "$output_file"
    
    # Display current values
    echo "[$timestamp] RealFairShare: $realfairshare, Running Jobs: $running_jobs"
    
    # Wait 10 seconds
    sleep 10
done
