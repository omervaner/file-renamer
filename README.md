# File Renamer

A powerful desktop application for bulk file renaming with multiple modes and smart features.

## Features

- **Pattern Rename**: Rename files with custom patterns (e.g., vacation_001, vacation_002)
- **Find & Replace**: Simple text replacement in filenames
- **Keep Original + Add Date**: Keep original filename and add creation date
- **Manual Selection**: Click to select/deselect specific files
- **File Type Filtering**: Filter by specific extensions (.jpg, .png, .pdf, etc.)
- **Sort Options**: Sort by name, date (oldest/newest first)
- **Custom Date Formats**: YYYYMMDD, YYYY-MM-DD, DDMMYYYY, etc.
- **Conflict Detection**: Warns before creating duplicate filenames
- **Undo**: One-click undo of last rename operation
- **Recent Folders**: Quick access to recently used folders
- **Drag & Drop**: Drag folders directly onto the app
- **Preview**: See changes before applying them

## Installation

### Requirements
- Python 3.9+
- tkinter (included with Python)
- tkinterdnd2

### Install Dependencies
```bash
pip install tkinterdnd2
```

## Usage

### Run from Source
```bash
python3 file_renamer_app.py
```

### Build as Mac App
```bash
pip install pyinstaller
pyinstaller --windowed --name "File Renamer" --onedir file_renamer_app.py
```

The `.app` file will be in the `dist` folder.

## How to Use

1. **Select a folder** using Browse or drag & drop
2. **Select files** by clicking on them (checkmark appears)
3. **Choose a rename mode**:
   - Pattern rename for sequential numbering
   - Find & Replace for text substitution
   - Keep original + date to add timestamps
4. **Configure options** (pattern, date format, sort order, etc.)
5. **Click "Preview Changes"** to see what will happen
6. **Click "Apply Rename"** to rename the files
7. **Use "Undo"** if you need to revert

## Development

Built with Python and tkinter for cross-platform compatibility.

Developed with assistance from [Claude Code](https://claude.com/claude-code).

## License

MIT License - feel free to use and modify!
