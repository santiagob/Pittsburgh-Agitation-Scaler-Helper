import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import glob
import re
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

class PittsburghTimeSeriesGenerator:
    def __init__(self):
        self.pittsburgh_columns = [
            'Aberrant_Vocalization',
            'Motor_Agitation',
            'Aggressiveness',
            'Resisting_Care'
        ]
        
    def parse_time_to_seconds(self, time_str):
        """Convert time string to seconds from start of day"""
        if pd.isna(time_str) or time_str == '':
            return None
            
        time_str = str(time_str).strip()
        
        # Try different time formats
        formats = [
            '%H:%M:%S',      # 14:30:45
            '%H:%M',         # 14:30
            '%I:%M %p',      # 2:30 PM
            '%I:%M:%S %p',   # 2:30:45 PM
            '%H.%M.%S',      # 14.30.45
            '%H.%M',         # 14.30
        ]
        
        for fmt in formats:
            try:
                time_obj = datetime.strptime(time_str, fmt)
                # Calculate seconds from midnight
                return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
            except ValueError:
                continue
        
        # Try to extract numbers for minutes:seconds format
        match = re.match(r'(\d+):(\d+)', time_str)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            if minutes < 60:  # Likely minutes:seconds
                return minutes * 60 + seconds
        
        # Try to parse as just seconds
        try:
            return float(time_str)
        except ValueError:
            return None
    
    def seconds_to_time_string(self, seconds):
        """Convert seconds from start of day to time string"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def process_observation_file(self, filepath):
        """Process a single observation file and generate time series"""
        print(f"\nProcessing: {os.path.basename(filepath)}")
        
        # Read the observation file
        df = pd.read_csv(filepath)
        
        # Check if it has the required columns
        if not all(col in df.columns for col in self.pittsburgh_columns):
            print(f"  Warning: Missing Pittsburgh columns in {filepath}")
            return None
            
        # Get time information
        if 'Time' not in df.columns:
            print(f"  Warning: No Time column in {filepath}")
            return None
        
        # Parse times and durations
        time_seconds = []
        durations = []
        
        for idx, row in df.iterrows():
            time_sec = self.parse_time_to_seconds(row['Time'])
            if time_sec is not None:
                time_seconds.append(time_sec)
                
                # Get duration (default to 600 seconds if not specified)
                duration = row.get('Duration_Seconds', 600)
                if pd.isna(duration) or duration == '':
                    duration = 600
                durations.append(float(duration))
        
        if not time_seconds:
            print(f"  Warning: No valid timestamps found in {filepath}")
            return None
        
        # Create time series from first to last observation + last duration
        start_time = min(time_seconds)
        end_time = max(time_seconds) + durations[-1]  # Add last observation's duration
        
        # Create 1-second interval time series
        time_range = np.arange(start_time, end_time, 1)  # 1-second intervals
        
        # Initialize time series dataframe
        ts_data = {
            'Time_Seconds': time_range,
            'Time': [self.seconds_to_time_string(t) for t in time_range]
        }
        
        # Initialize Pittsburgh columns with zeros
        for col in self.pittsburgh_columns:
            ts_data[col] = np.zeros(len(time_range))
        
        # Add Total_Agitation column (sum of all 4 parameters)
        ts_data['Total_Agitation'] = np.zeros(len(time_range))
        
        # Fill in the observations
        for idx, row in df.iterrows():
            time_sec = self.parse_time_to_seconds(row['Time'])
            if time_sec is None:
                continue
                
            duration = row.get('Duration_Seconds', 600)
            if pd.isna(duration) or duration == '':
                duration = 600
            else:
                duration = float(duration)
            
            # Find the start index in time series
            start_idx = int(time_sec - start_time)
            end_idx = min(int(start_idx + duration), len(time_range))
            
            # Fill in the Pittsburgh scores for the duration
            total_score = 0
            for col in self.pittsburgh_columns:
                score = row.get(col, 0)
                if pd.isna(score) or score == '':
                    score = 0
                else:
                    score = int(float(score))
                
                ts_data[col][start_idx:end_idx] = score
                total_score += score
            
            # Update total agitation
            ts_data['Total_Agitation'][start_idx:end_idx] = total_score
        
        # Create DataFrame
        ts_df = pd.DataFrame(ts_data)
        
        # Add metadata columns
        if 'Song' in df.columns and not df['Song'].isna().all():
            ts_df['Current_Song'] = self.propagate_song_info(df, ts_df)
        
        print(f"  Generated {len(ts_df)} seconds of time series data")
        print(f"  Time range: {ts_df['Time'].iloc[0]} to {ts_df['Time'].iloc[-1]}")
        
        return ts_df
    
    def propagate_song_info(self, obs_df, ts_df):
        """Propagate song information to time series"""
        songs = [''] * len(ts_df)
        
        for idx, row in obs_df.iterrows():
            if pd.notna(row.get('Song', '')):
                time_sec = self.parse_time_to_seconds(row['Time'])
                if time_sec is not None:
                    duration = row.get('Duration_Seconds', 600)
                    if pd.isna(duration):
                        duration = 600
                    
                    start_idx = int(time_sec - ts_df['Time_Seconds'].iloc[0])
                    end_idx = min(int(start_idx + duration), len(ts_df))
                    
                    for i in range(start_idx, end_idx):
                        if i < len(songs):
                            songs[i] = str(row['Song'])
        
        return songs
    
    def plot_time_series(self, ts_df, original_file, save_path):
        """Create a visualization of the time series data"""
        fig, axes = plt.subplots(5, 1, figsize=(15, 12), sharex=True)
        fig.suptitle(f'Pittsburgh Agitation Scale Time Series\n{os.path.basename(original_file)}', 
                    fontsize=14, fontweight='bold')
        
        # Calculate time in minutes for x-axis
        time_minutes = ts_df['Time_Seconds'] / 60
        
        # Color scheme for different levels
        colors = ['green', 'yellow', 'orange', 'red', 'darkred']
        level_names = ['Not Present', 'Level 1', 'Level 2', 'Level 3', 'Level 4']
        
        # Plot each parameter
        for idx, col in enumerate(self.pittsburgh_columns):
            ax = axes[idx]
            
            # Create filled area plot
            ax.fill_between(time_minutes, 0, ts_df[col], alpha=0.3, color='blue')
            ax.plot(time_minutes, ts_df[col], linewidth=1.5, color='darkblue')
            
            # Add colored background for severity levels
            for level in range(5):
                ax.axhspan(level - 0.1, level + 0.1, alpha=0.1, color=colors[level])
            
            ax.set_ylabel(col.replace('_', ' '), fontsize=10, fontweight='bold')
            ax.set_ylim(-0.5, 4.5)
            ax.set_yticks([0, 1, 2, 3, 4])
            ax.grid(True, alpha=0.3)
            
            # Add statistics
            mean_val = ts_df[col].mean()
            max_val = ts_df[col].max()
            non_zero_pct = (ts_df[col] > 0).mean() * 100
            
            stats_text = f'Mean: {mean_val:.2f} | Max: {max_val} | Active: {non_zero_pct:.1f}%'
            ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, 
                   fontsize=8, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Plot total agitation score
        ax = axes[4]
        ax.fill_between(time_minutes, 0, ts_df['Total_Agitation'], 
                       alpha=0.3, color='purple')
        ax.plot(time_minutes, ts_df['Total_Agitation'], 
               linewidth=2, color='darkviolet')
        ax.set_ylabel('Total Agitation\n(Sum)', fontsize=10, fontweight='bold')
        ax.set_ylim(-1, 17)
        ax.grid(True, alpha=0.3)
        
        # Add statistics for total
        mean_val = ts_df['Total_Agitation'].mean()
        max_val = ts_df['Total_Agitation'].max()
        non_zero_pct = (ts_df['Total_Agitation'] > 0).mean() * 100
        
        stats_text = f'Mean: {mean_val:.2f} | Max: {max_val} | Active: {non_zero_pct:.1f}%'
        ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, 
               fontsize=8, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Set x-axis label
        ax.set_xlabel('Time (minutes)', fontsize=11, fontweight='bold')
        
        # Add legend for severity levels
        legend_elements = [mpatches.Patch(color=colors[i], alpha=0.3, label=level_names[i]) 
                          for i in range(5)]
        axes[0].legend(handles=legend_elements, loc='upper right', ncol=5, fontsize=8)
        
        plt.tight_layout()
        
        # Save the plot
        plot_file = save_path.replace('.csv', '_plot.png')
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"  Plot saved: {plot_file}")
        
        # Show the plot
        plt.show()
        
        return plot_file
    
    def process_folder(self, folder_path):
        """Process all observation files in a folder"""
        # Find all files ending with Pittsburgh observations
        pattern = os.path.join(folder_path, "**", "*Observations_with_Pittsburgh_Scale.csv")
        observation_files = glob.glob(pattern, recursive=True)
        
        if not observation_files:
            print(f"No files ending with 'Observations_with_Pittsburgh_Scale.csv' found in {folder_path}")
            return
        
        print(f"Found {len(observation_files)} observation files to process")
        
        processed_files = []
        
        for obs_file in observation_files:
            # Generate time series
            ts_df = self.process_observation_file(obs_file)
            
            if ts_df is not None:
                # Create output filename
                base_name = os.path.basename(obs_file)
                dir_name = os.path.dirname(obs_file)
                
                # Replace the suffix to indicate time series
                output_name = base_name.replace(
                    "Observations_with_Pittsburgh_Scale.csv",
                    "Pittsburgh_TimeSeries_1sec.csv"
                )
                output_path = os.path.join(dir_name, output_name)
                
                # Save the time series
                ts_df.to_csv(output_path, index=False)
                print(f"  Saved time series: {output_name}")
                
                # Create and save plot
                self.plot_time_series(ts_df, obs_file, output_path)
                
                processed_files.append(output_path)
        
        print(f"\n{'='*50}")
        print(f"Processing complete! Generated {len(processed_files)} time series files")
        
        return processed_files

def main():
    """Main function to run the time series generator"""
    import tkinter as tk
    from tkinter import filedialog
    
    # Create root window (hidden)
    root = tk.Tk()
    root.withdraw()
    
    # Ask user to select folder
    folder_path = filedialog.askdirectory(
        title="Select folder containing Pittsburgh observation files"
    )
    
    if not folder_path:
        print("No folder selected. Exiting.")
        return
    
    # Create generator and process folder
    generator = PittsburghTimeSeriesGenerator()
    generator.process_folder(folder_path)
    
    print("\nAll files processed successfully!")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
