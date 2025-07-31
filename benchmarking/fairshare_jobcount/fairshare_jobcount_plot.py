import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Your 4 CSV files
files = [
    'fairshare_monitoring_YYYYMMDD_HHMMSS_1.csv',
    'fairshare_monitoring_YYYYMMDD_HHMMSS_2.csv',
    'fairshare_monitoring_YYYYMMDD_HHMMSS_3.csv',
    'fairshare_monitoring_YYYYMMDD_HHMMSS_4.csv'
]
labels = ['Config 1', 'Config 2', 'Config 3', 'Config 4']  # Customize these labels

# Create figure with 4 stacked subplots
fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)

# Define consistent colors
fairshare_color = '#1f77b4'  # Blue
jobs_color = '#ff7f0e'  # Orange

# Find global min/max for consistent y-axis scaling (optional)
all_fairshares = []
all_jobs = []
for file in files:
    df = pd.read_csv(file)
    all_fairshares.extend(df['realfairshare'].values)
    all_jobs.extend(df['running_jobs'].values)

fairshare_min, fairshare_max = min(all_fairshares), max(all_fairshares)
jobs_min, jobs_max = min(all_jobs), max(all_jobs)

# Plot each configuration
for idx, (file, label) in enumerate(zip(files, labels)):
    df = pd.read_csv(file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    ax1 = axes[idx]
    
    # Plot fairshare on primary y-axis
    line1 = ax1.plot(df['timestamp'], df['realfairshare'], 
                     color=fairshare_color, linewidth=2, label='RealFairShare')
    ax1.set_ylabel('RealFairShare', color=fairshare_color, fontsize=11)
    ax1.tick_params(axis='y', labelcolor=fairshare_color)
    ax1.set_ylim(fairshare_min * 0.95, fairshare_max * 1.05)  # Add 5% padding
    
    # Add horizontal grid for readability
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Create secondary y-axis for job count
    ax2 = ax1.twinx()
    line2 = ax2.plot(df['timestamp'], df['running_jobs'], 
                     color=jobs_color, linewidth=2, alpha=0.8, label='Running Jobs')
    ax2.set_ylabel('Running Jobs', color=jobs_color, fontsize=11)
    ax2.tick_params(axis='y', labelcolor=jobs_color)
    ax2.set_ylim(jobs_min - 5, jobs_max * 1.1)  # Add padding for jobs
    
    # Add configuration label
    ax1.text(0.02, 0.85, label, transform=ax1.transAxes, 
             fontsize=12, fontweight='bold', 
             bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # Remove top and bottom spines for cleaner look
    ax1.spines['top'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    if idx < 3:  # Not the bottom plot
        ax1.spines['bottom'].set_visible(False)
        ax2.spines['bottom'].set_visible(False)
    
    # Add legend only to the first subplot
    if idx == 0:
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper right', framealpha=0.9)

# Format x-axis (only on bottom subplot)
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
axes[-1].xaxis.set_major_locator(mdates.HourLocator(interval=2))
axes[-1].xaxis.set_minor_locator(mdates.HourLocator(interval=1))
plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=30, ha='right')
axes[-1].set_xlabel('Time', fontsize=12)

# Add overall title
plt.suptitle('Fairshare Score and Running Jobs Over Time\nAcross Different Array_Tag & Cluster_Tag Combinations', 
             fontsize=16, y=0.995)

# Adjust layout
plt.tight_layout()
plt.subplots_adjust(hspace=0.05, top=0.96)  # Minimal space between plots

# Save figure
plt.savefig('fairshare_stacked_comparison.png', dpi=300, bbox_inches='tight')
plt.show()

# Optional: Save summary statistics
print("\nSummary Statistics:")
print("-" * 50)
for file, label in zip(files, labels):
    df = pd.read_csv(file)
    print(f"\n{label}:")
    print(f"  Fairshare - Min: {df['realfairshare'].min():.6f}, Max: {df['realfairshare'].max():.6f}")
    print(f"  Jobs - Min: {df['running_jobs'].min()}, Max: {df['running_jobs'].max()}")
    print(f"  Total duration: {df.shape[0] * 10 / 60:.1f} minutes")
