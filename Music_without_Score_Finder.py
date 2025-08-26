import os
import pandas as pd
from pathlib import Path
from collections import defaultdict
import warnings
import tkinter as tk
from tkinter import filedialog, messagebox
import re
warnings.filterwarnings('ignore')

def select_folder():
    """Open a dialog window to select the PwD dataset folder"""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.title("Select PwD Dataset Folder")
    
    # Show instructions in a message box
    messagebox.showinfo(
        "Folder Selection", 
        "Please select your PwD dataset folder containing patient subfolders"
    )
    
    # Open folder selection dialog
    folder_path = filedialog.askdirectory(
        title="Select PwD Dataset Folder",
        initialdir=os.getcwd()
    )
    
    root.destroy()
    return folder_path

def extract_session_info(folder_name):
    """Extract session date and time from folder name"""
    # Pattern to match date and time period
    # Examples: "August 5 Morning AN 000133", "July 29 Afternoon AF 000233"
    
    # Try to extract month, day, and time period
    pattern = r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+\s+(?:Morning|Afternoon|Evening|Night))'
    match = re.search(pattern, folder_name, re.IGNORECASE)
    
    if match:
        return match.group(1)
    
    # If no match, return the full folder name
    return folder_name

def extract_patient_id(folder_name):
    """Extract patient ID from folder name"""
    # Pattern to match patient IDs like "AN 000133", "AF 000233", etc.
    pattern = r'([A-Z]{1,2}\s+\d{6})'
    match = re.search(pattern, folder_name)
    
    if match:
        return match.group(1)
    
    # If no match, return the last part of the folder name
    parts = folder_name.split()
    if len(parts) >= 2:
        return ' '.join(parts[-2:])
    return folder_name

def find_csv_files(root_folder):
    """Find all CSV files ending with 'Observations_with_Pittsburgh_Scale.csv'"""
    csv_files = []
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.endswith("Observations_with_Pittsburgh_Scale.csv"):
                csv_files.append(os.path.join(root, file))
    return csv_files

def is_valid_song_name(song_name):
    """Check if the entry is a valid song name (not just dashes or empty)"""
    if pd.isna(song_name):
        return False
    
    # Convert to string and strip whitespace
    song_str = str(song_name).strip()
    
    # List of invalid entries to skip
    invalid_entries = ['—', '-', '--', '---', '----', '–', '−', '']
    
    # Check if the song name is in the invalid list
    if song_str in invalid_entries:
        return False
    
    # Also check if it's just dashes with spaces
    if song_str.replace(' ', '').replace('-', '').replace('—', '').replace('–', '') == '':
        return False
    
    return True

def normalize_song_name(song_name):
    """Normalize song names to identify the same song despite minor variations"""
    if pd.isna(song_name):
        return song_name
    
    normalized = str(song_name).strip()
    
    # Remove quotes and extra spaces
    normalized = normalized.replace('"', '').replace('"', '').replace('"', '')
    normalized = ' '.join(normalized.split())  # Remove multiple spaces
    
    # Extract just the song title (remove artist info after " - " or " by ")
    if ' - ' in normalized:
        normalized = normalized.split(' - ')[0].strip()
    if ' by ' in normalized.lower():
        idx = normalized.lower().index(' by ')
        normalized = normalized[:idx].strip()
    
    return normalized

def analyze_songs_and_scores(csv_file):
    """Analyze a single CSV file for songs with/without scores"""
    try:
        df = pd.read_csv(csv_file)
        
        # Identify columns
        song_columns = [col for col in df.columns if 'song' in col.lower() or 'music' in col.lower()]
        score_columns = [col for col in df.columns if 'score' in col.lower() or 'pittsburgh' in col.lower()]
        date_columns = [col for col in df.columns if 'date' in col.lower() or 'day' in col.lower() or 'time' in col.lower()]
        
        if not song_columns:
            print(f"Warning: No song column found in {csv_file}")
            return None
        
        song_col = song_columns[0]
        score_col = score_columns[0] if score_columns else None
        date_col = date_columns[0] if date_columns else None
        
        # Filter out rows where song column is empty, NaN, or contains only dashes
        df_with_songs = df[df[song_col].apply(is_valid_song_name)]
        
        if df_with_songs.empty:
            print(f"  No valid song entries found in {os.path.basename(csv_file)}")
            return None
        
        # Add normalized song name column
        df_with_songs = df_with_songs.copy()
        df_with_songs['normalized_song'] = df_with_songs[song_col].apply(normalize_song_name)
        
        # Identify songs with and without scores
        if score_col:
            missing_scores = df_with_songs[df_with_songs[score_col].isna() | (df_with_songs[score_col] == '')]
            has_scores = df_with_songs[df_with_songs[score_col].notna() & (df_with_songs[score_col] != '')]
        else:
            print(f"Warning: No score column found in {csv_file}")
            missing_scores = df_with_songs
            has_scores = pd.DataFrame()
        
        # Count of skipped entries
        total_rows_with_song_col = df[df[song_col].notna()].shape[0]
        valid_songs = df_with_songs.shape[0]
        skipped = total_rows_with_song_col - valid_songs
        
        # Extract session and patient info
        folder_name = os.path.basename(os.path.dirname(csv_file))
        session = extract_session_info(folder_name)
        patient_id = extract_patient_id(folder_name)
        
        return {
            'file': folder_name,
            'session': session,
            'patient_id': patient_id,
            'missing_scores': missing_scores,
            'has_scores': has_scores,
            'song_col': song_col,
            'score_col': score_col,
            'date_col': date_col,
            'skipped_entries': skipped
        }
        
    except Exception as e:
        print(f"Error processing {csv_file}: {str(e)}")
        return None

