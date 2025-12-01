# File Tools v2.0

A powerful desktop application suite with 5 essential file management tools, all in one place.

## What's New in v2.0

- **4 New Tools**: Added Duplicate Finder, Folder Organizer, Image Resizer, and Operation Log
- **Image Previews**: See thumbnails when selecting image files in the renamer
- **Complete Logging**: All operations are tracked with timestamps and details
- **Enhanced UI**: Tabbed interface for easy navigation between tools

## Tools Included

### 1. File Renamer
- **Pattern Rename**: Rename files with custom patterns (e.g., vacation_001, vacation_002)
- **Find & Replace**: Simple text replacement in filenames
- **Manual Selection**: Click to select/deselect specific files
- **Image Preview**: See thumbnail previews of selected images
- **Undo**: One-click undo of last rename operation
- **Preview**: See changes before applying them

### 2. Duplicate Finder
- **Smart Detection**: Find duplicate files by content (MD5 hash)
- **Recursive Scanning**: Search subfolders automatically
- **File Details**: See file sizes and paths for all duplicates
- **Safe Deletion**: Select which copies to keep/delete
- **Group View**: Duplicates organized into groups

### 3. Folder Organizer
- **Auto-Organization**: Organize files into folders automatically
- **Three Modes**:
  - By File Type (Images, Documents, Music, Videos, etc.)
  - By Extension (.jpg, .pdf, .mp3, etc.)
  - By Date (YYYY-MM format)
- **Preview**: See organization plan before applying
- **Smart Naming**: Handles filename conflicts automatically

### 4. Image Resizer
- **Batch Processing**: Resize multiple images at once
- **Three Resize Modes**:
  - By Percentage (50%, 25%, etc.)
  - Fixed Dimensions (1920×1080)
  - Max Dimensions (fit within size, maintains aspect ratio)
- **Quality Control**: Adjustable JPEG quality (1-100%)
- **Format Conversion**: Convert between JPEG and PNG
- **Output Options**: Overwrite or save to different folder

### 5. Operation Log
- **Complete History**: Track all file operations with timestamps
- **Color-Coded**: Different colors for renames, deletions, organization, and resizing
- **Filtering**: View specific operation types
- **Persistent**: Logs saved between sessions (last 500 operations)

## Installation

### Requirements
- Python 3.9+
- tkinter (included with Python)
- tkinterdnd2

### Install Dependencies
```bash
pip install tkinterdnd2 Pillow
```

## Usage

### Run from Source
```bash
python3 file_tools_app.py
```

### Build as Mac App
```bash
pip install pyinstaller
pyinstaller --windowed --name "File Tools" --onedir file_tools_app.py
```

The `.app` file will be in the `dist` folder.

## How to Use

The app has 5 tabs for different tools:

### File Renamer Tab
1. Select a folder using Browse
2. Click on files to select them (checkmark appears)
3. See image previews in the side panel
4. Choose a rename mode (Pattern or Find & Replace)
5. Click "Preview Changes" to see what will happen
6. Click "Apply Rename" to rename the files
7. Use "Undo" if you need to revert

### Duplicate Finder Tab
1. Select a folder to scan
2. Choose whether to search subfolders recursively
3. Click "Scan for Duplicates"
4. Review duplicate groups
5. Click on files to select them for deletion
6. Click "Delete Selected" to remove duplicates

### Folder Organizer Tab
1. Select a folder with files to organize
2. Choose organization mode (Type, Extension, or Date)
3. Click "Preview Organization" to see the plan
4. Review which folders will be created
5. Click "Apply Organization" to organize files

### Image Resizer Tab
1. Select a folder with images
2. Choose an output folder (or keep same to overwrite)
3. Select resize mode (Percentage, Fixed, or Max Dimensions)
4. Adjust quality slider for JPEG compression
5. Choose output format (Keep Original, JPEG, or PNG)
6. Click "Resize Images" to process

### Operation Log Tab
- View all file operations with timestamps
- Filter by operation type (All, Renames, Deletions, Organization, Resize)
- Clear logs if needed

## Development

Built with Python and tkinter for cross-platform compatibility.

Developed with assistance from [Claude Code](https://claude.com/claude-code).

## License

MIT License - feel free to use and modify!
