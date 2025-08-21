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
        self.root.geometry("1200x800")
        
        # Variables
        self.current_csv_path = None
        self.current_df = None
        self.csv_files = []
        self.current_file_index = 0
        self.current_row_index = 0
        
        # Pittsburgh Agitation Scale parameters
        self.pas_categories = {
            'Aberrant Vocalization': ['0 - Not present', '1 - Low volume', '2 - Louder than conversational', '3 - Extremely loud', '4 - Extremely loud with combativeness'],
            'Motor Agitation': ['0 - Not present', '1 - Pacing/aimless wandering', '2 - Trying to get to different place', '3 - Grabbing/clinging to people', '4 - Pushing/shoving/pacing with combativeness'],
            'Aggressiveness': ['0 - Not present', '1 - Threatening verbal', '2 - Threatening gestures', '3 - Grabbing/pushing without injury', '4 - Hitting/kicking/biting/scratching'],
            'Resisting Care': ['0 - Not present', '1 - Procrastination/avoidance', '2 - Verbal/gesture refusal', '3 - Pushing away to avoid task', '4 - Hitting/kicking to avoid task']
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Top frame - folder selection and file info
        top_frame = ttk.LabelFrame(main_frame, text="Dataset Selection", padding="10")
        top_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(top_frame, text="Select PwD Dataset Folder", 
                  command=self.select_folder).grid(row=0, column=0, padx=5)
        
        self.folder_label = ttk.Label(top_frame, text="No folder selected")
        self.folder_label.grid(row=0, column=1, padx=5)
        
        self.file_info_label = ttk.Label(top_frame, text="")
        self.file_info_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Navigation frame
        nav_frame = ttk.Frame(main_frame)
        nav_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(nav_frame, text="◀ Previous CSV", 
                  command=self.previous_csv).grid(row=0, column=0, padx=5)
        ttk.Button(nav_frame, text="Next CSV ▶", 
                  command=self.next_csv).grid(row=0, column=1, padx=5)
        ttk.Button(nav_frame, text="◀ Previous Row", 
                  command=self.previous_row).grid(row=0, column=2, padx=20)
        ttk.Button(nav_frame, text="Next Row ▶", 
                  command=self.next_row).grid(row=0, column=3, padx=5)
        
        # Current observation display
        obs_frame = ttk.LabelFrame(main_frame, text="Current Observation", padding="10")
        obs_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.observation_text = scrolledtext.ScrolledText(obs_frame, height=8, width=100, wrap=tk.WORD)
        self.observation_text.grid(row=0, column=0, columnspan=2)
        
        self.row_info_label = ttk.Label(obs_frame, text="Row: 0/0")
        self.row_info_label.grid(row=1, column=0, pady=5)
        
        # Pittsburgh Scale Rating Section
        rating_frame = ttk.LabelFrame(main_frame, text="Pittsburgh Agitation Scale Rating", padding="10")
        rating_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.rating_vars = {}
        for i, (category, options) in enumerate(self.pas_categories.items()):
            ttk.Label(rating_frame, text=f"{category}:", font=('Arial', 10, 'bold')).grid(
                row=i, column=0, sticky=tk.W, pady=5, padx=5)
            
            self.rating_vars[category] = tk.StringVar(value=options[0])
            combo = ttk.Combobox(rating_frame, textvariable=self.rating_vars[category], 
                                values=options, width=50, state='readonly')
            combo.grid(row=i, column=1, pady=5, padx=5)
        
        # Time duration input
        duration_frame = ttk.Frame(rating_frame)
        duration_frame.grid(row=len(self.pas_categories), column=0, columnspan=2, pady=10)
        
        ttk.Label(duration_frame, text="Observation Duration (seconds):", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, padx=5)
        self.duration_var = tk.StringVar(value="10")
        ttk.Entry(duration_frame, textvariable=self.duration_var, width=10).grid(row=0, column=1, padx=5)
        
        # Save button
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Save Rating for Current Row", 
                  command=self.save_rating, style='Accent.TButton').grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Save All Changes to File", 
                  command=self.save_file, style='Accent.TButton').grid(row=0, column=1, padx=5)
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_label.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
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
            
            self.folder_label.config(text=f"Folder: {folder_path}")
            self.current_file_index = 0
            self.load_csv(self.csv_files[0])
            self.update_status(f"Found {len(self.csv_files)} observation files")
            
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
            
            filename = os.path.basename(csv_path)
            self.file_info_label.config(
                text=f"Current file: {filename} ({self.current_file_index + 1}/{len(self.csv_files)})")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {str(e)}")
            
    def display_current_row(self):
        if self.current_df is None or len(self.current_df) == 0:
            return
            
        row = self.current_df.iloc[self.current_row_index]
        
        # Display observation data
        self.observation_text.delete(1.0, tk.END)
        display_text = ""
        for col in self.current_df.columns:
            if col not in ['Aberrant_Vocalization', 'Motor_Agitation', 
                          'Aggressiveness', 'Resisting_Care', 'Duration_Seconds']:
                display_text += f"**{col}**: {row[col]}\n"
        
        self.observation_text.insert(1.0, display_text)
        
        # Update row info
        self.row_info_label.config(
            text=f"Row: {self.current_row_index + 1}/{len(self.current_df)}")
        
        # Load existing ratings if present
        if pd.notna(row.get('Aberrant_Vocalization', '')):
            for category in self.pas_categories:
                col_name = category.replace(' ', '_')
                if col_name in row and pd.notna(row[col_name]):
                    self.rating_vars[category].set(row[col_name])
        
        if 'Duration_Seconds' in row and pd.notna(row['Duration_Seconds']):
            self.duration_var.set(str(row['Duration_Seconds']))
            
    def save_rating(self):
        if self.current_df is None:
            return
            
        # Save ratings to dataframe
        for category, var in self.rating_vars.items():
            col_name = category.replace(' ', '_')
            self.current_df.at[self.current_row_index, col_name] = var.get()
        
        # Save duration
        try:
            duration = float(self.duration_var.get())
            self.current_df.at[self.current_row_index, 'Duration_Seconds'] = duration
        except ValueError:
            messagebox.showwarning("Invalid Duration", "Please enter a valid number for duration")
            return
        
        self.update_status(f"Saved rating for row {self.current_row_index + 1}")
        
        # Auto-advance to next row
        if self.current_row_index < len(self.current_df) - 1:
            self.next_row()
            
    def save_file(self):
        if self.current_df is None or self.current_csv_path is None:
            return
            
        # Generate new filename
        base_name = os.path.basename(self.current_csv_path)
        dir_name = os.path.dirname(self.current_csv_path)
        
        # Remove "Observations.csv" and add "Pittsburgh_Observations.csv"
        new_name = base_name.replace("Observations.csv", "Pittsburgh_Observations.csv")
        new_path = os.path.join(dir_name, new_name)
        
        try:
            self.current_df.to_csv(new_path, index=False)
            self.update_status(f"Saved to {new_name}")
            messagebox.showinfo("Success", f"File saved as:\n{new_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
            
    def next_csv(self):
        if self.current_file_index < len(self.csv_files) - 1:
            self.current_file_index += 1
            self.load_csv(self.csv_files[self.current_file_index])
            
    def previous_csv(self):
        if self.current_file_index > 0:
            self.current_file_index -= 1
            self.load_csv(self.csv_files[self.current_file_index])
            
    def next_row(self):
        if self.current_df is not None and self.current_row_index < len(self.current_df) - 1:
            self.current_row_index += 1
            self.display_current_row()
            
    def previous_row(self):
        if self.current_row_index > 0:
            self.current_row_index -= 1
            self.display_current_row()
            
    def update_status(self, message):
        self.status_label.config(text=message)

def main():
    root = tk.Tk()
    app = PittsburghObservationTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()