def show_completion_message(output_file):
    """Show a completion message with the output file location"""
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "Analysis Complete", 
        f"Analysis complete!\n\nResults have been saved to:\n{output_file}\n\nCheck the console for detailed output."
    )
    root.destroy()

def main():
    # Get the dataset folder using file dialog
    print("=" * 60)
    print("**Song Score Analysis Tool**")
    print("=" * 60)
    print("\nA folder selection window will appear...")
    
    pwd_folder = select_folder()
    
    if not pwd_folder:
        print("No folder selected. Exiting...")
        return
    
    if not os.path.exists(pwd_folder):
        print(f"Error: The folder '{pwd_folder}' does not exist!")
        return
    
    # Find all relevant CSV files
    print(f"\nSelected folder: {pwd_folder}")
    print(f"Searching for CSV files...")
    csv_files = find_csv_files(pwd_folder)
    
    if not csv_files:
        print("No CSV files ending with 'Observations_with_Pittsburgh_Scale.csv' found!")
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "No Files Found",
            "No CSV files ending with 'Observations_with_Pittsburgh_Scale.csv' were found in the selected folder and its subfolders."
        )
        root.destroy()
        return
    
    print(f"Found {len(csv_files)} CSV file(s) to analyze")
    print("Note: Entries with '—' or similar dashes will be skipped")
    print("Results will be aggregated by session (date/time)\n")
    
    # Analyze each file
    all_results = []
    total_skipped = 0
    for csv_file in csv_files:
        print(f"Processing: {os.path.basename(csv_file)}")
        result = analyze_songs_and_scores(csv_file)
        if result is not None:
            all_results.append(result)
            if result['skipped_entries'] > 0:
                print(f"  → Skipped {result['skipped_entries']} non-song entries (dashes, etc.)")
            total_skipped += result.get('skipped_entries', 0)
    
    if not all_results:
        print("\nNo valid data found in the CSV files.")
        return
    
    # Group results by session
    sessions_data = defaultdict(lambda: {
        'patients': set(),
        'missing_songs_by_time': defaultdict(set),
        'all_missing_songs': set(),
        'has_scores_count': 0,
        'missing_scores_count': 0
    })
    
    for result in all_results:
        session = result['session']
        patient_id = result['patient_id']
        
        sessions_data[session]['patients'].add(patient_id)
        
        if result['has_scores'] is not None:
            sessions_data[session]['has_scores_count'] += len(result['has_scores'])
        
        if result['missing_scores'] is not None and not result['missing_scores'].empty:
            sessions_data[session]['missing_scores_count'] += len(result['missing_scores'])
            
            if result['date_col']:
                # Group by time within the session
                for _, row in result['missing_scores'].iterrows():
                    time = row[result['date_col']]
                    song = row['normalized_song'] if 'normalized_song' in row else row[result['song_col']]
                    sessions_data[session]['missing_songs_by_time'][time].add(song)
                    sessions_data[session]['all_missing_songs'].add(song)
            else:
                # Just add songs without time grouping
                for _, row in result['missing_scores'].iterrows():
                    song = row['normalized_song'] if 'normalized_song' in row else row[result['song_col']]
                    sessions_data[session]['all_missing_songs'].add(song)
    
    if total_skipped > 0:
        print(f"\nTotal non-song entries skipped across all files: {total_skipped}")
    
    # Sort sessions chronologically
    def sort_session_key(session):
        months = ['January', 'February', 'March', 'April', 'May', 'June', 
                  'July', 'August', 'September', 'October', 'November', 'December']
        for i, month in enumerate(months):
            if month in session:
                # Extract day number
                day_match = re.search(r'\d+', session)
                day = int(day_match.group()) if day_match else 0
                # Morning = 0, Afternoon = 1, Evening = 2, Night = 3
                time_order = 0
                if 'Afternoon' in session:
                    time_order = 1
                elif 'Evening' in session:
                    time_order = 2
                elif 'Night' in session:
                    time_order = 3
                return (i, day, time_order)
        return (99, 0, 0)
    
    sorted_sessions = sorted(sessions_data.keys(), key=sort_session_key)
    
    # Output results by session
    print("\n" + "=" * 60)
    print("**SONGS WITH MISSING SCORES (BY SESSION)**")
    print("=" * 60)
    
    for session in sorted_sessions:
        data = sessions_data[session]
        if data['all_missing_songs']:
            print(f"\n**Session: {session}**")
            print(f"Participants: {', '.join(sorted(data['patients']))}")
            
            if data['missing_songs_by_time']:
                # Sort times
                sorted_times = sorted(data['missing_songs_by_time'].keys())
                for time in sorted_times:
                    songs = data['missing_songs_by_time'][time]
                    print(f"\n  Time: {time}")
                    for song in sorted(songs):
                        print(f"    • {song}")
            else:
                print("\n  Songs missing scores:")
                for song in sorted(data['all_missing_songs']):
                    print(f"    • {song}")
    
    # Summary
    print("\n" + "=" * 60)
    print("**SESSION SUMMARY**")
    print("=" * 60)
    
    total_with_scores = 0
    total_without_scores = 0
    
    for session in sorted_sessions:
        data = sessions_data[session]
        total_with_scores += data['has_scores_count']
        total_without_scores += data['missing_scores_count']
        
        print(f"\n**{session}**")
        print(f"  Participants: {len(data['patients'])} ({', '.join(sorted(data['patients']))})")
        print(f"  Songs with scores: {data['has_scores_count']}")
        print(f"  Songs without scores: {data['missing_scores_count']}")
        print(f"  Unique songs missing scores: {len(data['all_missing_songs'])}")
        
        if (data['has_scores_count'] + data['missing_scores_count']) > 0:
            completion = data['has_scores_count'] / (data['has_scores_count'] + data['missing_scores_count']) * 100
            print(f"  Completion rate: {completion:.1f}%")
    
    print("\n" + "=" * 60)
    print("**TOTAL SUMMARY**")
    print("=" * 60)
    print(f"Total sessions analyzed: {len(sessions_data)}")
    print(f"Total valid songs with scores: {total_with_scores}")
    print(f"Total valid songs without scores: {total_without_scores}")
    print(f"Total non-song entries skipped: {total_skipped}")
    if (total_with_scores + total_without_scores) > 0:
        print(f"Overall completion rate: {total_with_scores/(total_with_scores + total_without_scores)*100:.1f}%")
    
    # Save results to file
    output_file = os.path.join(pwd_folder, "song_score_analysis_by_session.txt")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("SONG SCORE ANALYSIS RESULTS (BY SESSION)\n")
            f.write("=" * 60 + "\n")
            f.write(f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Note: Results aggregated by session (date/time)\n")
            f.write(f"Note: Entries with '—' or dashes were skipped\n\n")
            
            f.write("SONGS WITH MISSING SCORES BY SESSION\n")
            f.write("-" * 40 + "\n")
            
            for session in sorted_sessions:
                data = sessions_data[session]
                if data['all_missing_songs']:
                    f.write(f"\nSession: {session}\n")
                    f.write(f"Participants: {', '.join(sorted(data['patients']))}\n")
                    
                    if data['missing_songs_by_time']:
                        sorted_times = sorted(data['missing_songs_by_time'].keys())
                        for time in sorted_times:
                            songs = data['missing_songs_by_time'][time]
                            f.write(f"  Time: {time}\n")
                            for song in sorted(songs):
                                f.write(f"    • {song}\n")
                    else:
                        f.write("  Songs missing scores:\n")
                        for song in sorted(data['all_missing_songs']):
                            f.write(f"    • {song}\n")
            
            f.write("\n\nSESSION SUMMARY\n")
            f.write("-" * 40 + "\n")
            for session in sorted_sessions:
                data = sessions_data[session]
                f.write(f"\n{session}\n")
                f.write(f"  Participants: {len(data['patients'])} ({', '.join(sorted(data['patients']))})\n")
                f.write(f"  Songs with scores: {data['has_scores_count']}\n")
                f.write(f"  Songs without scores: {data['missing_scores_count']}\n")
                f.write(f"  Unique songs missing scores: {len(data['all_missing_songs'])}\n")
                if (data['has_scores_count'] + data['missing_scores_count']) > 0:
                    completion = data['has_scores_count'] / (data['has_scores_count'] + data['missing_scores_count']) * 100
                    f.write(f"  Completion rate: {completion:.1f}%\n")
            
            f.write("\n\nTOTAL SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total sessions analyzed: {len(sessions_data)}\n")
            f.write(f"Total valid songs with scores: {total_with_scores}\n")
            f.write(f"Total valid songs without scores: {total_without_scores}\n")
            f.write(f"Total non-song entries skipped: {total_skipped}\n")
            if (total_with_scores + total_without_scores) > 0:
                f.write(f"Overall completion rate: {total_with_scores/(total_with_scores + total_without_scores)*100:.1f}%\n")
        
        print(f"\n\nResults saved to: {output_file}")
        show_completion_message(output_file)
        
    except Exception as e:
        print(f"\nError saving results to file: {str(e)}")

if __name__ == "__main__":
    main()
