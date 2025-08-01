#!/usr/bin/env python3
"""
Line chart with aggregation for multiple jobs per sample pair
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def create_aggregated_chart(csv_file='seff_results.csv'):
    # Read data
    df = pd.read_csv(csv_file)
    
    # Create combination label
    df['Config'] = df['Array_Tag'].astype(str) + '_' + df['Cluster_Tag'].astype(str)
    
    # Aggregate by Sample_Pair_ID and Config (in case of multiple jobs)
    agg_df = df.groupby(['Sample_Pair_ID', 'Array_Tag', 'Cluster_Tag', 'Config']).agg({
        'Wall_Time_Hours': ['mean', 'std', 'count']
    }).reset_index()
    
    # Flatten column names
    agg_df.columns = ['Sample_Pair_ID', 'Array_Tag', 'Cluster_Tag', 'Config', 
                       'Wall_Time_Mean', 'Wall_Time_Std', 'Job_Count']
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Cold color palette
    color_map = {
        '0_0': '#c2a5cf',  # no array, dev - light purple
        '0_1': '#a6dba0',  # no array, phx - light green
        '1_0': '#7b3294',  # array, dev - dark purple
        '1_1': '#008837'   # array, phx - dark green
    }
    
    # Labels for legend
    label_map = {
        '0_0': 'No Array, Dev',
        '0_1': 'No Array, Phx',
        '1_0': 'Use Array, Dev',
        '1_1': 'Use Array, Phx'
    }
    
    # Get unique sample pairs in order
    sample_pairs = sorted(agg_df['Sample_Pair_ID'].unique())
    x_positions = range(len(sample_pairs))
    
    # Plot each configuration
    for config in sorted(agg_df['Config'].unique()):
        config_data = agg_df[agg_df['Config'] == config]
        
        # Ensure we have data for all sample pairs (fill missing with NaN)
        y_values = []
        y_errors = []
        
        for sample in sample_pairs:
            sample_data = config_data[config_data['Sample_Pair_ID'] == sample]
            if len(sample_data) > 0:
                y_values.append(sample_data['Wall_Time_Mean'].iloc[0])
                # Use standard error if multiple jobs, 0 if single job
                if sample_data['Job_Count'].iloc[0] > 1:
                    se = sample_data['Wall_Time_Std'].iloc[0] / np.sqrt(sample_data['Job_Count'].iloc[0])
                    y_errors.append(se)
                else:
                    y_errors.append(0)
            else:
                y_values.append(np.nan)
                y_errors.append(0)
        
        # Plot with error bars
        ax.errorbar(x_positions, y_values,
                   yerr=y_errors,
                   marker='o',
                   markersize=8,
                   linewidth=2.5,
                   label=label_map[config],
                   color=color_map[config],
                   capsize=5,
                   alpha=0.85)
    
    # Customize plot
    ax.set_xticks(x_positions)
    ax.set_xticklabels(sample_pairs, rotation=45, ha='right')
    ax.set_xlabel('Sample Pair ID', fontsize=12)
    ax.set_ylabel('Wall Time (Hours)', fontsize=12)
    ax.set_title('Average Wall Time by Sample Pair and Configuration\n(Error bars show standard error)', 
                fontsize=12)
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Legend
    ax.legend(title='Configuration', 
             bbox_to_anchor=(1.02, 1), 
             loc='upper left',
             frameon=True,
             fancybox=True,
             shadow=True)
    
    # Add annotation for total jobs
    total_jobs = df.shape[0]
    ax.text(0.02, 0.98, f'Total Jobs: {total_jobs}', 
            transform=ax.transAxes, 
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('wall_time_aggregated.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print summary
    print("\n=== Configuration Summary ===")
    for config in sorted(agg_df['Config'].unique()):
        config_df = agg_df[agg_df['Config'] == config]
        print(f"\n{label_map[config]}:")
        print(f"  Samples: {len(config_df)}")
        print(f"  Avg Wall Time: {config_df['Wall_Time_Mean'].mean():.2f} hours")
        print(f"  Total Jobs: {config_df['Job_Count'].sum()}")

# Run the function
if __name__ == "__main__":
    create_aggregated_chart('seff_results.csv')
