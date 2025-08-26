import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import glob
import re
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches
import tkinter as tk
from tkinter import filedialog, messagebox
import textwrap

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
    
    def seconds_to_datetime(self, seconds, base_date=None):
        """Convert seconds from start of day to datetime object"""
        if base_date is None:
            base_date = datetime.now().date()
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return datetime.combine(base_date, datetime.min.time()) + timedelta(hours=hours, minutes=minutes, seconds=secs)
    
    def process_observation_file(self, filepath):
        """Process a single observation file and generate time series"""
        print(f"\nProcessing: {os.path.basename(filepath)}")
        
        # Read the observation file
        df = pd.read_csv(filepath)
        
        # Check if it has the required columns
        if not all(col in df.columns for col in self.pittsburgh_columns):
            print(f"  Warning: Missing Pittsburgh columns in {filepath}")
            return None, None
            
        # Get time information
        if 'Time' not in df.columns:
            print(f"  Warning: No Time column in {filepath}")
            return None, None
        
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
            return None, None
        
        # Create time series from first to last observation + last duration
        start_time = min(time_seconds)
        end_time = max(time_seconds) + durations[-1]  # Add last observation's duration
        
        # Create 1-second interval time series
        time_range = np.arange(start_time, end_time, 1)  # 1-second intervals
        
        # Initialize time series dataframe
        ts_data = {
            'Time_Seconds': time_range,
            'Time': [self.seconds_to_time_string(t) for t in time_range],
            'Datetime': [self.seconds_to_datetime(t) for t in time_range]
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
        
        return ts_df, df  # Return both time series and original observations
    
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
    
    def plot_time_series_with_annotations(self, ts_df, obs_df, original_file, save_path):
        """Create a visualization of the time series data with song and observation annotations"""
        
        # Prepare annotations from observation data
        annotations = []
        music_start = None
        music_end = None
        
        for idx, row in obs_df.iterrows():
            time_sec = self.parse_time_to_seconds(row['Time'])
            if time_sec is None:
                continue
            
            # Build annotation text - FULL TEXT WITHOUT TRUNCATION
            text_parts = []
            
            # Add song info if available (FULL TEXT)
            if pd.notna(row.get('Song', '')) and str(row['Song']).strip():
                song_text = str(row['Song']).strip()
                # Wrap long song titles
                wrapped_song = '\n'.join(textwrap.wrap(song_text, width=30))
                text_parts.append(f"♪ {wrapped_song}")
            
                # Add score if available
                if pd.notna(row.get('Score', '')) and str(row['Score']).strip():
                    text_parts.append(f"S:{row['Score']}")
            else:
                # Add observation if available (FULL TEXT)
                if pd.notna(row.get('Observations', '')) and str(row['Observations']).strip():
                    obs_text = str(row['Observations']).strip()
                    # Wrap long observations
                    wrapped_obs = '\n'.join(textwrap.wrap(obs_text, width=35))
                    text_parts.append(wrapped_obs)
            
            if text_parts:  # Only add annotation if there's text
                annotation_time = self.seconds_to_datetime(time_sec)
                annotations.append({
                    'time': annotation_time,
                    'text': '\n'.join(text_parts),  # Multi-line text
                    'has_song': pd.notna(row.get('Song', '')) and str(row['Song']).strip()
                })
                
                # Track music period
                if pd.notna(row.get('Song', '')) and str(row['Song']).strip():
                    if music_start is None:
                        music_start = annotation_time
                    music_end = annotation_time + timedelta(seconds=float(row.get('Duration_Seconds', 600)))
        
        # Calculate figure height based on annotation content
        max_lines = max([ann['text'].count('\n') + 1 for ann in annotations], default=1)
        fig_height = max(16, 14 + (max_lines * 0.3))
        
        # Create figure with subplots - dynamic height based on content
        fig, axes = plt.subplots(5, 1, figsize=(26, fig_height), sharex=True)
        fig.suptitle(f'Pittsburgh Agitation Scale Time Series with Annotations\n{os.path.basename(original_file)}', 
                    fontsize=16, fontweight='bold')
        
        # Use datetime for x-axis
        x_time = ts_df['Datetime']
        
        # Color scheme for different levels
        colors = ['green', 'yellow', 'orange', 'red', 'darkred']
        level_names = ['Not Present', 'Level 1', 'Level 2', 'Level 3', 'Level 4']
        
        # Plot each parameter
        for idx, col in enumerate(self.pittsburgh_columns):
            ax = axes[idx]
            
            # Plot the data
            ax.plot(x_time, ts_df[col], linewidth=1.5, color='darkblue', label=col.replace('_', ' '))
            ax.fill_between(x_time, 0, ts_df[col], alpha=0.3, color='blue')
            
            # Add colored background for severity levels
            for level in range(5):
                ax.axhspan(level - 0.1, level + 0.1, alpha=0.1, color=colors[level])
            
            # Add music period shading if available
            if music_start and music_end:
                ax.axvspan(music_start, music_end, color='lightgray', alpha=0.3, zorder=0, label='Music Period')
            
            ax.set_ylabel(col.replace('_', ' '), fontsize=10, fontweight='bold')
            ax.set_ylim(-0.5, 4.5)
            ax.set_yticks([0, 1, 2, 3, 4])
            ax.grid(True, alpha=0.3, axis='y')
            
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
        ax.plot(x_time, ts_df['Total_Agitation'], linewidth=2, color='darkviolet')
        ax.fill_between(x_time, 0, ts_df['Total_Agitation'], alpha=0.3, color='purple')
        
        # Add music period shading
        if music_start and music_end:
            ax.axvspan(music_start, music_end, color='lightgray', alpha=0.3, zorder=0, label='Music Period')
        
        ax.set_ylabel('Total Agitation\n(Sum)', fontsize=10, fontweight='bold')
        ax.set_ylim(-2, 17)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add annotations with alternating vertical positions to reduce overlap
        if annotations:
            # Use alternating levels for adjacent annotations
            y_levels = [-0.15, -0.35, -0.55]
            level_index = 0
            
            for i, annotation in enumerate(annotations):
                # Check if next annotation is close in time
                if i > 0:
                    time_diff = (annotation['time'] - annotations[i-1]['time']).total_seconds()
                    if time_diff < 120:  # If within 2 minutes, alternate level
                        level_index = (level_index + 1) % len(y_levels)
                    else:
                        level_index = 0  # Reset to top level
                
                y_position = y_levels[level_index]
                
                # Add vertical line at annotation time
                line_color = 'blue' if annotation.get('has_song', False) else 'gray'
                ax.axvline(x=annotation['time'], color=line_color, linestyle=':', alpha=0.4, linewidth=0.8)
                
                # Add full annotation text
                ax.annotate(
                    annotation['text'],
                    xy=(annotation['time'], y_position),
                    xycoords=('data', 'axes fraction'),
                    ha='center',  # Center align for better readability
                    va='top',
                    fontsize=7,
                    rotation=0,  # No rotation for better readability of full text
                    bbox=dict(boxstyle="round,pad=0.3", 
                             fc="lightyellow" if annotation.get('has_song', False) else "white", 
                             ec="blue" if annotation.get('has_song', False) else "gray", 
                             lw=0.5, alpha=0.95),
                    arrowprops=dict(arrowstyle="-", connectionstyle="arc3,rad=0.1", 
                                  color=line_color, alpha=0.5, lw=0.5)
                )
        
        # Add statistics for total
        mean_val = ts_df['Total_Agitation'].mean()
        max_val = ts_df['Total_Agitation'].max()
        non_zero_pct = (ts_df['Total_Agitation'] > 0).mean() * 100
        
        stats_text = f'Mean: {mean_val:.2f} | Max: {max_val} | Active: {non_zero_pct:.1f}%'
        ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, 
               fontsize=8, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax.set_xlabel('Time (HH:MM:SS)', fontsize=11, fontweight='bold')
        
        # Add legend for severity levels to first plot
        legend_elements = [mpatches.Patch(color=colors[i], alpha=0.3, label=level_names[i]) 
                          for i in range(5)]
        if music_start:
            legend_elements.append(mpatches.Patch(color='lightgray', alpha=0.3, label='Music Period'))
        axes[0].legend(handles=legend_elements, loc='upper right', ncol=6, fontsize=8)
        
        # Rotate x-axis labels
        fig.autofmt_xdate()
        
        # Adjust layout with extra space for annotations
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.3)  # Extra room for annotations
        
        # Save the plot
        plot_file = save_path.replace('.csv', '_annotated_plot.png')
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"  ✓ Annotated plot saved: {os.path.basename(plot_file)}")
        
        # Close the plot to free memory and avoid blocking
        plt.close(fig)
        
        return plot_file
    
    def process_folder(self, folder_path):
        """Process all observation files in a folder"""
        # Find all files ending with Pittsburgh observations
        pattern = os.path.join(folder_path, "**", "*Observations_with_Pittsburgh_Scale.csv")
        observation_files = glob.glob(pattern, recursive=True)
        
        if not observation_files:
            print(f"\n⚠️  No files ending with 'Observations_with_Pittsburgh_Scale.csv' found in {folder_path}")
            print("   Please ensure you have processed observation files with the Pittsburgh Scale first.")
            return []
        
        print(f"\n✅ Found {len(observation_files)} observation files to process")
        print("="*60)
        
        processed_files = []
        
        for i, obs_file in enumerate(observation_files, 1):
            print(f"\n[{i}/{len(observation_files)}] Processing file...")
            
            try:
                # Generate time series
                ts_df, obs_df = self.process_observation_file(obs_file)
                
                if ts_df is not None and obs_df is not None:
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
                    print(f"  ✓ Saved time series: {os.path.basename(output_name)}")
                    
                    # Create and save annotated plot
                    self.plot_time_series_with_annotations(ts_df, obs_df, obs_file, output_path)
                    print(f"  ✓ Created annotated plot")
                    
                    processed_files.append(output_path)
                else:
                    print(f"  ⚠️  Skipped: Could not process {os.path.basename(obs_file)}")
                    
            except Exception as e:
                print(f"  ❌ Error processing {os.path.basename(obs_file)}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n{'='*60}")
        print(f"🎉 Processing complete!")
        print(f"   Generated {len(processed_files)} time series files with annotated plots")
        print(f"   All files saved in their respective directories")
        
        return processed_files

