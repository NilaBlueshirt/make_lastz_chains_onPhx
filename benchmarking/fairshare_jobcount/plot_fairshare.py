#!/usr/bin/env python3
"""
Plot fairshare and job count monitoring data from multiple CSV files.
Usage: python plot_fairshare.py fairshare_monitoring_*.csv
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='Plot fairshare and job count monitoring data from CSV files')
    parser.add_argument('files', nargs='+', help='CSV files to plot')
    parser.add_argument('--drop-zeros', action='store_true', 
                       help='Drop zero/missing values instead of plotting them')
    parser.add_argument('--output', '-o', default='fairshare_comparison.png',
                       help='Output filename (default: fairshare_comparison.png)')
    parser.add_argument('--figsize', nargs=2, type=int, default=[14, 3],
                       help='Figure width and height per subplot (default: 14 3)')
    parser.add_argument('--labels', nargs='*', 
                       help='Custom labels for each file (default: use filenames)')
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Validate files exist
    files = []
    for f in args.files:
        if not os.path.exists(f):
            print(f"Error: File '{f}' not found")
            sys.exit(1)
        files.append(f)
    
    n_files = len(files)
    if n_files == 0:
        print("Error: No files provided")
        sys.exit(1)
    
    # Generate labels
    if args.labels and len(args.labels) == n_files:
        labels = args.labels
    else:
        # Use filenames without path and extension as labels
        labels = [os.path.splitext(os.path.basename(f))[0] for f in files]
        if args.labels:
            print(f"Warning: Number of labels ({len(args.labels)}) doesn't match number of files ({n_files}). Using filenames.")
    
    # Calculate figure size
    fig_width = args.figsize[0]
    fig_height = args.figsize[1] * n_files
    
    # Create figure with stacked subplots
    fig, axes = plt.subplots(n_files, 1, figsize=(fig_width, fig_height), sharex=True)
    
    # Handle single file case (axes won't be an array)
    if n_files == 1:
        axes = [axes]
    
    # Define consistent colors
    fairshare_color = '#1f77b4'  # Blue
    jobs_color = '#ff7f0e'  # Orange
    
    # Find global min/max for consistent y-axis scaling
    all_fairshares = []
    all_jobs = []
    
    # First pass: read all data to find global scales
    for file in files:
        try:
            df = pd.read_csv(file)
            df['realfairshare'] = pd.to_numeric(df['realfairshare'], errors='coerce')
            df['running_jobs'] = pd.to_numeric(df['running_jobs'], errors='coerce')
            
            if args.drop_zeros:
                valid_fairshares = df[df['realfairshare'] > 0]['realfairshare']
            else:
                valid_fairshares = df['realfairshare'].fillna(0)
            
            if len(valid_fairshares) > 0:
                all_fairshares.extend(valid_fairshares.values)
            
            valid_jobs = df['running_jobs'].fillna(0)
            all_jobs.extend(valid_jobs.values)
        except Exception as e:
            print(f"Error reading {file}: {e}")
            sys.exit(1)
    
    # Calculate ranges
    if all_fairshares:
        if args.drop_zeros:
            fairshare_min = min([x for x in all_fairshares if x > 0]) * 0.95
        else:
            fairshare_min = min(all_fairshares) * 0.95 if min(all_fairshares) > 0 else 0
        fairshare_max = max(all_fairshares) * 1.05
    else:
        fairshare_min, fairshare_max = 0, 1
    
    # Fix for jobs range when all values are 0
    jobs_min = 0
    if all_jobs and max(all_jobs) > 0:
        jobs_max = max(all_jobs) * 1.1
    else:
        jobs_max = 10  # Default range when no jobs
    
    # Plot each file
    for idx, (file, label) in enumerate(zip(files, labels)):
        df = pd.read_csv(file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['realfairshare'] = pd.to_numeric(df['realfairshare'], errors='coerce')
        df['running_jobs'] = pd.to_numeric(df['running_jobs'], errors='coerce')
        
        ax1 = axes[idx]
        
        if args.drop_zeros:
            # Drop zeros and missing values
            df_fairshare = df[df['realfairshare'] > 0].copy()
            df_jobs = df[df['running_jobs'].notna()].copy()
            
            if len(df_fairshare) > 0:
                ax1.plot(df_fairshare['timestamp'], df_fairshare['realfairshare'], 
                        color=fairshare_color, linewidth=2, marker='o', markersize=2,
                        label='RealFairShare')
        else:
            # Replace missing/invalid with zeros
            df['realfairshare'] = df['realfairshare'].fillna(0)
            df.loc[df['realfairshare'] < 0, 'realfairshare'] = 0
            df['running_jobs'] = df['running_jobs'].fillna(0)
            df_jobs = df
            
            ax1.plot(df['timestamp'], df['realfairshare'], 
                    color=fairshare_color, linewidth=2, label='RealFairShare')
        
        ax1.set_ylabel('RealFairShare', color=fairshare_color, fontsize=11)
        ax1.tick_params(axis='y', labelcolor=fairshare_color)
        ax1.set_ylim(fairshare_min, fairshare_max)
        
        # Add horizontal grid
        ax1.grid(True, alpha=0.3, axis='y', linestyle='-', linewidth=0.5)
        
        # Add vertical gridlines every 30 minutes
        ax1.grid(True, alpha=0.3, axis='x', linestyle=':', linewidth=0.5)
        
        # Create secondary y-axis for job count
        ax2 = ax1.twinx()
        if len(df_jobs) > 0:
            ax2.plot(df_jobs['timestamp'], df_jobs['running_jobs'], 
                    color=jobs_color, linewidth=2, alpha=0.8, label='Running Jobs')
        
        ax2.set_ylabel('Running Jobs', color=jobs_color, fontsize=11)
        ax2.tick_params(axis='y', labelcolor=jobs_color)
        
        # Only set ylim if it's not causing singular transformation
        if jobs_max > jobs_min:
            ax2.set_ylim(jobs_min, jobs_max)
        
        # Add configuration label
        ax1.text(0.02, 0.85, label, transform=ax1.transAxes, 
                fontsize=10, fontweight='bold', 
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        # Remove spines for cleaner look, but keep bottom for separation
        ax1.spines['top'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        
        # Add solid line at bottom for separation (except for the last subplot)
        if idx < n_files - 1:
            ax1.spines['bottom'].set_visible(True)
            ax1.spines['bottom'].set_linewidth(1.5)
            ax1.spines['bottom'].set_color('black')
        
        # Add legend only to the first subplot
        if idx == 0:
            ax1.legend(loc='upper left', framealpha=0.9)
            ax2.legend(loc='upper right', framealpha=0.9)
    
    # Format x-axis with 30-minute intervals
    axes[-1].xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%m/%d-%H:%M'))
    
    # Add minor ticks if needed
    axes[-1].xaxis.set_minor_locator(mdates.MinuteLocator(interval=10))
    
    plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=45, ha='right')
    axes[-1].set_xlabel('Time', fontsize=12)
    
    # Add title without "Zeros Included"
    plt.suptitle('Fairshare Score and Running Jobs Over Time', 
                fontsize=14, y=0.995)
    
    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.05, top=0.98 - (0.01 * max(0, n_files - 4)))
    
    # Save figure
    plt.savefig(args.output, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {args.output}")
    
    # Show plot
    plt.show()
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("-" * 70)
    for file, label in zip(files, labels):
        df = pd.read_csv(file)
        # Convert timestamp to datetime for duration calculation
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['realfairshare'] = pd.to_numeric(df['realfairshare'], errors='coerce')
        df['running_jobs'] = pd.to_numeric(df['running_jobs'], errors='coerce')
        
        total_points = len(df)
        valid_fairshare = len(df[df['realfairshare'] > 0])
        zero_invalid = total_points - valid_fairshare
        
        print(f"\n{label}:")
        print(f"  File: {file}")
        print(f"  Total data points: {total_points}")
        print(f"  Valid fairshare points: {valid_fairshare}")
        print(f"  Zero/Invalid points: {zero_invalid} ({zero_invalid/total_points*100:.1f}%)")
        
        if valid_fairshare > 0:
            valid_df = df[df['realfairshare'] > 0]
            print(f"  Fairshare range: {valid_df['realfairshare'].min():.6f} - {valid_df['realfairshare'].max():.6f}")
        
        # Handle case where all job values might be NaN
        valid_jobs = df['running_jobs'].dropna()
        if len(valid_jobs) > 0:
            print(f"  Jobs range: {valid_jobs.min():.0f} - {valid_jobs.max():.0f}")
        else:
            print(f"  Jobs range: No valid job data")
        
        # Calculate duration safely
        if len(df) > 0:
            duration_minutes = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60
            print(f"  Duration: {duration_minutes:.1f} minutes")
        else:
            print(f"  Duration: No data")

if __name__ == "__main__":
    main()
