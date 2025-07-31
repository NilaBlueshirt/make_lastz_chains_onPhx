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
    
    # Get RealFairShare using myfairshare
    realfairshare=$(myfairshare | grep "^[[:space:]]*$USER" | awk '{print $NF}')
    
    # Get number of running jobs
    running_jobs=$(squeue -u $USER -t RUNNING -h | wc -l)
    
    # Append to CSV
    echo "$timestamp,$realfairshare,$running_jobs" >> "$output_file"
    
    # Optional: Display current values
    echo "[$timestamp] RealFairShare: $realfairshare, Running Jobs: $running_jobs"
    
    # Wait 10 seconds
    sleep 10
done
