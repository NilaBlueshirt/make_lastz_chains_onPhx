import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse
from pathlib import Path
import sys
import numpy as np

def plot_slurm_data_comparison(
    data_files: list,
    y_column: str,
    output_file: str,
    plot_title: str
):
    """
    Generates a single plot to compare Slurm performance data from multiple
    CSV files, with each file represented as a separate line. The time axis
    is normalized to show time elapsed since the start of each collection.

    Args:
        data_files (list): A list of paths to the CSV data files to plot.
        y_column (str): The name of the column to plot on the Y-axis.
        output_file (str): Path to save the output plot image.
        plot_title (str): The main title for the figure.
    """
    # --- 1. Setup Plot ---
    if not data_files:
        print("Error: No data files provided.")
        sys.exit(1)

    fig, ax = plt.subplots(figsize=(18, 10))
    fig.suptitle(plot_title, fontsize=20, y=0.95)
    
    # Generate distinct colors for each line
    colors = plt.cm.viridis(np.linspace(0, 1, len(data_files)))

    # --- 2. Loop Through Data Files and Plot Each as a Line ---
    for i, data_file in enumerate(data_files):
        print(f"\nProcessing file: {data_file}...")

        try:
            # Load the dataset
            df = pd.read_csv(data_file, parse_dates=['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
        except FileNotFoundError:
            print(f"  Warning: Data file not found at '{data_file}'. Skipping.")
            continue
        except (KeyError, ValueError):
            print(f"  Error: 'timestamp' column not found or in wrong format in {data_file}. Check CSV.")
            continue

        # Check if the requested y_column exists
        if y_column not in df.columns:
            print(f"  Error: Column '{y_column}' not found in {data_file}.")
            print(f"  Available columns are: {list(df.columns)}")
            continue
            
        if df.empty:
            print(f"  Warning: Data file '{data_file}' is empty. Skipping.")
            continue

        # --- 3. Normalize the Time Axis ---
        # Calculate time elapsed since the first timestamp in this file
        start_time = df['timestamp'].iloc[0]
        # Convert timedelta to total hours for a clean numeric axis
        df['time_elapsed_hours'] = (df['timestamp'] - start_time).dt.total_seconds() / 3600.0

        # --- 4. Plot the Data ---
        ax.plot(
            df['time_elapsed_hours'],
            df[y_column],
            label=Path(data_file).name, # Label the line with the filename
            color=colors[i],
            linewidth=2
        )

    # --- 5. Format the Plot ---
    ax.set_xlabel("Time Elapsed (Hours)", fontsize=12)
    ax.set_ylabel(y_column.replace('_', ' ').title(), fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    # Only add legend if there are lines plotted
    if ax.get_legend_handles_labels()[0]:
        ax.legend(loc='upper left', title="Data Files")
    else:
        ax.text(0.5, 0.5, "No data to plot.", ha='center', va='center', fontsize=12, color='red')


    # --- 6. Finalize and Save Plot ---
    plt.tight_layout(rect=[0, 0, 1, 0.93]) # Adjust layout for suptitle
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nPlot successfully saved to '{output_file}'")


if __name__ == "__main__":
    # --- Command-Line Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Plot and compare Slurm performance data from multiple CSV files on a single graph.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--data-files',
        nargs='+',
        required=True,
        help="One or more paths to the data CSV files (e.g., run1.csv run2.csv)."
    )
    parser.add_argument(
        '--y-column',
        required=True,
        help="The name of the data column to plot on the Y-axis (e.g., 'Cycles_per_minute' or 'cpu_iowait')."
    )
    parser.add_argument(
        '--title',
        default="Slurm Performance Comparison",
        help="The main title for the plot."
    )
    parser.add_argument(
        '--output',
        default="slurm_comparison_plot.png",
        help="The filename for the output plot image."
    )

    args = parser.parse_args()

    plot_slurm_data_comparison(
        data_files=args.data_files,
        y_column=args.y_column,
        output_file=args.output,
        plot_title=args.title
    )

    # --- Example Usage ---
    #
    # Assume you have two files from two different runs:
    # - slurm_schedule_stats_run1.csv
    # - slurm_schedule_stats_run2.csv
    #
    # To compare the 'Mean_cycle' time for these two runs on a single plot:
    #
    # python plot_slurm_stats.py \
    #   --data-files slurm_schedule_stats_run1.csv slurm_schedule_stats_run2.csv \
    #   --y-column Mean_cycle \
    #   --title "Comparison of Slurm Mean Schedule Cycle Time" \
    #   --output mean_cycle_comparison.png
    #
    # To compare the 'cpu_load' from four different node stat files:
    #
    # python plot_slurm_stats.py \
    #   --data-files node_stats_A.csv node_stats_B.csv node_stats_C.csv node_stats_D.csv \
    #   --y-column load_avg_5m \
    #   --title "Comparison of Controller 5-min Load Average" \
    #   --output controller_load_comparison.png


