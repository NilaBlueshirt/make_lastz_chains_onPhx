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
    
    # --- User-defined color palette ---
    custom_colors = ['#c2a5cf', '#a6dba0', '#7b3294', '#008837']

    # --- 2. Loop Through Data Files and Plot Each as a Line ---
    for i, data_file in enumerate(data_files):
        print(f"\nProcessing file: {data_file}...")

        try:
            # Load the dataset without auto-parsing dates initially
            df = pd.read_csv(data_file)
        except FileNotFoundError:
            print(f"  Warning: Data file not found at '{data_file}'. Skipping.")
            continue
        except Exception as e:
            print(f"  Error: Could not read CSV file {data_file}. Reason: {e}")
            continue

        # --- 2a. Robust Date Parsing ---
        if 'timestamp' not in df.columns:
            print(f"  Error: 'timestamp' column not found in {data_file}. Skipping.")
            continue
            
        # Explicitly convert to datetime, coercing errors to NaT (Not a Time)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

        # Check for and remove rows where date parsing failed
        initial_rows = len(df)
        df.dropna(subset=['timestamp'], inplace=True)
        if len(df) < initial_rows:
            print(f"  Warning: {initial_rows - len(df)} rows with invalid timestamp format were removed.")

        if df.empty:
            print(f"  Warning: No valid data left in '{data_file}' after cleaning timestamps. Skipping.")
            continue

        # Sort values after cleaning and before processing
        df = df.sort_values('timestamp').reset_index(drop=True)

        # --- 2b. Data Integrity Checks ---
        # Check for known bad headers from a potential collector script bug
        if 'Main' in df.columns and 'statistics' in df.columns:
            print("  Warning: Detected potentially incorrect headers ('Main', 'statistics').")
            print("           This may indicate a bug in the data collection script, causing misaligned columns.")

        # Check if the requested y_column exists
        if y_column not in df.columns:
            print(f"  Error: Column '{y_column}' not found in {data_file}.")
            print(f"  Available columns are: {list(df.columns)}")
            continue

        # --- 3. Normalize the Time Axis ---
        start_time = df['timestamp'].iloc[0]
        df['time_elapsed_hours'] = (df['timestamp'] - start_time).dt.total_seconds() / 3600.0

        # --- 4. Plot the Data ---
        color = custom_colors[i % len(custom_colors)]
        
        ax.plot(
            df['time_elapsed_hours'],
            df[y_column],
            label=Path(data_file).name,
            color=color,
            linewidth=2
        )

    # --- 5. Format the Plot ---
    ax.set_xlabel("Time Elapsed (Hours)", fontsize=12)
    ax.set_ylabel(y_column.replace('_', ' ').title(), fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    if ax.get_legend_handles_labels()[0]:
        ax.legend(loc='upper left', title="Data Files")
    else:
        ax.text(0.5, 0.5, "No valid data to plot.", ha='center', va='center', fontsize=12, color='red')

    # --- 6. Finalize and Save Plot ---
    plt.tight_layout(rect=[0, 0, 1, 0.93])
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
    # Assume you have four files from four different runs:
    # - run_A.csv, run_B.csv, run_C.csv, run_D.csv
    #
    # python plot_slurm_stats.py \
    #   --data-files run_A.csv run_B.csv run_C.csv run_D.csv \
    #   --y-column Mean_cycle \
    #   --title "Comparison of Slurm Mean Schedule Cycle Time" \
    #   --output mean_cycle_comparison.png
    #
    # The line for run_A.csv will be light purple ('#c2a5cf').
    # The line for run_B.csv will be light green ('#a6dba0').
    # The line for run_C.csv will be dark purple ('#7b3294').
    # The line for run_D.csv will be dark green ('#008837').