def main():
    """Main function to run the time series generator"""
    
    print("\n" + "="*70)
    print(" PITTSBURGH AGITATION SCALE - TIME SERIES GENERATOR ")
    print("="*70)
    
    print("\n📋 INSTRUCTIONS:")
    print("   1. This tool converts Pittsburgh Scale observations to time series data")
    print("   2. It creates 1-second resolution data with annotated visualizations")
    print("   3. You need to select the folder containing your processed observation files")
    print("   4. Files must end with '_Observations_with_Pittsburgh_Scale.csv'")
    print("\n" + "-"*70)
    
    # Create root window (hidden)
    root = tk.Tk()
    root.withdraw()
    
    # Show message box with instructions
    response = messagebox.showinfo(
        "Pittsburgh Time Series Generator",
        "Please select the folder containing your Pittsburgh observation files.\n\n" +
        "The tool will:\n" +
        "• Generate 1-second time series data\n" +
        "• Create annotated visualization plots with full text\n" +
        "• Save all outputs in the same directories\n\n" +
        "Click OK to select your folder."
    )
    
    print("\n🗂️  Please select your data folder in the dialog window...")
    
    # Ask user to select folder
    folder_path = filedialog.askdirectory(
        title="Select Folder with Pittsburgh Observation Files (*_Observations_with_Pittsburgh_Scale.csv)"
    )
    
    if not folder_path:
        print("\n❌ No folder selected. Exiting.")
        messagebox.showwarning("Cancelled", "No folder selected. The program will now exit.")
        return
    
    print(f"\n📁 Selected folder: {folder_path}")
    print("-"*70)
    
    # Create generator and process folder
    generator = PittsburghTimeSeriesGenerator()
    processed_files = generator.process_folder(folder_path)
    
    if processed_files:
        # Show completion message
        messagebox.showinfo(
            "Processing Complete!",
            f"Successfully processed {len(processed_files)} files!\n\n" +
            "Generated outputs:\n" +
            "• Time series CSV files (*_Pittsburgh_TimeSeries_1sec.csv)\n" +
            "• Annotated plot images (*_annotated_plot.png) with full text\n\n" +
            "All files saved in their original directories."
        )
        print("\n✅ All files processed successfully!")
    else:
        messagebox.showwarning(
            "No Files Processed",
            "No valid Pittsburgh observation files were found or processed.\n\n" +
            "Please ensure your folder contains files ending with:\n" +
            "'_Observations_with_Pittsburgh_Scale.csv'"
        )
        print("\n⚠️  No files were processed.")

if __name__ == "__main__":
    main()
