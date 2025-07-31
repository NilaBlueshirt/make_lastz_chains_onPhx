#!/usr/bin/env python3
"""
Flexible seff parser that can read job IDs from:
- Command line arguments
- A file
Time values are converted to hours for easier analysis
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

def parse_memory_value(mem_str):
    """
    Convert memory string to GB for easier analysis.
    Handles formats like: 1.5GB, 500MB, 1TB, etc.
    """
    if not mem_str or mem_str == 'None':
        return None
    
    try:
        # Remove whitespace
        mem_str = mem_str.strip().upper()
        
        # Extract number and unit
        match = re.match(r'([\d.]+)\s*([KMGT]?B)?', mem_str)
        if not match:
            return None
        
        value = float(match.group(1))
        unit = match.group(2) or 'B'
        
        # Convert to GB
        conversions = {
            'B': 1 / (1024**3),
            'KB': 1 / (1024**2),
            'MB': 1 / 1024,
            'GB': 1,
            'TB': 1024
        }
        
        return round(value * conversions.get(unit, 1), 3)
    
    except:
        return None

def get_seff_data(job_id):
    """Get seff data for a single job"""
    try:
        output = subprocess.check_output(['seff', str(job_id)], 
                                       stderr=subprocess.DEVNULL, 
                                       text=True)
    except subprocess.CalledProcessError:
        return {'Job_ID': job_id, 'Error': 'Failed to get seff data'}
    except FileNotFoundError:
        print("Error: seff command not found. Are you on a Slurm system?")
        sys.exit(1)
    
    # Parse the output
    data = {'Job_ID': job_id}
    
    # Extract all relevant fields
    patterns = {
        'State': r'State:\s*(\S+)',
        'Exit_Code': r'Exit code:\s*(\S+)',
        'CPU_Efficiency': r'CPU Efficiency:\s*([\d.]+%)',
        'Memory_Efficiency': r'Memory Efficiency:\s*([\d.]+%)',
        'Memory_Used': r'Memory Utilized:\s*(\S+)',
        'Memory_Requested': r'of\s*(\S+)\s*\(',
        'Wall_Time': r'Job Wall-clock time:\s*([0-9:\-]+)',
        'CPU_Time': r'CPU Utilized:\s*([0-9:\-]+)',
        'Nodes': r'Nodes:\s*(\d+)',
        'Cores': r'Cores per node:\s*(\d+)',
        'Cluster': r'Cluster:\s*(\S+)',
        'User': r'User/Group:\s*(\S+)/(\S+)',
        'Billing': r'Billing:\s*(\S+)'
    }
    
    for field, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if field == 'User' and match:
            data['User'] = match.group(1)
            data['Group'] = match.group(2)
        else:
            data[field] = match.group(1) if match else None
    
    # Convert time fields to hours
    if data.get('Wall_Time'):
        data['Wall_Time_Hours'] = slurm_time_to_hours(data['Wall_Time'])
    
    if data.get('CPU_Time'):
        data['CPU_Time_Hours'] = slurm_time_to_hours(data['CPU_Time'])
    
    # Convert memory fields to GB
    if data.get('Memory_Used'):
        data['Memory_Used_GB'] = parse_memory_value(data['Memory_Used'])
    
    if data.get('Memory_Requested'):
        data['Memory_Requested_GB'] = parse_memory_value(data['Memory_Requested'])
    
    # Extract numeric values for efficiency
    if data.get('CPU_Efficiency'):
        data['CPU_Efficiency_Numeric'] = float(data['CPU_Efficiency'].rstrip('%'))
    if data.get('Memory_Efficiency'):
        data['Memory_Efficiency_Numeric'] = float(data['Memory_Efficiency'].rstrip('%'))
    
    # Calculate core-hours if possible
    if data.get('Wall_Time_Hours') and data.get('Cores') and data.get('Nodes'):
        try:
            total_cores = int(data['Cores']) * int(data['Nodes'])
            data['Core_Hours'] = round(data['Wall_Time_Hours'] * total_cores, 2)
        except:
            data['Core_Hours'] = None
    
    return data

def main():
    parser = argparse.ArgumentParser(description='Parse seff output for multiple Slurm jobs')
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
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    # Reorder columns for better readability
    column_order = [
        'Job_ID', 'State', 'Exit_Code', 
        'CPU_Efficiency', 'CPU_Efficiency_Numeric', 
        'Memory_Efficiency', 'Memory_Efficiency_Numeric',
        'Wall_Time', 'Wall_Time_Hours', 
        'CPU_Time', 'CPU_Time_Hours',
        'Memory_Used', 'Memory_Used_GB',
        'Memory_Requested', 'Memory_Requested_GB',
        'Nodes', 'Cores', 'Core_Hours',
        'Cluster', 'User', 'Group', 'Billing', 'Error'
    ]
    
    # Only include columns that exist
    df = df[[col for col in column_order if col in df.columns]]
    
    # Save to CSV
    df.to_csv(args.output, index=False)
    print(f"\nResults saved to {args.output}")
    
    # Display summary
    print("\n=== Summary ===")
    print(f"Total jobs processed: {len(df)}")
    
    if 'State' in df.columns:
        state_counts = df['State'].value_counts()
        print("\nJob States:")
        for state, count in state_counts.items():
            print(f"  {state}: {count}")
    
    if 'CPU_Efficiency_Numeric' in df.columns:
        valid_cpu = df['CPU_Efficiency_Numeric'].dropna()
        if not valid_cpu.empty:
            print(f"\nCPU Efficiency:")
            print(f"  Average: {valid_cpu.mean():.1f}%")
            print(f"  Min: {valid_cpu.min():.1f}%")
            print(f"  Max: {valid_cpu.max():.1f}%")
    
    if 'Memory_Efficiency_Numeric' in df.columns:
        valid_mem = df['Memory_Efficiency_Numeric'].dropna()
        if not valid_mem.empty:
            print(f"\nMemory Efficiency:")
            print(f"  Average: {valid_mem.mean():.1f}%")
            print(f"  Min: {valid_mem.min():.1f}%")
            print(f"  Max: {valid_mem.max():.1f}%")
    
    if 'Wall_Time_Hours' in df.columns:
        valid_time = df['Wall_Time_Hours'].dropna()
        if not valid_time.empty:
            print(f"\nWall Time (Hours):")
            print(f"  Total: {valid_time.sum():.1f}")
            print(f"  Average: {valid_time.mean():.1f}")
            print(f"  Max: {valid_time.max():.1f}")
    
    if 'Core_Hours' in df.columns:
        valid_core_hours = df['Core_Hours'].dropna()
        if not valid_core_hours.empty:
            print(f"\nCore Hours:")
            print(f"  Total: {valid_core_hours.sum():.1f}")
    
    # Show preview
    print("\n=== Preview of Results ===")
    preview_cols = ['Job_ID', 'State', 'CPU_Efficiency', 'Memory_Efficiency', 'Wall_Time_Hours']
    preview_cols = [col for col in preview_cols if col in df.columns]
    if preview_cols:
        print(df[preview_cols].head(10).to_string())

if __name__ == "__main__":
    main()
