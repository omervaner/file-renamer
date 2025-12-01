import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import json
from datetime import datetime
from pathlib import Path

# TODO: Add custom app icon here
# To set a custom icon, uncomment the line below in __init__ and replace 'icon.icns' with your icon file path
# self.root.iconbitmap('icon.icns')  # For Mac use .icns file

class FileRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulk File Renamer")
        self.root.geometry("900x700")

        # Store selected folder and files
        self.folder_path = ""
        self.files = []
        self.selected_files = set()
        self.last_rename_history = []  # For undo functionality

        # Recent folders tracking
        self.recent_folders_file = os.path.join(os.path.expanduser("~"), ".file_renamer_recent.json")
        self.recent_folders = self.load_recent_folders()

        # Create UI
        self.create_widgets()

        # Enable drag and drop for folder
        self.setup_drag_drop()

    def create_widgets(self):
        # Action buttons - PACK FIRST so they stick to bottom
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Button(button_frame, text="Preview Changes", command=self.preview_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Apply Rename", command=self.apply_rename).pack(side=tk.LEFT, padx=5)
        self.undo_button = ttk.Button(button_frame, text="Undo Last Rename", command=self.undo_rename, state="disabled")
        self.undo_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_all).pack(side=tk.RIGHT, padx=5)

        # Folder selection section
        folder_frame = ttk.Frame(self.root, padding="10")
        folder_frame.pack(fill=tk.X)

        ttk.Label(folder_frame, text="Select Folder (or drag & drop):").pack(side=tk.LEFT)
        self.folder_label = ttk.Label(folder_frame, text="No folder selected", foreground="gray")
        self.folder_label.pack(side=tk.LEFT, padx=10)

        # Recent folders dropdown
        if self.recent_folders:
            self.recent_var = tk.StringVar()
            recent_dropdown = ttk.Combobox(folder_frame, textvariable=self.recent_var,
                                          values=self.recent_folders, state="readonly", width=30)
            recent_dropdown.pack(side=tk.RIGHT, padx=5)
            recent_dropdown.bind("<<ComboboxSelected>>", self.load_recent_folder)
            ttk.Label(folder_frame, text="Recent:").pack(side=tk.RIGHT)

        ttk.Button(folder_frame, text="Browse", command=self.browse_folder).pack(side=tk.RIGHT)

        # Files display section
        files_frame = ttk.LabelFrame(self.root, text="Files Found (click to select/deselect)", padding="10")
        files_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)

        # Selection buttons
        select_button_frame = ttk.Frame(files_frame)
        select_button_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(select_button_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(select_button_frame, text="Deselect All", command=self.deselect_all).pack(side=tk.LEFT, padx=2)

        # Scrollable file list with checkboxes
        self.file_tree = ttk.Treeview(files_frame, columns=("Selected", "Type", "Name"), show="headings", height=8)
        self.file_tree.heading("Selected", text="✓")
        self.file_tree.heading("Type", text="Extension")
        self.file_tree.heading("Name", text="Current Name")
        self.file_tree.column("Selected", width=30, anchor="center")
        self.file_tree.column("Type", width=80)
        self.file_tree.column("Name", width=400)

        # Bind click event to toggle selection
        self.file_tree.bind("<Button-1>", self.toggle_file_selection)

        scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscroll=scrollbar.set)

        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Rename options section
        options_frame = ttk.LabelFrame(self.root, text="Rename Options", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=10)

        # Rename mode selection
        mode_frame = ttk.Frame(options_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        ttk.Label(mode_frame, text="Mode:").pack(side=tk.LEFT)
        self.rename_mode_var = tk.StringVar(value="pattern")
        ttk.Radiobutton(mode_frame, text="Pattern rename",
                       variable=self.rename_mode_var, value="pattern",
                       command=self.update_mode_ui).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="Keep original + date",
                       variable=self.rename_mode_var, value="date_only",
                       command=self.update_mode_ui).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="Find & Replace",
                       variable=self.rename_mode_var, value="find_replace",
                       command=self.update_mode_ui).pack(side=tk.LEFT)

        # Sort order selection
        sort_frame = ttk.Frame(options_frame)
        sort_frame.pack(fill=tk.X, pady=5)
        ttk.Label(sort_frame, text="Sort by:").pack(side=tk.LEFT)
        self.sort_var = tk.StringVar(value="name")
        ttk.Radiobutton(sort_frame, text="Name", variable=self.sort_var, value="name").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(sort_frame, text="Date (oldest first)", variable=self.sort_var, value="date_asc").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(sort_frame, text="Date (newest first)", variable=self.sort_var, value="date_desc").pack(side=tk.LEFT, padx=5)

        # Pattern input (only for pattern mode)
        self.pattern_frame = ttk.Frame(options_frame)
        self.pattern_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.pattern_frame, text="Pattern:").pack(side=tk.LEFT)
        self.pattern_var = tk.StringVar(value="file")
        ttk.Entry(self.pattern_frame, textvariable=self.pattern_var, width=30).pack(side=tk.LEFT, padx=10)
        ttk.Label(self.pattern_frame, text="(will add _001, _002, etc.)").pack(side=tk.LEFT)

        # Find & Replace inputs (only for find_replace mode)
        self.find_replace_frame = ttk.Frame(options_frame)
        self.find_replace_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.find_replace_frame, text="Find:").pack(side=tk.LEFT)
        self.find_var = tk.StringVar()
        ttk.Entry(self.find_replace_frame, textvariable=self.find_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Label(self.find_replace_frame, text="Replace with:").pack(side=tk.LEFT, padx=(10, 0))
        self.replace_var = tk.StringVar()
        ttk.Entry(self.find_replace_frame, textvariable=self.replace_var, width=20).pack(side=tk.LEFT, padx=5)
        # Hide by default
        self.find_replace_frame.pack_forget()

        # Date options
        self.date_frame = ttk.Frame(options_frame)
        self.date_frame.pack(fill=tk.X, pady=5)
        self.date_position_var = tk.StringVar(value="end")
        ttk.Label(self.date_frame, text="Date:").pack(side=tk.LEFT)

        # Date format dropdown
        self.date_format_var = tk.StringVar(value="YYYYMMDD")
        date_format_dropdown = ttk.Combobox(self.date_frame, textvariable=self.date_format_var,
                                           values=["YYYYMMDD", "YYYY-MM-DD", "DDMMYYYY", "DD-MM-YYYY", "MMDDYYYY"],
                                           state="readonly", width=12)
        date_format_dropdown.pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(self.date_frame, text="At end", variable=self.date_position_var, value="end").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(self.date_frame, text="At beginning", variable=self.date_position_var, value="start").pack(side=tk.LEFT)

        # File type filter (dropdown)
        filter_frame = ttk.Frame(options_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        ttk.Label(filter_frame, text="Show only:").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar(value="All Files")
        filter_dropdown = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                       values=["All Files", ".jpg", ".jpeg", ".png", ".gif", ".pdf",
                                              ".txt", ".doc", ".docx", ".mp4", ".mp3", ".heic", ".wav"],
                                       state="readonly", width=15)
        filter_dropdown.pack(side=tk.LEFT, padx=10)
        filter_dropdown.bind("<<ComboboxSelected>>", lambda e: self.apply_filter())

        # Preview section
        preview_frame = ttk.LabelFrame(self.root, text="Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.preview_tree = ttk.Treeview(preview_frame, columns=("Old", "New"), show="headings", height=6)
        self.preview_tree.heading("Old", text="Current Name")
        self.preview_tree.heading("New", text="New Name")
        self.preview_tree.column("Old", width=300)
        self.preview_tree.column("New", width=300)

        preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        self.preview_tree.configure(yscroll=preview_scrollbar.set)

        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_drag_drop(self):
        """Enable drag and drop for folder selection"""
        try:
            # Try to enable drag and drop (requires tkinterdnd2)
            self.folder_label.drop_target_register(DND_FILES)
            self.folder_label.dnd_bind('<<Drop>>', self.drop_folder)
        except:
            # tkinterdnd2 not installed, drag & drop won't work but app will still function
            pass

    def drop_folder(self, event):
        """Handle folder drop event"""
        folder = event.data.strip('{}')  # Remove curly braces from path
        if os.path.isdir(folder):
            self.folder_path = folder
            self.folder_label.config(text=folder, foreground="black")
            self.add_to_recent_folders(folder)
            self.load_files()

    def browse_folder(self):
        """Open folder browser dialog"""
        folder = filedialog.askdirectory(title="Select Folder to Rename Files")
        if folder:
            self.folder_path = folder
            self.folder_label.config(text=folder, foreground="black")
            self.add_to_recent_folders(folder)
            self.load_files()

    def load_files(self):
        """Load files from selected folder"""
        self.files = []
        self.selected_files = set()
        self.file_tree.delete(*self.file_tree.get_children())

        try:
            for filename in os.listdir(self.folder_path):
                file_path = os.path.join(self.folder_path, filename)

                # Skip hidden files and directories
                if filename.startswith('.') or os.path.isdir(file_path):
                    continue

                # Get file extension and creation time
                ext = Path(filename).suffix.lower()
                ctime = os.path.getctime(file_path)

                self.files.append({'name': filename, 'ext': ext, 'ctime': ctime})
                self.file_tree.insert("", tk.END, values=("", ext, filename))

        except Exception as e:
            messagebox.showerror("Error", f"Could not load files: {str(e)}")

    def toggle_file_selection(self, event):
        """Toggle file selection when clicked"""
        region = self.file_tree.identify("region", event.x, event.y)
        if region == "cell" or region == "tree":
            item = self.file_tree.identify_row(event.y)
            if item:
                values = self.file_tree.item(item, "values")
                filename = values[2]  # Name is in column 2

                if filename in self.selected_files:
                    self.selected_files.remove(filename)
                    self.file_tree.item(item, values=("", values[1], values[2]))
                else:
                    self.selected_files.add(filename)
                    self.file_tree.item(item, values=("✓", values[1], values[2]))

    def select_all(self):
        """Select all visible files"""
        for item in self.file_tree.get_children():
            values = self.file_tree.item(item, "values")
            filename = values[2]
            self.selected_files.add(filename)
            self.file_tree.item(item, values=("✓", values[1], values[2]))

    def deselect_all(self):
        """Deselect all files"""
        self.selected_files.clear()
        for item in self.file_tree.get_children():
            values = self.file_tree.item(item, "values")
            self.file_tree.item(item, values=("", values[1], values[2]))

    def apply_filter(self):
        """Filter displayed files by extension"""
        filter_ext = self.filter_var.get()
        self.file_tree.delete(*self.file_tree.get_children())

        for file_info in self.files:
            filename = file_info['name']
            ext = file_info['ext']

            # Apply filter
            if filter_ext == "All Files" or ext == filter_ext:
                is_selected = "✓" if filename in self.selected_files else ""
                self.file_tree.insert("", tk.END, values=(is_selected, ext, filename))

    def update_mode_ui(self):
        """Update UI based on rename mode"""
        mode = self.rename_mode_var.get()

        if mode == "pattern":
            # Show pattern frame, hide find/replace
            self.pattern_frame.pack(fill=tk.X, pady=5)
            self.find_replace_frame.pack_forget()
            for widget in self.pattern_frame.winfo_children():
                widget.configure(state="normal")
        elif mode == "find_replace":
            # Show find/replace frame, hide pattern
            self.find_replace_frame.pack(fill=tk.X, pady=5)
            self.pattern_frame.pack_forget()
        else:
            # date_only mode - hide both pattern and find/replace
            self.pattern_frame.pack_forget()
            self.find_replace_frame.pack_forget()

    def get_filtered_files(self):
        """Get only selected files and sort them"""
        selected = [f for f in self.files if f['name'] in self.selected_files]

        # Sort based on selected order
        sort_order = self.sort_var.get()
        if sort_order == "name":
            selected.sort(key=lambda x: x['name'].lower())
        elif sort_order == "date_asc":
            selected.sort(key=lambda x: x['ctime'])
        elif sort_order == "date_desc":
            selected.sort(key=lambda x: x['ctime'], reverse=True)

        return selected

    def format_date(self, timestamp):
        """Format date based on selected format"""
        date_obj = datetime.fromtimestamp(timestamp)
        format_type = self.date_format_var.get()

        if format_type == "YYYYMMDD":
            return date_obj.strftime("%Y%m%d")
        elif format_type == "YYYY-MM-DD":
            return date_obj.strftime("%Y-%m-%d")
        elif format_type == "DDMMYYYY":
            return date_obj.strftime("%d%m%Y")
        elif format_type == "DD-MM-YYYY":
            return date_obj.strftime("%d-%m-%Y")
        elif format_type == "MMDDYYYY":
            return date_obj.strftime("%m%d%Y")

        return date_obj.strftime("%Y%m%d")  # Default

    def generate_new_name(self, filename, index):
        """Generate new filename based on options"""
        mode = self.rename_mode_var.get()
        file_path = os.path.join(self.folder_path, filename)
        ext = Path(filename).suffix
        base_name_without_ext = Path(filename).stem

        # Get file creation date
        timestamp = os.path.getctime(file_path)
        date_str = self.format_date(timestamp)
        date_position = self.date_position_var.get()

        if mode == "date_only":
            # Keep original name and just add date
            if date_position == "start":
                new_name = f"{date_str}_{base_name_without_ext}{ext}"
            else:
                new_name = f"{base_name_without_ext}_{date_str}{ext}"
        elif mode == "find_replace":
            # Find and replace mode
            find_text = self.find_var.get()
            replace_text = self.replace_var.get()
            new_base_name = base_name_without_ext.replace(find_text, replace_text)
            new_name = f"{new_base_name}{ext}"
        else:
            # Pattern rename mode
            pattern = self.pattern_var.get()
            base_name = f"{pattern}_{str(index+1).zfill(3)}"

            # Add date if in pattern mode
            if date_position == "start":
                new_name = f"{date_str}_{base_name}{ext}"
            else:
                new_name = f"{base_name}_{date_str}{ext}"

        return new_name

    def check_conflicts(self, rename_map):
        """Check for naming conflicts"""
        new_names = [new_name for old_name, new_name in rename_map]

        # Check for duplicates in new names
        if len(new_names) != len(set(new_names)):
            duplicates = [name for name in new_names if new_names.count(name) > 1]
            return True, f"Conflict detected! These names would be duplicated: {', '.join(set(duplicates))}"

        # Check if any new name conflicts with existing files (that aren't being renamed)
        existing_files = set([f['name'] for f in self.files])
        files_being_renamed = set([old_name for old_name, new_name in rename_map])

        for old_name, new_name in rename_map:
            if new_name in existing_files and new_name not in files_being_renamed:
                return True, f"Conflict detected! '{new_name}' already exists in the folder."

        return False, ""

    def preview_changes(self):
        """Show preview of what files will be renamed to"""
        self.preview_tree.delete(*self.preview_tree.get_children())

        if not self.folder_path:
            messagebox.showwarning("Warning", "Please select a folder first")
            return

        filtered_files = self.get_filtered_files()

        if not filtered_files:
            messagebox.showinfo("Info", "No files selected. Please select files by clicking on them.")
            return

        rename_map = []
        for index, file_info in enumerate(filtered_files):
            old_name = file_info['name']
            new_name = self.generate_new_name(old_name, index)
            rename_map.append((old_name, new_name))
            self.preview_tree.insert("", tk.END, values=(old_name, new_name))

        # Check for conflicts
        has_conflict, conflict_msg = self.check_conflicts(rename_map)
        if has_conflict:
            messagebox.showwarning("Naming Conflict", conflict_msg)

    def apply_rename(self):
        """Actually rename the files"""
        if not self.folder_path:
            messagebox.showwarning("Warning", "Please select a folder first")
            return

        filtered_files = self.get_filtered_files()

        if not filtered_files:
            messagebox.showinfo("Info", "No files to rename")
            return

        # Build rename map
        rename_map = []
        for index, file_info in enumerate(filtered_files):
            old_name = file_info['name']
            new_name = self.generate_new_name(old_name, index)
            rename_map.append((old_name, new_name))

        # Check for conflicts
        has_conflict, conflict_msg = self.check_conflicts(rename_map)
        if has_conflict:
            messagebox.showerror("Cannot Rename", conflict_msg)
            return

        # Confirm with user
        result = messagebox.askyesno("Confirm",
            f"This will rename {len(filtered_files)} file(s). Continue?")

        if not result:
            return

        try:
            # Store history for undo
            self.last_rename_history = []

            renamed_count = 0
            for old_name, new_name in rename_map:
                old_path = os.path.join(self.folder_path, old_name)
                new_path = os.path.join(self.folder_path, new_name)

                # Rename the file
                os.rename(old_path, new_path)
                self.last_rename_history.append((new_name, old_name))  # Store reverse for undo
                renamed_count += 1

            messagebox.showinfo("Success", f"Successfully renamed {renamed_count} file(s)!")

            # Enable undo button
            self.undo_button.config(state="normal")

            # Reload files to show new names
            self.load_files()
            self.preview_tree.delete(*self.preview_tree.get_children())

        except Exception as e:
            messagebox.showerror("Error", f"Error renaming files: {str(e)}")

    def undo_rename(self):
        """Undo the last rename operation"""
        if not self.last_rename_history:
            messagebox.showinfo("Info", "Nothing to undo")
            return

        result = messagebox.askyesno("Confirm Undo",
            f"This will undo the last rename operation ({len(self.last_rename_history)} files). Continue?")

        if not result:
            return

        try:
            for current_name, original_name in self.last_rename_history:
                current_path = os.path.join(self.folder_path, current_name)
                original_path = os.path.join(self.folder_path, original_name)

                if os.path.exists(current_path):
                    os.rename(current_path, original_path)

            messagebox.showinfo("Success", "Undo completed successfully!")

            # Clear history and disable undo button
            self.last_rename_history = []
            self.undo_button.config(state="disabled")

            # Reload files
            self.load_files()

        except Exception as e:
            messagebox.showerror("Error", f"Error during undo: {str(e)}")

    def load_recent_folders(self):
        """Load recent folders from file"""
        try:
            if os.path.exists(self.recent_folders_file):
                with open(self.recent_folders_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []

    def save_recent_folders(self):
        """Save recent folders to file"""
        try:
            with open(self.recent_folders_file, 'w') as f:
                json.dump(self.recent_folders, f)
        except:
            pass

    def add_to_recent_folders(self, folder_path):
        """Add folder to recent folders list"""
        # Remove if already in list
        if folder_path in self.recent_folders:
            self.recent_folders.remove(folder_path)

        # Add to beginning
        self.recent_folders.insert(0, folder_path)

        # Keep only last 5
        self.recent_folders = self.recent_folders[:5]

        # Save to file
        self.save_recent_folders()

    def load_recent_folder(self, event):
        """Load a folder from recent folders dropdown"""
        folder = self.recent_var.get()
        if folder and os.path.isdir(folder):
            self.folder_path = folder
            self.folder_label.config(text=folder, foreground="black")
            self.add_to_recent_folders(folder)
            self.load_files()

    def clear_all(self):
        """Clear all selections and previews"""
        self.folder_path = ""
        self.folder_label.config(text="No folder selected", foreground="gray")
        self.files = []
        self.selected_files.clear()
        self.file_tree.delete(*self.file_tree.get_children())
        self.preview_tree.delete(*self.preview_tree.get_children())
        self.pattern_var.set("file")
        self.rename_mode_var.set("pattern")
        self.filter_var.set("All Files")
        self.sort_var.set("name")
        self.date_format_var.set("YYYYMMDD")

# Run the app
if __name__ == "__main__":
    try:
        # Try to use TkinterDnD for drag and drop support
        root = TkinterDnD.Tk()
    except:
        # Fall back to regular Tk if tkinterdnd2 not installed
        root = tk.Tk()

    app = FileRenamerApp(root)
    root.mainloop()
