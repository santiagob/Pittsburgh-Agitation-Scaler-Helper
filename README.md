# Pittsburgh Agitation Scale Observation Tool

## PAS Helper (PAS_Helper.py)

A desktop application for efficiently rating behavioral observations using the Pittsburgh Agitation Scale (PAS) for people with dementia (PwD) research datasets.

### Features

- 📁 **Batch Processing**: Automatically finds and processes all CSV files ending with "Observations.csv" in nested folders
- 👁️ **Dual View**: Shows current observation and preview of next observation simultaneously
- ⚡ **Keyboard Shortcuts**: Speed up your workflow with keyboard navigation
- 💾 **Auto-save**: Preserves your work with automatic prompts when switching files
- 📊 **4-Parameter Rating**: Complete Pittsburgh Agitation Scale implementation (0-4 scale)
- ⏱️ **Duration Tracking**: Records observation duration in seconds

### Installation

#### Prerequisites
- Python 3.7 or higher
- tkinter (usually comes with Python)

#### Setup

1. Clone this repository:
```bash
git clone https://github.com/yourusername/pittsburgh-observation-tool.git
cd pittsburgh-observation-tool
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

#### macOS Additional Setup
If tkinter is not installed:
```bash
brew install python-tk
```

#### Linux Additional Setup
If tkinter is not installed:
```bash
sudo apt-get install python3-tk
```

### Usage

1. Run the application:
```bash
python pittsburgh_tool.py
```

2. Click **"Select PwD Dataset Folder"** to choose your dataset directory

3. The tool will automatically find all CSV files ending with "Observations.csv"

4. For each observation:
   - Review the displayed observation text
   - Select ratings from the dropdown menus (0-4 scale)
   - Enter observation duration in seconds
   - Click "Save Rating" or press **Ctrl+S**

5. Navigate through:
   - **Rows**: Use Up/Down arrow keys or buttons
   - **Files**: Use Left/Right arrow keys or buttons

6. Processed files are saved with "_Pittsburgh_Observations.csv" suffix

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+S** | Save current rating |
| **Ctrl+0** | Set all ratings to 0 |
| **↑** | Previous row |
| **↓** | Next row |
| **←** | Previous CSV file |
| **→** | Next CSV file |

### Pittsburgh Agitation Scale Parameters

The tool rates observations on four dimensions:

#### 1. Aberrant Vocalization
- 0 - Not present
- 1 - Low volume  
- 2 - Louder than conversational
- 3 - Extremely loud
- 4 - Extremely loud with combativeness

#### 2. Motor Agitation
- 0 - Not present
- 1 - Pacing/aimless wandering
- 2 - Trying to get to different place
- 3 - Grabbing/clinging to people
- 4 - Pushing/shoving/pacing with combativeness

#### 3. Aggressiveness
- 0 - Not present
- 1 - Threatening verbal
- 2 - Threatening gestures
- 3 - Grabbing/pushing without injury
- 4 - Hitting/kicking/biting/scratching

#### 4. Resisting Care
- 0 - Not present
- 1 - Procrastination/avoidance
- 2 - Verbal/gesture refusal
- 3 - Pushing away to avoid task
- 4 - Hitting/kicking to avoid task

### Output Format

The tool adds five new columns to your CSV files:
- `Aberrant_Vocalization` (0-4)
- `Motor_Agitation` (0-4)
- `Aggressiveness` (0-4)
- `Resisting_Care` (0-4)
- `Duration_Seconds` (numeric)

### Project Structure

```
pittsburgh-observation-tool/
├── pittsburgh_tool.py      # Main application
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── setup.sh               # Optional setup script (Linux/Mac)
```

### Troubleshooting

#### "No module named '_tkinter'" Error
- **Windows**: Reinstall Python from python.org (includes tkinter)
- **macOS**: `brew install python-tk`
- **Linux**: `sudo apt-get install python3-tk`

#### CSV Files Not Found
- Ensure your CSV files end exactly with "Observations.csv"
- Check that files are in the selected folder or its subdirectories

#### Performance Issues
- For very large CSV files (>10,000 rows), consider splitting them
- Close other applications to free up memory

## Time Series Generator (PAS_Plotter.py)

### Overview

The `pittsburgh_timeseries_generator.py` script converts discrete Pittsburgh Agitation Scale observations into continuous time-series data with 1-second sampling rate. This tool is essential for temporal analysis and visualization of agitation patterns over extended observation periods.

### Purpose

While the main observation tool records discrete events with durations, many analyses require continuous time-series data. This script bridges that gap by:
- Creating second-by-second agitation scores
- Filling gaps between observations with zeros
- Generating comprehensive visualizations
- Enabling time-based statistical analysis


### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### License

This project is licensed under the MIT License - see the LICENSE file for details.

### Acknowledgments

- Based on the [Pittsburgh Agitation Scale](https://www.dementiaresearch.org.au/wp-content/uploads/2016/06/PAS-2.pdf)
- Developed for dementia research applications
- Built with Python and tkinter for cross-platform compatibility