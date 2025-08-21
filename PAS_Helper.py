import os
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import scrolledtext
import glob

class PittsburghObservationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Pittsburgh Agitation Scale Observation Tool")
        self.root.geometry("1005x1000")
        
        # Variables
        self.current_csv_path = None
        self.current_df = None
        self.csv_files = []
        self.current_file_index = 0
        self.current_row_index = 0
        self.unsaved_changes = False
        
        # Pittsburgh Agitation Scale parameters
        self.pas_categories = {
            'Aberrant Vocalization': ['0 - Not present', '1 - Low volume', '2 - Louder than conversational', '3 - Extremely loud', '4 - Extremely loud with combativeness'],
            'Motor Agitation': ['0 - Not present', '1 - Pacing/aimless wandering', '2 - Trying to get to different place', '3 - Grabbing/clinging to people', '4 - Pushing/shoving/pacing with combativeness'],
            'Aggressiveness': ['0 - Not present', '1 - Threatening verbal', '2 - Threatening gestures', '3 - Grabbing/pushing without injury', '4 - Hitting/kicking/biting/scratching'],
            'Resisting Care': ['0 - Not present', '1 - Procrastination/avoidance', '2 - Verbal/gesture refusal', '3 - Pushing away to avoid task', '4 - Hitting/kicking to avoid task']
        }
        
        self.setup_ui()
        self.setup_global_keybindings()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Top frame - folder selection and file info
        top_frame = ttk.LabelFrame(main_frame, text="Dataset Selection", padding="10")
        top_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(top_frame, text="Select PwD Dataset Folder", 
                  command=self.select_folder).grid(row=0, column=0, padx=5)
        
        self.folder_label = ttk.Label(top_frame, text="No folder selected")
        self.folder_label.grid(row=0, column=1, padx=5)
        
        # Unsaved changes indicator
        self.unsaved_indicator = ttk.Label(top_frame, text="", foreground="red", font=('Arial', 10, 'bold'))
        self.unsaved_indicator.grid(row=0, column=2, padx=20)
        
        self.file_info_label = ttk.Label(top_frame, text="")
        self.file_info_label.grid(row=1, column=0, columnspan=3, pady=5)
        
        # CSV Navigation frame
        csv_nav_frame = ttk.Frame(main_frame)
        csv_nav_frame.grid(row=1, column=0, columnspan=3, pady=10)
        
        ttk.Button(csv_nav_frame, text="◀ Previous CSV File", 
                  command=self.previous_csv).grid(row=0, column=0, padx=5)
        ttk.Button(csv_nav_frame, text="Next CSV File ▶", 
                  command=self.next_csv).grid(row=0, column=1, padx=5)
        
        # Add keyboard hints
        ttk.Label(csv_nav_frame, text="(Alt+Left / Alt+Right)", 
                 font=('Arial', 9), foreground='gray').grid(row=1, column=0, columnspan=2, pady=2)
        
        # Middle section container
        middle_container = ttk.Frame(main_frame)
        middle_container.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Left side - Observations display
        obs_container = ttk.Frame(middle_container)
        obs_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Current observation frame
        current_obs_frame = ttk.LabelFrame(obs_container, text="CURRENT OBSERVATION", padding="10")
        current_obs_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Header info frame (Time, Song, Score)
        header_frame = ttk.Frame(current_obs_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.time_label = ttk.Label(header_frame, text="Time: --", font=('Arial', 11))
        self.time_label.grid(row=0, column=0, padx=10, sticky=tk.W)
        
        self.song_label = ttk.Label(header_frame, text="Song: --", font=('Arial', 11))
        self.song_label.grid(row=0, column=1, padx=10, sticky=tk.W)
        
        self.score_label = ttk.Label(header_frame, text="Score: --", font=('Arial', 11))
        self.score_label.grid(row=0, column=2, padx=10, sticky=tk.W)
        
        # Main observation text
        self.observation_text = tk.Text(current_obs_frame, height=8, width=70, wrap=tk.WORD, 
                                       font=('Arial', 14), bg='#f8f8f8')
        self.observation_text.grid(row=1, column=0, pady=5)
        self.observation_text.config(state=tk.DISABLED)  # Make read-only
        
        self.row_info_label = ttk.Label(current_obs_frame, text="Row: 0/0", font=('Arial', 10, 'bold'))
        self.row_info_label.grid(row=2, column=0, pady=5)
        
        # Next observation preview frame
        next_obs_frame = ttk.LabelFrame(obs_container, text="NEXT OBSERVATION PREVIEW", padding="10")
        next_obs_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Next observation header
        next_header_frame = ttk.Frame(next_obs_frame)
        next_header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.next_time_label = ttk.Label(next_header_frame, text="Time: --", font=('Arial', 10), foreground='gray')
        self.next_time_label.grid(row=0, column=0, padx=10, sticky=tk.W)
        
        self.next_song_label = ttk.Label(next_header_frame, text="Song: --", font=('Arial', 10), foreground='gray')
        self.next_song_label.grid(row=0, column=1, padx=10, sticky=tk.W)
        
        self.next_score_label = ttk.Label(next_header_frame, text="Score: --", font=('Arial', 10), foreground='gray')
        self.next_score_label.grid(row=0, column=2, padx=10, sticky=tk.W)
        
        # Next observation text (smaller)
        self.next_observation_text = tk.Text(next_obs_frame, height=4, width=70, wrap=tk.WORD, 
                                            font=('Arial', 11), bg='#f0f0f0', foreground='gray')
        self.next_observation_text.grid(row=1, column=0)
        self.next_observation_text.config(state=tk.DISABLED)  # Make read-only
        
        # Right side - Row navigation buttons
        nav_frame = ttk.LabelFrame(middle_container, text="ROW NAVIGATION", padding="10")
        nav_frame.grid(row=0, column=1, sticky=(tk.N, tk.S), padx=10)
        
        ttk.Button(nav_frame, text="↑\nPrevious\nRow", width=12, 
                  command=self.previous_row).grid(row=0, column=0, pady=10)
        
        ttk.Label(nav_frame, text="(Up Arrow)", font=('Arial', 9), 
                 foreground='gray').grid(row=1, column=0)
        
        self.current_row_label = ttk.Label(nav_frame, text="Current\nRow: 1", 
                                          font=('Arial', 11, 'bold'), justify=tk.CENTER)
        self.current_row_label.grid(row=2, column=0, pady=15)
        
        ttk.Button(nav_frame, text="↓\nNext\nRow", width=12, 
                  command=self.next_row).grid(row=3, column=0, pady=10)
        
        ttk.Label(nav_frame, text="(Down Arrow)", font=('Arial', 9), 
                 foreground='gray').grid(row=4, column=0)
        
        # Auto-save indicator
        self.autosave_label = ttk.Label(nav_frame, text="✓ Auto-save enabled", 
                                       font=('Arial', 9), foreground='green')
        self.autosave_label.grid(row=5, column=0, pady=10)
        
        # Pittsburgh Scale Rating Section
        rating_frame = ttk.LabelFrame(main_frame, text="Pittsburgh Agitation Scale Rating", padding="10")
        rating_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.rating_vars = {}
        self.rating_combos = {}  # Store references to comboboxes
        
        for i, (category, options) in enumerate(self.pas_categories.items()):
            ttk.Label(rating_frame, text=f"{category}:", font=('Arial', 10, 'bold')).grid(
                row=i, column=0, sticky=tk.W, pady=5, padx=5)
            
            self.rating_vars[category] = tk.StringVar(value=options[0])
            combo = ttk.Combobox(rating_frame, textvariable=self.rating_vars[category], 
                                values=options, width=50, state='readonly')
            combo.grid(row=i, column=1, pady=5, padx=5)
            
            # Store reference to combo
            self.rating_combos[category] = combo
            
            # Bind change event to mark unsaved changes
            combo.bind('<<ComboboxSelected>>', lambda e: self.mark_unsaved())
            
            # Override arrow key behavior in comboboxes
            combo.bind('<Up>', lambda e: (self.previous_row(), "break")[1])
            combo.bind('<Down>', lambda e: (self.next_row(), "break")[1])
            combo.bind('<Left>', lambda e: "break")
            combo.bind('<Right>', lambda e: "break")
        
        # Time duration input (in seconds)
        duration_frame = ttk.Frame(rating_frame)
        duration_frame.grid(row=len(self.pas_categories), column=0, columnspan=2, pady=10)
        
        ttk.Label(duration_frame, text="Observation Duration (seconds):", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, padx=5)
        self.duration_var = tk.StringVar(value="60")  # Default 1 minutes = 60 seconds
        self.duration_entry = ttk.Entry(duration_frame, textvariable=self.duration_var, width=10)
        self.duration_entry.grid(row=0, column=1, padx=5)
        self.duration_entry.bind('<KeyRelease>', lambda e: self.mark_unsaved() if e.keysym not in ['Up', 'Down', 'Left', 'Right'] else None)
        
        # Override arrow keys in entry field
        self.duration_entry.bind('<Up>', lambda e: (self.previous_row(), "break")[1])
        self.duration_entry.bind('<Down>', lambda e: (self.next_row(), "break")[1])
        
        # Helper label for common durations
        ttk.Label(duration_frame, text="(e.g., 60s = 1 min, 300s = 5 min, 600s = 10 min)", 
                 font=('Arial', 9), foreground='gray').grid(row=0, column=2, padx=5)
        
        # Save buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="Set All to 0 (Not Present) [Ctrl+0]", 
                  command=self.set_all_zero, style='Warning.TButton').grid(row=0, column=0, padx=5)
        
        # Main save button - now the primary action
        self.save_file_btn = ttk.Button(button_frame, text="💾 Save File to Disk [Ctrl+S]", 
                                        command=self.save_file, style='Accent.TButton')
        self.save_file_btn.grid(row=0, column=1, padx=20)
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text="Ready | Use Arrow Keys to Navigate", relief=tk.SUNKEN)
        self.status_label.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
    def setup_global_keybindings(self):
        """Setup global keyboard shortcuts that work regardless of focus"""
        # Use bind_all for global bindings that work everywhere
        self.root.bind_all('<Up>', lambda e: self.previous_row())
        self.root.bind_all('<Down>', lambda e: self.next_row())
        self.root.bind_all('<Alt-Left>', lambda e: self.previous_csv())
        self.root.bind_all('<Alt-Right>', lambda e: self.next_csv())
        self.root.bind_all('<Control-s>', lambda e: self.save_file())
        self.root.bind_all('<Control-0>', lambda e: self.set_all_zero())
        
        # Alternative number keys for ratings (1-4 for quick rating)
        self.root.bind_all('<Control-1>', lambda e: self.quick_set_rating(1))
        self.root.bind_all('<Control-2>', lambda e: self.quick_set_rating(2))
        self.root.bind_all('<Control-3>', lambda e: self.quick_set_rating(3))
        self.root.bind_all('<Control-4>', lambda e: self.quick_set_rating(4))
        
    def quick_set_rating(self, rating_level):
        """Quick set all ratings to the same level using number keys"""
        for category in self.pas_categories:
            self.rating_vars[category].set(self.pas_categories[category][rating_level])
        self.mark_unsaved()
        self.update_status(f"All ratings set to level {rating_level}")
        
    def mark_unsaved(self):
        """Mark that there are unsaved changes"""
        self.unsaved_changes = True
        self.unsaved_indicator.config(text="⚠ Unsaved changes")
        self.save_file_btn.config(text="💾 Save File to Disk* [Ctrl+S]")
        
    def clear_unsaved(self):
        """Clear the unsaved changes indicator"""
        self.unsaved_changes = False
        self.unsaved_indicator.config(text="")
        self.save_file_btn.config(text="💾 Save File to Disk [Ctrl+S]")
        
    def auto_save_current_row(self):
        """Automatically save the current row's ratings to the dataframe"""
        if self.current_df is None:
            return
            
        # Check if any rating is set (not default)
        any_rating_set = False
        for category, var in self.rating_vars.items():
            if var.get() != self.pas_categories[category][0]:
                any_rating_set = True
                break
        
        # If no rating is set, automatically set all to 0
        if not any_rating_set:
            for category in self.pas_categories:
                self.rating_vars[category].set(self.pas_categories[category][0])
        
        # Save ratings to dataframe
        for category, var in self.rating_vars.items():
            col_name = category.replace(' ', '_')
            # Extract just the number from the rating (e.g., "0 - Not present" -> "0")
            rating_value = var.get().split(' - ')[0]
            self.current_df.at[self.current_row_index, col_name] = rating_value
        
        # Save duration in seconds
        try:
            duration = float(self.duration_var.get())
            if duration <= 0:
                duration = 60  # Default to 60 seconds if invalid
            self.current_df.at[self.current_row_index, 'Duration_Seconds'] = duration
        except ValueError:
            self.current_df.at[self.current_row_index, 'Duration_Seconds'] = 60
        
        self.update_status(f"Auto-saved row {self.current_row_index + 1}")
        self.mark_unsaved()
        
    def select_folder(self):
        folder_path = filedialog.askdirectory(title="Select PwD Dataset Folder")
        if folder_path:
            # Find all CSV files ending with "Observations.csv"
            pattern = os.path.join(folder_path, "**", "*Observations.csv")
            self.csv_files = glob.glob(pattern, recursive=True)
            
            if not self.csv_files:
                messagebox.showwarning("No Files Found", 
                                      "No CSV files ending with 'Observations.csv' found in the selected folder.")
                return
            
            self.folder_label.config(text=f"Folder: {os.path.basename(folder_path)}")
            self.current_file_index = 0
            self.load_csv(self.csv_files[0])
            self.update_status(f"Found {len(self.csv_files)} observation files | Use Arrow Keys to Navigate")
            
    def load_csv(self, csv_path):
        try:
            self.current_csv_path = csv_path
            self.current_df = pd.read_csv(csv_path)
            
            # Add new columns if they don't exist
            new_columns = ['Aberrant_Vocalization', 'Motor_Agitation', 
                          'Aggressiveness', 'Resisting_Care', 'Duration_Seconds']
            
            for col in new_columns:
                if col not in self.current_df.columns:
                    self.current_df[col] = ''
            
            self.current_row_index = 0
            self.display_current_row()
            self.display_next_row()
            self.clear_unsaved()
            
            filename = os.path.basename(csv_path)
            self.file_info_label.config(
                text=f"Current file: {filename} ({self.current_file_index + 1}/{len(self.csv_files)})")
            
            # Set focus to main frame to ensure arrow keys work
            self.root.focus_set()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {str(e)}")
            
    def display_current_row(self):
        if self.current_df is None or len(self.current_df) == 0:
            return
            
        row = self.current_df.iloc[self.current_row_index]
        
        # Update header labels
        if 'Time' in row:
            self.time_label.config(text=f"Time: {row['Time']}")
        if 'Song' in row:
            self.song_label.config(text=f"Song: {row['Song']}")
        if 'Score' in row:
            self.score_label.config(text=f"Score: {row['Score']}")
        
        # Display main observation text
        self.observation_text.config(state=tk.NORMAL)
        self.observation_text.delete(1.0, tk.END)
        if 'Observation' in row:
            self.observation_text.insert(1.0, str(row['Observation']))
        else:
            # If no specific Observation column, show all other data
            display_text = ""
            for col in self.current_df.columns:
                if col not in ['Aberrant_Vocalization', 'Motor_Agitation', 
                              'Aggressiveness', 'Resisting_Care', 'Duration_Seconds',
                              'Time', 'Song', 'Score']:
                    display_text += f"{col}: {row[col]}\n"
            self.observation_text.insert(1.0, display_text)
        self.observation_text.config(state=tk.DISABLED)
        
        # Update row info
        self.row_info_label.config(
            text=f"Row: {self.current_row_index + 1}/{len(self.current_df)}")
        self.current_row_label.config(
            text=f"Current\nRow: {self.current_row_index + 1}")
        
        # Load existing ratings if present
        has_ratings = False
        for category in self.pas_categories:
            col_name = category.replace(' ', '_')
            if col_name in row and pd.notna(row[col_name]) and row[col_name] != '':
                # Find the matching option from the dropdown
                rating_value = str(row[col_name])
                for option in self.pas_categories[category]:
                    if option.startswith(rating_value + ' -'):
                        self.rating_vars[category].set(option)
                        has_ratings = True
                        break
            else:
                self.rating_vars[category].set(self.pas_categories[category][0])
        
        if 'Duration_Seconds' in row and pd.notna(row['Duration_Seconds']) and row['Duration_Seconds'] != '':
            self.duration_var.set(str(row['Duration_Seconds']))
        else:
            self.duration_var.set("60")  # Default to 60 seconds (10 minutes)
            
    def display_next_row(self):
        """Display preview of the next row"""
        if self.current_df is None or len(self.current_df) == 0:
            return
            
        self.next_observation_text.config(state=tk.NORMAL)
        
        if self.current_row_index < len(self.current_df) - 1:
            next_row = self.current_df.iloc[self.current_row_index + 1]
            
            # Update next row header labels
            if 'Time' in next_row:
                self.next_time_label.config(text=f"Time: {next_row['Time']}")
            else:
                self.next_time_label.config(text="Time: --")
                
            if 'Song' in next_row:
                self.next_song_label.config(text=f"Song: {next_row['Song']}")
            else:
                self.next_song_label.config(text="Song: --")
                
            if 'Score' in next_row:
                self.next_score_label.config(text=f"Score: {next_row['Score']}")
            else:
                self.next_score_label.config(text="Score: --")
            
            # Display next observation text
            self.next_observation_text.delete(1.0, tk.END)
            if 'Observation' in next_row:
                self.next_observation_text.insert(1.0, str(next_row['Observation']))
            else:
                display_text = ""
                for col in self.current_df.columns:
                    if col not in ['Aberrant_Vocalization', 'Motor_Agitation', 
                                  'Aggressiveness', 'Resisting_Care', 'Duration_Seconds',
                                  'Time', 'Song', 'Score']:
                        display_text += f"{col}: {next_row[col]}\n"
                self.next_observation_text.insert(1.0, display_text)
        else:
            # No next row
            self.next_time_label.config(text="Time: --")
            self.next_song_label.config(text="Song: --")
            self.next_score_label.config(text="Score: --")
            self.next_observation_text.delete(1.0, tk.END)
            self.next_observation_text.insert(1.0, "No more observations in this file")
            
        self.next_observation_text.config(state=tk.DISABLED)
            
    def set_all_zero(self):
        """Set all ratings to 0 (Not present) for quick entry"""
        for category in self.pas_categories:
            self.rating_vars[category].set(self.pas_categories[category][0])
        self.update_status("All ratings set to 0 - Not present")
        self.mark_unsaved()
        return "break"  # Prevent event propagation
        
    def save_file(self):
        if self.current_df is None or self.current_csv_path is None:
            return "break"
            
        # Auto-save current row before saving file
        self.auto_save_current_row()
        
        # Generate new filename
        base_name = os.path.basename(self.current_csv_path)
        dir_name = os.path.dirname(self.current_csv_path)
        
        # Remove "Observations.csv" and add "Pittsburgh_Observations.csv"
        new_name = base_name.replace("Observations.csv", "Observations_with_Pittsburgh_Scale.csv")
        new_path = os.path.join(dir_name, new_name)
        
        try:
            self.current_df.to_csv(new_path, index=False)
            self.update_status(f"Saved to {new_name}")
            self.clear_unsaved()
            messagebox.showinfo("Success", f"File saved as:\n{new_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
        
        return "break"  # Prevent event propagation
            
    def next_csv(self):
        if self.current_file_index < len(self.csv_files) - 1:
            # Auto-save current row before switching
            self.auto_save_current_row()
            
            if self.unsaved_changes:
                if messagebox.askyesno("Save Changes", "Save current file before moving to next?"):
                    self.save_file()
            
            self.current_file_index += 1
            self.load_csv(self.csv_files[self.current_file_index])
        return "break"  # Prevent event propagation
            
    def previous_csv(self):
        if self.current_file_index > 0:
            # Auto-save current row before switching
            self.auto_save_current_row()
            
            if self.unsaved_changes:
                if messagebox.askyesno("Save Changes", "Save current file before moving to previous?"):
                    self.save_file()
            
            self.current_file_index -= 1
            self.load_csv(self.csv_files[self.current_file_index])
        return "break"  # Prevent event propagation
            
    def next_row(self):
        if self.current_df is not None and self.current_row_index < len(self.current_df) - 1:
            # Auto-save current row before moving
            self.auto_save_current_row()
            
            self.current_row_index += 1
            self.display_current_row()
            self.display_next_row()
            
            # Remove focus from any widget to ensure arrow keys keep working
            self.root.focus_set()
        return "break"  # Prevent event propagation
            
    def previous_row(self):
        if self.current_row_index > 0:
            # Auto-save current row before moving
            self.auto_save_current_row()
            
            self.current_row_index -= 1
            self.display_current_row()
            self.display_next_row()
            
            # Remove focus from any widget to ensure arrow keys keep working
            self.root.focus_set()
        return "break"  # Prevent event propagation
            
    def on_closing(self):
        """Handle window closing event"""
        if self.unsaved_changes:
            if messagebox.askyesnocancel("Save Changes", "Do you want to save changes before closing?"):
                self.save_file()
                self.root.destroy()
            elif messagebox.askyesno("Confirm", "Close without saving?"):
                self.root.destroy()
        else:
            self.root.destroy()
            
    def update_status(self, message):
        self.status_label.config(text=message)

def main():
    root = tk.Tk()
    app = PittsburghObservationTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()
