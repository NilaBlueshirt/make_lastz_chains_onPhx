#!/usr/bin/env python3
"""
Simplified seff parser that extracts only essential columns:
Job_ID, State, CPU_Efficiency, Memory_Efficiency, Wall_Time_Hours
"""

import subprocess
import pandas as pd
import re
import sys
import argparse

def slurm_time_to_hours(time_str):
    """
    Convert Slurm time format to hours.
    Handles formats: DD-HH:MM:SS, HH:MM:SS, MM:SS, SS
    """
    if not time_str or time_str == 'None':
        return None
    
    try:
        # Remove any whitespace
        time_str = time_str.strip()
        
        # Check for days (DD-HH:MM:SS format)
        if '-' in time_str:
            days, time_part = time_str.split('-')
            days = int(days)
            time_parts = time_part.split(':')
        else:
            days = 0
            time_parts = time_str.split(':')
        
        # Parse time components
        if len(time_parts) == 3:
            hours, minutes, seconds = map(int, time_parts)
        elif len(time_parts) == 2:
            hours = 0
            minutes, seconds = map(int, time_parts)
        elif len(time_parts) == 1:
            hours = minutes = 0
            seconds = int(time_parts[0])
        else:
            return None
        
        # Convert to total hours
        total_hours = days * 24 + hours + minutes / 60 + seconds / 3600
        return round(total_hours, 4)
    
    except:
        return None

def get_seff_data(job_id):
    """Get seff data for a single job - only essential columns"""
    try:
        output = subprocess.check_output(['seff', str(job_id)], 
                                       stderr=subprocess.DEVNULL, 
                                       text=True)
    except subprocess.CalledProcessError:
        return {
            'Job_ID': job_id, 
            'State': 'ERROR',
            'CPU_Efficiency': None,
            'Memory_Efficiency': None,
            'Wall_Time_Hours': None
        }
    except FileNotFoundError:
        print("Error: seff command not found. Are you on a Slurm system?")
        sys.exit(1)
    
    # Initialize data dictionary with only needed fields
    data = {
        'Job_ID': job_id,
        'State': None,
        'CPU_Efficiency': None,
        'Memory_Efficiency': None,
        'Wall_Time_Hours': None
    }
    
    # Extract State
    state_match = re.search(r'State:\s*(\S+)', output, re.MULTILINE)
    if state_match:
        data['State'] = state_match.group(1)
    
    # Extract CPU Efficiency
    cpu_match = re.search(r'CPU Efficiency:\s*([\d.]+%)', output, re.MULTILINE)
    if cpu_match:
        data['CPU_Efficiency'] = cpu_match.group(1)
    
    # Extract Memory Efficiency
    mem_match = re.search(r'Memory Efficiency:\s*([\d.]+%)', output, re.MULTILINE)
    if mem_match:
        data['Memory_Efficiency'] = mem_match.group(1)
    
    # Extract Wall Time and convert to hours
    time_match = re.search(r'Job Wall-clock time:\s*([0-9:\-]+)', output, re.MULTILINE)
    if time_match:
        time_str = time_match.group(1)
        data['Wall_Time_Hours'] = slurm_time_to_hours(time_str)
    
    return data

def main():
    parser = argparse.ArgumentParser(description='Parse seff output for multiple Slurm jobs (simplified version)')
    parser.add_argument('job_ids', nargs='*', help='Job IDs (space-separated)')
    parser.add_argument('-f', '--file', help='File containing job IDs (one per line)')
    parser.add_argument('-o', '--output', default='seff_results.csv', 
                        help='Output CSV filename (default: seff_results.csv)')
    
    args = parser.parse_args()
    
    # Get job IDs from various sources
    job_ids = []
    
    # From command line arguments
    if args.job_ids:
        job_ids.extend(args.job_ids)
    
    # From file
    if args.file:
        try:
            with open(args.file, 'r') as f:
                job_ids.extend([line.strip() for line in f if line.strip()])
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found")
            sys.exit(1)
    
    # Check if no job IDs provided
    if not job_ids:
        print("Error: No job IDs provided.")
        print("\nUsage:")
        print("  python script.py JOB_ID1 JOB_ID2 ...")
        print("  python script.py -f job_ids.txt")
        print("  python script.py JOB_ID1 JOB_ID2 -f more_jobs.txt")
        sys.exit(1)
    
    print(f"Processing {len(job_ids)} jobs...")
    
    # Collect data for all jobs
    all_data = []
    for i, job_id in enumerate(job_ids, 1):
        print(f"  [{i}/{len(job_ids)}] Processing job {job_id}...", end='', flush=True)
        data = get_seff_data(job_id)
        all_data.append(data)
        print(" Done")
    
    # Create DataFrame with only the 5 columns
    df = pd.DataFrame(all_data)
    
    # Ensure column order
    df = df[['Job_ID', 'State', 'CPU_Efficiency', 'Memory_Efficiency', 'Wall_Time_Hours']]
    
    # Save to CSV
    df.to_csv(args.output, index=False)
    print(f"\nResults saved to {args.output}")
    
    # Display summary
    print("\n=== Summary ===")
    print(f"Total jobs processed: {len(df)}")
    
    # State counts
    if 'State' in df.columns:
        state_counts = df['State'].value_counts()
        print("\nJob States:")
        for state, count in state_counts.items():
            print(f"  {state}: {count}")
    
    # Efficiency statistics
    print("\nEfficiency Statistics (for completed jobs):")
    completed_df = df[df['State'] == 'COMPLETED'].copy()
    
    if len(completed_df) > 0:
        # CPU Efficiency
        if 'CPU_Efficiency' in completed_df.columns:
            cpu_values = completed_df['CPU_Efficiency'].str.rstrip('%').astype(float)
            print(f"\nCPU Efficiency:")
            print(f"  Average: {cpu_values.mean():.1f}%")
            print(f"  Min: {cpu_values.min():.1f}%")
            print(f"  Max: {cpu_values.max():.1f}%")
        
        # Memory Efficiency
        if 'Memory_Efficiency' in completed_df.columns:
            mem_values = completed_df['Memory_Efficiency'].str.rstrip('%').astype(float)
            print(f"\nMemory Efficiency:")
            print(f"  Average: {mem_values.mean():.1f}%")
            print(f"  Min: {mem_values.min():.1f}%")
            print(f"  Max: {mem_values.max():.1f}%")
        
        # Wall Time
        if 'Wall_Time_Hours' in completed_df.columns:
            time_values = completed_df['Wall_Time_Hours'].dropna()
            if len(time_values) > 0:
                print(f"\nWall Time (Hours):")
                print(f"  Total: {time_values.sum():.1f}")
                print(f"  Average: {time_values.mean():.1f}")
                print(f"  Min: {time_values.min():.1f}")
                print(f"  Max: {time_values.max():.1f}")
    
    # Show preview
    print("\n=== Data Preview ===")
    print(df.head(10).to_string())

if __name__ == "__main__":
    main()
