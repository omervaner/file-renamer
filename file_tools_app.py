import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from PIL import Image, ImageTk

class FileToolsApp:
    VERSION = "2.0"

    def __init__(self, root):
        self.root = root
        self.root.title(f"File Tools v{self.VERSION}")
        self.root.geometry("950x750")

        # Initialize logging
        self.log_file = os.path.join(os.path.expanduser("~"), ".file_tools_log.json")
        self.logs = self.load_logs()

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.renamer_tab = ttk.Frame(self.notebook)
        self.duplicate_tab = ttk.Frame(self.notebook)
        self.organizer_tab = ttk.Frame(self.notebook)
        self.resizer_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.renamer_tab, text="File Renamer")
        self.notebook.add(self.duplicate_tab, text="Duplicate Finder")
        self.notebook.add(self.organizer_tab, text="Folder Organizer")
        self.notebook.add(self.resizer_tab, text="Image Resizer")
        self.notebook.add(self.log_tab, text="Operation Log")

        # Initialize all tools
        self.init_file_renamer()
        self.init_duplicate_finder()
        self.init_folder_organizer()
        self.init_image_resizer()
        self.init_log_viewer()

    # ========== FILE RENAMER TAB ==========
    def init_file_renamer(self):
        # Store selected folder and files
        self.renamer_folder_path = ""
        self.renamer_files = []
        self.renamer_selected_files = set()
        self.last_rename_history = []

        # Recent folders tracking
        self.recent_folders_file = os.path.join(os.path.expanduser("~"), ".file_renamer_recent.json")
        self.recent_folders = self.load_recent_folders()

        # Create renamer UI
        self.create_renamer_widgets()

    def create_renamer_widgets(self):
        # Action buttons - PACK FIRST so they stick to bottom
        button_frame = ttk.Frame(self.renamer_tab, padding="10")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Button(button_frame, text="Preview Changes", command=self.preview_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Apply Rename", command=self.apply_rename).pack(side=tk.LEFT, padx=5)
        self.undo_button = ttk.Button(button_frame, text="Undo Last Rename", command=self.undo_rename, state="disabled")
        self.undo_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_renamer).pack(side=tk.RIGHT, padx=5)

        # Folder selection section
        folder_frame = ttk.Frame(self.renamer_tab, padding="10")
        folder_frame.pack(fill=tk.X)

        ttk.Label(folder_frame, text="Select Folder:").pack(side=tk.LEFT)
        self.renamer_folder_label = ttk.Label(folder_frame, text="No folder selected", foreground="gray")
        self.renamer_folder_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(folder_frame, text="Browse", command=self.browse_renamer_folder).pack(side=tk.RIGHT)

        # Main content area with image preview on the right
        content_frame = ttk.Frame(self.renamer_tab)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left side: Files list
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Files display section
        files_frame = ttk.LabelFrame(left_frame, text="Files Found (click to select/deselect)", padding="10")
        files_frame.pack(fill=tk.BOTH, expand=True)

        # Selection buttons
        select_button_frame = ttk.Frame(files_frame)
        select_button_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(select_button_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(select_button_frame, text="Deselect All", command=self.deselect_all).pack(side=tk.LEFT, padx=2)

        # Scrollable file list
        self.file_tree = ttk.Treeview(files_frame, columns=("Selected", "Type", "Name"), show="headings", height=6)
        self.file_tree.heading("Selected", text="✓")
        self.file_tree.heading("Type", text="Extension")
        self.file_tree.heading("Name", text="Current Name")
        self.file_tree.column("Selected", width=30, anchor="center")
        self.file_tree.column("Type", width=80)
        self.file_tree.column("Name", width=300)
        self.file_tree.bind("<Button-1>", self.toggle_file_selection)
        self.file_tree.bind("<<TreeviewSelect>>", self.on_file_selected)

        scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscroll=scrollbar.set)
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Right side: Image preview panel
        preview_panel = ttk.LabelFrame(content_frame, text="Image Preview", padding="10")
        preview_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))

        self.image_preview_label = ttk.Label(preview_panel, text="Select an image file\nto see preview",
                                             foreground="gray", anchor="center")
        self.image_preview_label.pack(expand=True, fill=tk.BOTH)

        # Store reference to prevent garbage collection
        self.current_preview_image = None

        # Rename options section
        options_frame = ttk.LabelFrame(left_frame, text="Rename Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(10, 0))

        # Rename mode selection
        mode_frame = ttk.Frame(options_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        ttk.Label(mode_frame, text="Mode:").pack(side=tk.LEFT)
        self.rename_mode_var = tk.StringVar(value="pattern")
        ttk.Radiobutton(mode_frame, text="Pattern rename", variable=self.rename_mode_var, value="pattern", command=self.update_mode_ui).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="Find & Replace", variable=self.rename_mode_var, value="find_replace", command=self.update_mode_ui).pack(side=tk.LEFT, padx=10)

        # Pattern input
        self.pattern_frame = ttk.Frame(options_frame)
        self.pattern_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.pattern_frame, text="Pattern:").pack(side=tk.LEFT)
        self.pattern_var = tk.StringVar(value="file")
        ttk.Entry(self.pattern_frame, textvariable=self.pattern_var, width=30).pack(side=tk.LEFT, padx=10)
        ttk.Label(self.pattern_frame, text="(will add _001, _002, etc.)").pack(side=tk.LEFT)

        # Find & Replace inputs
        self.find_replace_frame = ttk.Frame(options_frame)
        self.find_replace_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.find_replace_frame, text="Find:").pack(side=tk.LEFT)
        self.find_var = tk.StringVar()
        ttk.Entry(self.find_replace_frame, textvariable=self.find_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Label(self.find_replace_frame, text="Replace with:").pack(side=tk.LEFT, padx=(10, 0))
        self.replace_var = tk.StringVar()
        ttk.Entry(self.find_replace_frame, textvariable=self.replace_var, width=20).pack(side=tk.LEFT, padx=5)
        self.find_replace_frame.pack_forget()

        # Preview section
        preview_frame = ttk.LabelFrame(left_frame, text="Rename Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.preview_tree = ttk.Treeview(preview_frame, columns=("Old", "New"), show="headings", height=4)
        self.preview_tree.heading("Old", text="Current Name")
        self.preview_tree.heading("New", text="New Name")
        self.preview_tree.column("Old", width=200)
        self.preview_tree.column("New", width=200)

        preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        self.preview_tree.configure(yscroll=preview_scrollbar.set)
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # ========== DUPLICATE FINDER TAB ==========
    def init_duplicate_finder(self):
        self.duplicate_folder_path = ""
        self.duplicates = {}  # {hash: [file_paths]}
        self.selected_for_deletion = set()

        self.create_duplicate_finder_widgets()

    def create_duplicate_finder_widgets(self):
        # Action buttons at bottom
        button_frame = ttk.Frame(self.duplicate_tab, padding="10")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Button(button_frame, text="Scan for Duplicates", command=self.scan_duplicates).pack(side=tk.LEFT, padx=5)
        self.delete_duplicates_btn = ttk.Button(button_frame, text="Delete Selected", command=self.delete_duplicates, state="disabled")
        self.delete_duplicates_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_duplicates).pack(side=tk.RIGHT, padx=5)

        # Folder selection
        folder_frame = ttk.Frame(self.duplicate_tab, padding="10")
        folder_frame.pack(fill=tk.X)

        ttk.Label(folder_frame, text="Select Folder:").pack(side=tk.LEFT)
        self.duplicate_folder_label = ttk.Label(folder_frame, text="No folder selected", foreground="gray")
        self.duplicate_folder_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(folder_frame, text="Browse", command=self.browse_duplicate_folder).pack(side=tk.RIGHT)

        # Options
        options_frame = ttk.Frame(self.duplicate_tab, padding="10")
        options_frame.pack(fill=tk.X)

        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Search subfolders recursively", variable=self.recursive_var).pack(side=tk.LEFT)

        # Status label
        self.scan_status_label = ttk.Label(self.duplicate_tab, text="", foreground="gray")
        self.scan_status_label.pack(pady=5)

        # Results display
        results_frame = ttk.LabelFrame(self.duplicate_tab, text="Duplicate Files Found", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tree view for duplicates
        self.duplicate_tree = ttk.Treeview(results_frame, columns=("Select", "Path", "Size"), show="tree headings", height=15)
        self.duplicate_tree.heading("#0", text="Filename")
        self.duplicate_tree.heading("Select", text="Delete?")
        self.duplicate_tree.heading("Path", text="Path")
        self.duplicate_tree.heading("Size", text="Size")
        self.duplicate_tree.column("#0", width=250)
        self.duplicate_tree.column("Select", width=60, anchor="center")
        self.duplicate_tree.column("Path", width=400)
        self.duplicate_tree.column("Size", width=100)
        self.duplicate_tree.bind("<Button-1>", self.toggle_duplicate_selection)

        dup_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.duplicate_tree.yview)
        self.duplicate_tree.configure(yscroll=dup_scrollbar.set)
        self.duplicate_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        dup_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # ========== FILE RENAMER METHODS ==========
    def browse_renamer_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Rename Files")
        if folder:
            self.renamer_folder_path = folder
            self.renamer_folder_label.config(text=folder, foreground="black")
            self.load_renamer_files()

    def load_renamer_files(self):
        self.renamer_files = []
        self.renamer_selected_files = set()
        self.file_tree.delete(*self.file_tree.get_children())

        try:
            for filename in sorted(os.listdir(self.renamer_folder_path)):
                file_path = os.path.join(self.renamer_folder_path, filename)
                if os.path.isfile(file_path) and not filename.startswith('.'):
                    file_stat = os.stat(file_path)
                    self.renamer_files.append({
                        'name': filename,
                        'path': file_path,
                        'created': file_stat.st_birthtime
                    })

            for file_info in self.renamer_files:
                filename = file_info['name']
                ext = os.path.splitext(filename)[1]
                self.file_tree.insert("", tk.END, values=("", ext, filename))
        except Exception as e:
            messagebox.showerror("Error", f"Error loading files: {str(e)}")

    def toggle_file_selection(self, event):
        item = self.file_tree.identify_row(event.y)
        if item:
            values = self.file_tree.item(item, "values")
            filename = values[2]

            if filename in self.renamer_selected_files:
                self.renamer_selected_files.remove(filename)
                self.file_tree.item(item, values=("", values[1], values[2]))
            else:
                self.renamer_selected_files.add(filename)
                self.file_tree.item(item, values=("✓", values[1], values[2]))

    def select_all(self):
        for item in self.file_tree.get_children():
            values = self.file_tree.item(item, "values")
            filename = values[2]
            self.renamer_selected_files.add(filename)
            self.file_tree.item(item, values=("✓", values[1], values[2]))

    def deselect_all(self):
        self.renamer_selected_files.clear()
        for item in self.file_tree.get_children():
            values = self.file_tree.item(item, "values")
            self.file_tree.item(item, values=("", values[1], values[2]))

    def on_file_selected(self, event):
        """Handle file selection and show image preview"""
        selection = self.file_tree.selection()
        if selection:
            item = selection[0]
            values = self.file_tree.item(item, "values")
            filename = values[2]
            file_path = os.path.join(self.renamer_folder_path, filename)

            # Check if it's an image file
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.ico', '.tiff', '.heic'}
            ext = os.path.splitext(filename)[1].lower()

            if ext in image_extensions:
                self.show_image_preview(file_path)
            else:
                self.clear_image_preview()
        else:
            self.clear_image_preview()

    def show_image_preview(self, image_path):
        """Display image thumbnail in preview panel"""
        try:
            # Open and resize image
            img = Image.open(image_path)

            # Get dimensions for thumbnail (max 250x250)
            max_size = (250, 250)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)

            # Update label
            self.image_preview_label.config(image=photo, text="")
            self.current_preview_image = photo  # Keep reference

        except Exception as e:
            self.image_preview_label.config(
                image="",
                text=f"Could not load image:\n{str(e)[:50]}",
                foreground="red"
            )
            self.current_preview_image = None

    def clear_image_preview(self):
        """Clear the image preview"""
        self.image_preview_label.config(
            image="",
            text="Select an image file\nto see preview",
            foreground="gray"
        )
        self.current_preview_image = None

    def update_mode_ui(self):
        mode = self.rename_mode_var.get()
        if mode == "pattern":
            self.pattern_frame.pack(fill=tk.X, pady=5)
            self.find_replace_frame.pack_forget()
        elif mode == "find_replace":
            self.find_replace_frame.pack(fill=tk.X, pady=5)
            self.pattern_frame.pack_forget()

    def preview_changes(self):
        self.preview_tree.delete(*self.preview_tree.get_children())

        if not self.renamer_selected_files:
            messagebox.showwarning("No Files Selected", "Please select files to rename")
            return

        selected = [f for f in self.renamer_files if f['name'] in self.renamer_selected_files]
        mode = self.rename_mode_var.get()

        for index, file_info in enumerate(selected):
            old_name = file_info['name']
            base_name, ext = os.path.splitext(old_name)

            if mode == "find_replace":
                find_text = self.find_var.get()
                replace_text = self.replace_var.get()
                new_base_name = base_name.replace(find_text, replace_text)
                new_name = f"{new_base_name}{ext}"
            else:  # pattern mode
                pattern = self.pattern_var.get()
                new_name = f"{pattern}_{str(index+1).zfill(3)}{ext}"

            self.preview_tree.insert("", tk.END, values=(old_name, new_name))

    def apply_rename(self):
        if not self.renamer_selected_files:
            messagebox.showwarning("No Files Selected", "Please select files to rename")
            return

        # Check for conflicts
        preview_items = self.preview_tree.get_children()
        if not preview_items:
            messagebox.showwarning("No Preview", "Please preview changes first")
            return

        new_names = [self.preview_tree.item(item)["values"][1] for item in preview_items]
        if len(new_names) != len(set(new_names)):
            messagebox.showerror("Conflict", "Some files would have duplicate names!")
            return

        # Perform rename
        self.last_rename_history = []
        try:
            for item in preview_items:
                values = self.preview_tree.item(item)["values"]
                old_name, new_name = values[0], values[1]
                old_path = os.path.join(self.renamer_folder_path, old_name)
                new_path = os.path.join(self.renamer_folder_path, new_name)

                os.rename(old_path, new_path)
                self.last_rename_history.append((new_path, old_path))

                # Log the rename
                self.add_log("rename", f"'{old_name}' → '{new_name}'")

            messagebox.showinfo("Success", f"Renamed {len(preview_items)} files")
            self.undo_button.config(state="normal")
            self.load_renamer_files()
            self.preview_tree.delete(*self.preview_tree.get_children())
        except Exception as e:
            messagebox.showerror("Error", f"Error renaming files: {str(e)}")

    def undo_rename(self):
        if not self.last_rename_history:
            return

        try:
            for new_path, old_path in self.last_rename_history:
                os.rename(new_path, old_path)

            messagebox.showinfo("Undo", "Rename operation undone")
            self.undo_button.config(state="disabled")
            self.load_renamer_files()
        except Exception as e:
            messagebox.showerror("Error", f"Error during undo: {str(e)}")

    def clear_renamer(self):
        self.renamer_folder_path = ""
        self.renamer_folder_label.config(text="No folder selected", foreground="gray")
        self.renamer_files = []
        self.renamer_selected_files.clear()
        self.file_tree.delete(*self.file_tree.get_children())
        self.preview_tree.delete(*self.preview_tree.get_children())

    def load_recent_folders(self):
        try:
            if os.path.exists(self.recent_folders_file):
                with open(self.recent_folders_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []

    # ========== DUPLICATE FINDER METHODS ==========
    def browse_duplicate_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Scan for Duplicates")
        if folder:
            self.duplicate_folder_path = folder
            self.duplicate_folder_label.config(text=folder, foreground="black")

    def scan_duplicates(self):
        if not self.duplicate_folder_path:
            messagebox.showwarning("No Folder", "Please select a folder to scan")
            return

        self.duplicate_tree.delete(*self.duplicate_tree.get_children())
        self.duplicates = {}
        self.selected_for_deletion = set()
        self.scan_status_label.config(text="Scanning...")
        self.root.update()

        # Hash all files
        file_hashes = defaultdict(list)
        file_count = 0

        try:
            if self.recursive_var.get():
                # Recursive scan
                for root, dirs, files in os.walk(self.duplicate_folder_path):
                    for filename in files:
                        if not filename.startswith('.'):
                            file_path = os.path.join(root, filename)
                            file_hash = self.hash_file(file_path)
                            if file_hash:
                                file_hashes[file_hash].append(file_path)
                                file_count += 1
            else:
                # Non-recursive scan
                for filename in os.listdir(self.duplicate_folder_path):
                    file_path = os.path.join(self.duplicate_folder_path, filename)
                    if os.path.isfile(file_path) and not filename.startswith('.'):
                        file_hash = self.hash_file(file_path)
                        if file_hash:
                            file_hashes[file_hash].append(file_path)
                            file_count += 1

            # Find duplicates (hashes with multiple files)
            self.duplicates = {h: paths for h, paths in file_hashes.items() if len(paths) > 1}

            # Display results
            if self.duplicates:
                for file_hash, paths in self.duplicates.items():
                    # Create parent node for this duplicate group
                    parent = self.duplicate_tree.insert("", tk.END, text=f"Duplicate Group ({len(paths)} copies)", values=("", "", ""))

                    for path in paths:
                        filename = os.path.basename(path)
                        size = os.path.getsize(path)
                        size_str = self.format_size(size)
                        self.duplicate_tree.insert(parent, tk.END, text=filename, values=("", path, size_str))

                total_duplicates = sum(len(paths) - 1 for paths in self.duplicates.values())
                self.scan_status_label.config(text=f"Found {len(self.duplicates)} duplicate groups ({total_duplicates} duplicate files)")
            else:
                self.scan_status_label.config(text=f"No duplicates found (scanned {file_count} files)")

        except Exception as e:
            messagebox.showerror("Error", f"Error scanning for duplicates: {str(e)}")
            self.scan_status_label.config(text="Error during scan")

    def hash_file(self, file_path):
        """Calculate MD5 hash of file"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return None

    def format_size(self, size_bytes):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def toggle_duplicate_selection(self, event):
        item = self.duplicate_tree.identify_row(event.y)
        if item:
            # Only allow selection of child items (actual files), not parent groups
            parent = self.duplicate_tree.parent(item)
            if parent:  # This is a file item, not a group
                values = list(self.duplicate_tree.item(item, "values"))
                file_path = values[1]

                if file_path in self.selected_for_deletion:
                    self.selected_for_deletion.remove(file_path)
                    values[0] = ""
                else:
                    self.selected_for_deletion.add(file_path)
                    values[0] = "✓"

                self.duplicate_tree.item(item, values=values)
                self.delete_duplicates_btn.config(state="normal" if self.selected_for_deletion else "disabled")

    def delete_duplicates(self):
        if not self.selected_for_deletion:
            return

        response = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete {len(self.selected_for_deletion)} files?\nThis cannot be undone!"
        )

        if response:
            deleted_count = 0
            try:
                for file_path in self.selected_for_deletion:
                    os.remove(file_path)
                    deleted_count += 1

                    # Log the deletion
                    self.add_log("delete", f"Deleted duplicate: {file_path}")

                messagebox.showinfo("Success", f"Deleted {deleted_count} files")
                self.scan_duplicates()  # Rescan
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting files: {str(e)}")

    def clear_duplicates(self):
        self.duplicate_folder_path = ""
        self.duplicate_folder_label.config(text="No folder selected", foreground="gray")
        self.duplicates = {}
        self.selected_for_deletion = set()
        self.duplicate_tree.delete(*self.duplicate_tree.get_children())
        self.scan_status_label.config(text="")
        self.delete_duplicates_btn.config(state="disabled")

    # ========== FOLDER ORGANIZER TAB ==========
    def init_folder_organizer(self):
        self.organizer_folder_path = ""
        self.organizer_files = []
        self.organize_plan = {}  # {folder_name: [file_paths]}
        self.create_organizer_widgets()

    def create_organizer_widgets(self):
        # Action buttons at bottom
        button_frame = ttk.Frame(self.organizer_tab, padding="10")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Button(button_frame, text="Preview Organization", command=self.preview_organization).pack(side=tk.LEFT, padx=5)
        self.organize_btn = ttk.Button(button_frame, text="Apply Organization", command=self.apply_organization, state="disabled")
        self.organize_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_organizer).pack(side=tk.RIGHT, padx=5)

        # Folder selection
        folder_frame = ttk.Frame(self.organizer_tab, padding="10")
        folder_frame.pack(fill=tk.X)

        ttk.Label(folder_frame, text="Select Folder to Organize:").pack(side=tk.LEFT)
        self.organizer_folder_label = ttk.Label(folder_frame, text="No folder selected", foreground="gray")
        self.organizer_folder_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(folder_frame, text="Browse", command=self.browse_organizer_folder).pack(side=tk.RIGHT)

        # Organization mode options
        options_frame = ttk.LabelFrame(self.organizer_tab, text="Organize By", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=10)

        self.organize_mode_var = tk.StringVar(value="type")
        ttk.Radiobutton(options_frame, text="File Type (Images, Documents, Music, etc.)",
                       variable=self.organize_mode_var, value="type").pack(anchor=tk.W, pady=3)
        ttk.Radiobutton(options_frame, text="Extension (.jpg, .pdf, .mp3, etc.)",
                       variable=self.organize_mode_var, value="extension").pack(anchor=tk.W, pady=3)
        ttk.Radiobutton(options_frame, text="Date (YYYY-MM format)",
                       variable=self.organize_mode_var, value="date").pack(anchor=tk.W, pady=3)

        # Status label
        self.organize_status_label = ttk.Label(self.organizer_tab, text="", foreground="gray")
        self.organize_status_label.pack(pady=5)

        # Preview display
        preview_frame = ttk.LabelFrame(self.organizer_tab, text="Organization Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tree view for preview
        self.organize_tree = ttk.Treeview(preview_frame, columns=("Files", "Destination"), show="tree headings", height=15)
        self.organize_tree.heading("#0", text="Folder Name")
        self.organize_tree.heading("Files", text="File Count")
        self.organize_tree.heading("Destination", text="Path")
        self.organize_tree.column("#0", width=200)
        self.organize_tree.column("Files", width=100)
        self.organize_tree.column("Destination", width=500)

        org_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.organize_tree.yview)
        self.organize_tree.configure(yscroll=org_scrollbar.set)
        self.organize_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        org_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def browse_organizer_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Organize")
        if folder:
            self.organizer_folder_path = folder
            self.organizer_folder_label.config(text=folder, foreground="black")
            self.load_organizer_files()

    def load_organizer_files(self):
        self.organizer_files = []
        try:
            for filename in os.listdir(self.organizer_folder_path):
                file_path = os.path.join(self.organizer_folder_path, filename)
                if os.path.isfile(file_path) and not filename.startswith('.'):
                    self.organizer_files.append(file_path)

            self.organize_status_label.config(text=f"Loaded {len(self.organizer_files)} files")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading files: {str(e)}")

    def get_file_category(self, extension):
        """Categorize file by extension into broad categories"""
        ext = extension.lower()

        images = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff', '.heic'}
        documents = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages', '.md', '.tex'}
        spreadsheets = {'.xls', '.xlsx', '.csv', '.numbers', '.ods'}
        presentations = {'.ppt', '.pptx', '.key', '.odp'}
        videos = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm', '.m4v'}
        music = {'.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg', '.wma'}
        archives = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.dmg', '.iso'}
        code = {'.py', '.js', '.java', '.cpp', '.c', '.h', '.html', '.css', '.php', '.rb', '.swift', '.go'}

        if ext in images:
            return "Images"
        elif ext in documents:
            return "Documents"
        elif ext in spreadsheets:
            return "Spreadsheets"
        elif ext in presentations:
            return "Presentations"
        elif ext in videos:
            return "Videos"
        elif ext in music:
            return "Music"
        elif ext in archives:
            return "Archives"
        elif ext in code:
            return "Code"
        else:
            return "Other"

    def preview_organization(self):
        if not self.organizer_files:
            messagebox.showwarning("No Files", "Please select a folder with files to organize")
            return

        self.organize_tree.delete(*self.organize_tree.get_children())
        self.organize_plan = defaultdict(list)
        mode = self.organize_mode_var.get()

        try:
            for file_path in self.organizer_files:
                filename = os.path.basename(file_path)
                ext = os.path.splitext(filename)[1]

                if mode == "type":
                    folder_name = self.get_file_category(ext)
                elif mode == "extension":
                    folder_name = ext[1:] if ext else "no_extension"
                else:  # date
                    file_date = datetime.fromtimestamp(os.path.getmtime(file_path))
                    folder_name = file_date.strftime("%Y-%m")

                self.organize_plan[folder_name].append(file_path)

            # Display preview
            for folder_name in sorted(self.organize_plan.keys()):
                files = self.organize_plan[folder_name]
                dest_path = os.path.join(self.organizer_folder_path, folder_name)
                parent = self.organize_tree.insert("", tk.END, text=folder_name,
                                                   values=(f"{len(files)} files", dest_path))

                # Add files as children
                for file_path in files[:10]:  # Show first 10 files
                    filename = os.path.basename(file_path)
                    self.organize_tree.insert(parent, tk.END, text=f"  {filename}", values=("", ""))

                if len(files) > 10:
                    self.organize_tree.insert(parent, tk.END, text=f"  ... and {len(files)-10} more",
                                            values=("", ""))

            self.organize_status_label.config(
                text=f"Will create {len(self.organize_plan)} folders and organize {len(self.organizer_files)} files"
            )
            self.organize_btn.config(state="normal")

        except Exception as e:
            messagebox.showerror("Error", f"Error previewing organization: {str(e)}")

    def apply_organization(self):
        if not self.organize_plan:
            return

        response = messagebox.askyesno(
            "Confirm Organization",
            f"This will create {len(self.organize_plan)} folders and move {len(self.organizer_files)} files.\nContinue?"
        )

        if not response:
            return

        try:
            moved_count = 0
            for folder_name, files in self.organize_plan.items():
                # Create folder if it doesn't exist
                folder_path = os.path.join(self.organizer_folder_path, folder_name)
                os.makedirs(folder_path, exist_ok=True)

                # Move files
                for file_path in files:
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(folder_path, filename)

                    # Handle duplicate filenames
                    if os.path.exists(dest_path):
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(dest_path):
                            dest_path = os.path.join(folder_path, f"{base}_{counter}{ext}")
                            counter += 1

                    os.rename(file_path, dest_path)
                    moved_count += 1

                    # Log the organization
                    self.add_log("organize", f"Moved '{filename}' → '{folder_name}/' folder")

            messagebox.showinfo("Success", f"Organized {moved_count} files into {len(self.organize_plan)} folders")
            self.clear_organizer()

        except Exception as e:
            messagebox.showerror("Error", f"Error during organization: {str(e)}")

    def clear_organizer(self):
        self.organizer_folder_path = ""
        self.organizer_folder_label.config(text="No folder selected", foreground="gray")
        self.organizer_files = []
        self.organize_plan = {}
        self.organize_tree.delete(*self.organize_tree.get_children())
        self.organize_status_label.config(text="")
        self.organize_btn.config(state="disabled")

    # ========== IMAGE RESIZER TAB ==========
    def init_image_resizer(self):
        self.resizer_folder_path = ""
        self.resizer_output_folder = ""
        self.resizer_images = []
        self.create_resizer_widgets()

    def create_resizer_widgets(self):
        # Action buttons at bottom
        button_frame = ttk.Frame(self.resizer_tab, padding="10")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.resize_btn = ttk.Button(button_frame, text="Resize Images", command=self.apply_resize, state="disabled")
        self.resize_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_resizer).pack(side=tk.RIGHT, padx=5)

        # Input folder selection
        input_frame = ttk.Frame(self.resizer_tab, padding="10")
        input_frame.pack(fill=tk.X)

        ttk.Label(input_frame, text="Input Folder:").pack(side=tk.LEFT)
        self.resizer_folder_label = ttk.Label(input_frame, text="No folder selected", foreground="gray")
        self.resizer_folder_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(input_frame, text="Browse", command=self.browse_resizer_folder).pack(side=tk.RIGHT)

        # Output folder selection
        output_frame = ttk.Frame(self.resizer_tab, padding="10")
        output_frame.pack(fill=tk.X)

        ttk.Label(output_frame, text="Output Folder:").pack(side=tk.LEFT)
        self.resizer_output_label = ttk.Label(output_frame, text="Same as input (will overwrite)", foreground="gray")
        self.resizer_output_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(output_frame, text="Choose Different", command=self.browse_output_folder).pack(side=tk.RIGHT)

        # Resize options
        options_frame = ttk.LabelFrame(self.resizer_tab, text="Resize Options", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=10)

        # Resize mode
        mode_frame = ttk.Frame(options_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        ttk.Label(mode_frame, text="Resize Mode:").pack(side=tk.LEFT)
        self.resize_mode_var = tk.StringVar(value="percentage")
        ttk.Radiobutton(mode_frame, text="By Percentage", variable=self.resize_mode_var,
                       value="percentage", command=self.update_resize_ui).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="Fixed Dimensions", variable=self.resize_mode_var,
                       value="fixed", command=self.update_resize_ui).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="Max Dimensions (fit)", variable=self.resize_mode_var,
                       value="max", command=self.update_resize_ui).pack(side=tk.LEFT, padx=10)

        # Percentage input
        self.percentage_frame = ttk.Frame(options_frame)
        self.percentage_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.percentage_frame, text="Scale:").pack(side=tk.LEFT)
        self.percentage_var = tk.StringVar(value="50")
        ttk.Entry(self.percentage_frame, textvariable=self.percentage_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(self.percentage_frame, text="%").pack(side=tk.LEFT)

        # Fixed dimensions input
        self.fixed_frame = ttk.Frame(options_frame)
        ttk.Label(self.fixed_frame, text="Width:").pack(side=tk.LEFT)
        self.width_var = tk.StringVar(value="1920")
        ttk.Entry(self.fixed_frame, textvariable=self.width_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(self.fixed_frame, text="Height:").pack(side=tk.LEFT, padx=(10, 0))
        self.height_var = tk.StringVar(value="1080")
        ttk.Entry(self.fixed_frame, textvariable=self.height_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(self.fixed_frame, text="px").pack(side=tk.LEFT)
        self.fixed_frame.pack_forget()

        # Max dimensions input
        self.max_frame = ttk.Frame(options_frame)
        ttk.Label(self.max_frame, text="Max Width:").pack(side=tk.LEFT)
        self.max_width_var = tk.StringVar(value="1920")
        ttk.Entry(self.max_frame, textvariable=self.max_width_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(self.max_frame, text="Max Height:").pack(side=tk.LEFT, padx=(10, 0))
        self.max_height_var = tk.StringVar(value="1080")
        ttk.Entry(self.max_frame, textvariable=self.max_height_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(self.max_frame, text="(maintains aspect ratio)").pack(side=tk.LEFT, padx=5)
        self.max_frame.pack_forget()

        # Quality setting
        quality_frame = ttk.Frame(options_frame)
        quality_frame.pack(fill=tk.X, pady=5)
        ttk.Label(quality_frame, text="Quality:").pack(side=tk.LEFT)
        self.quality_var = tk.StringVar(value="85")
        quality_slider = ttk.Scale(quality_frame, from_=1, to=100, variable=self.quality_var, orient=tk.HORIZONTAL, length=200)
        quality_slider.pack(side=tk.LEFT, padx=10)
        self.quality_label = ttk.Label(quality_frame, text="85%")
        self.quality_label.pack(side=tk.LEFT)
        quality_slider.configure(command=lambda v: self.quality_label.config(text=f"{int(float(v))}%"))

        # Image format
        format_frame = ttk.Frame(options_frame)
        format_frame.pack(fill=tk.X, pady=5)
        ttk.Label(format_frame, text="Output Format:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="same")
        ttk.Radiobutton(format_frame, text="Keep Original", variable=self.format_var, value="same").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_frame, text="JPEG", variable=self.format_var, value="JPEG").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="PNG", variable=self.format_var, value="PNG").pack(side=tk.LEFT, padx=5)

        # Status label
        self.resize_status_label = ttk.Label(self.resizer_tab, text="", foreground="gray")
        self.resize_status_label.pack(pady=5)

        # Preview/Info area
        info_frame = ttk.LabelFrame(self.resizer_tab, text="Images Found", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tree view for image list
        self.resizer_tree = ttk.Treeview(info_frame, columns=("Name", "Size", "Dimensions"), show="headings", height=12)
        self.resizer_tree.heading("Name", text="Filename")
        self.resizer_tree.heading("Size", text="File Size")
        self.resizer_tree.heading("Dimensions", text="Dimensions")
        self.resizer_tree.column("Name", width=300)
        self.resizer_tree.column("Size", width=100)
        self.resizer_tree.column("Dimensions", width=120)

        resizer_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.resizer_tree.yview)
        self.resizer_tree.configure(yscroll=resizer_scrollbar.set)
        self.resizer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        resizer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def browse_resizer_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Images")
        if folder:
            self.resizer_folder_path = folder
            self.resizer_folder_label.config(text=folder, foreground="black")
            self.load_resizer_images()

    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.resizer_output_folder = folder
            self.resizer_output_label.config(text=folder, foreground="black")

    def load_resizer_images(self):
        self.resizer_images = []
        self.resizer_tree.delete(*self.resizer_tree.get_children())

        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}

        try:
            for filename in os.listdir(self.resizer_folder_path):
                file_path = os.path.join(self.resizer_folder_path, filename)
                ext = os.path.splitext(filename)[1].lower()

                if os.path.isfile(file_path) and ext in image_extensions:
                    try:
                        # Get file size
                        size = os.path.getsize(file_path)
                        size_str = self.format_size(size)

                        # Get image dimensions
                        with Image.open(file_path) as img:
                            dimensions = f"{img.width}×{img.height}"

                        self.resizer_images.append({
                            'name': filename,
                            'path': file_path,
                            'size': size,
                            'width': img.width,
                            'height': img.height
                        })

                        self.resizer_tree.insert("", tk.END, values=(filename, size_str, dimensions))
                    except:
                        pass

            if self.resizer_images:
                self.resize_status_label.config(text=f"Found {len(self.resizer_images)} images")
                self.resize_btn.config(state="normal")
            else:
                self.resize_status_label.config(text="No images found in folder")
                self.resize_btn.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", f"Error loading images: {str(e)}")

    def update_resize_ui(self):
        mode = self.resize_mode_var.get()
        if mode == "percentage":
            self.percentage_frame.pack(fill=tk.X, pady=5)
            self.fixed_frame.pack_forget()
            self.max_frame.pack_forget()
        elif mode == "fixed":
            self.fixed_frame.pack(fill=tk.X, pady=5)
            self.percentage_frame.pack_forget()
            self.max_frame.pack_forget()
        else:  # max
            self.max_frame.pack(fill=tk.X, pady=5)
            self.percentage_frame.pack_forget()
            self.fixed_frame.pack_forget()

    def apply_resize(self):
        if not self.resizer_images:
            return

        # Determine output folder
        output_folder = self.resizer_output_folder if self.resizer_output_folder else self.resizer_folder_path

        # Confirm if overwriting
        if output_folder == self.resizer_folder_path:
            response = messagebox.askyesno(
                "Confirm Overwrite",
                f"This will overwrite {len(self.resizer_images)} images in the original folder.\nContinue?"
            )
            if not response:
                return

        try:
            mode = self.resize_mode_var.get()
            quality = int(float(self.quality_var.get()))
            output_format = self.format_var.get()
            processed = 0

            for img_info in self.resizer_images:
                input_path = img_info['path']
                filename = img_info['name']

                # Open image
                with Image.open(input_path) as img:
                    # Calculate new size
                    if mode == "percentage":
                        scale = float(self.percentage_var.get()) / 100.0
                        new_width = int(img.width * scale)
                        new_height = int(img.height * scale)
                    elif mode == "fixed":
                        new_width = int(self.width_var.get())
                        new_height = int(self.height_var.get())
                    else:  # max dimensions
                        max_width = int(self.max_width_var.get())
                        max_height = int(self.max_height_var.get())
                        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                        new_width, new_height = img.size

                    # Resize if needed
                    if mode != "max":
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                    # Determine output format
                    if output_format == "same":
                        save_format = img.format or "JPEG"
                        output_filename = filename
                    else:
                        save_format = output_format
                        name_without_ext = os.path.splitext(filename)[0]
                        ext = ".jpg" if output_format == "JPEG" else ".png"
                        output_filename = f"{name_without_ext}{ext}"

                    # Save
                    output_path = os.path.join(output_folder, output_filename)

                    # Convert RGBA to RGB for JPEG
                    if save_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
                        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode == "P":
                            img = img.convert("RGBA")
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                        img = rgb_img

                    img.save(output_path, format=save_format, quality=quality, optimize=True)
                    processed += 1

                    # Log the resize
                    self.add_log("resize", f"Resized '{filename}' → {new_width}×{new_height} ({mode} mode)")

            messagebox.showinfo("Success", f"Resized {processed} images successfully!")
            self.resize_status_label.config(text=f"Successfully resized {processed} images")

            # Reload if output is same folder
            if output_folder == self.resizer_folder_path:
                self.load_resizer_images()

        except Exception as e:
            messagebox.showerror("Error", f"Error resizing images: {str(e)}")

    def clear_resizer(self):
        self.resizer_folder_path = ""
        self.resizer_output_folder = ""
        self.resizer_folder_label.config(text="No folder selected", foreground="gray")
        self.resizer_output_label.config(text="Same as input (will overwrite)", foreground="gray")
        self.resizer_images = []
        self.resizer_tree.delete(*self.resizer_tree.get_children())
        self.resize_status_label.config(text="")
        self.resize_btn.config(state="disabled")

    # ========== LOGGING SYSTEM ==========
    def load_logs(self):
        """Load logs from file"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []

    def save_logs(self):
        """Save logs to file"""
        try:
            # Keep only last 500 logs to prevent file from growing too large
            if len(self.logs) > 500:
                self.logs = self.logs[-500:]

            with open(self.log_file, 'w') as f:
                json.dump(self.logs, f, indent=2)
        except Exception as e:
            print(f"Error saving logs: {e}")

    def add_log(self, operation_type, details):
        """Add a log entry"""
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': operation_type,
            'details': details
        }
        self.logs.append(log_entry)
        self.save_logs()
        self.refresh_log_display()

    def init_log_viewer(self):
        """Initialize the log viewer tab"""
        # Header with controls
        header_frame = ttk.Frame(self.log_tab, padding="10")
        header_frame.pack(fill=tk.X)

        ttk.Label(header_frame, text="Operation Log", font=("", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(header_frame, text="Refresh", command=self.refresh_log_display).pack(side=tk.RIGHT, padx=5)
        ttk.Button(header_frame, text="Clear All Logs", command=self.clear_all_logs).pack(side=tk.RIGHT, padx=5)

        # Filter options
        filter_frame = ttk.Frame(self.log_tab, padding="10")
        filter_frame.pack(fill=tk.X)

        ttk.Label(filter_frame, text="Filter by:").pack(side=tk.LEFT)
        self.log_filter_var = tk.StringVar(value="all")
        ttk.Radiobutton(filter_frame, text="All", variable=self.log_filter_var,
                       value="all", command=self.refresh_log_display).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Renames", variable=self.log_filter_var,
                       value="rename", command=self.refresh_log_display).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Deletions", variable=self.log_filter_var,
                       value="delete", command=self.refresh_log_display).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Organization", variable=self.log_filter_var,
                       value="organize", command=self.refresh_log_display).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Resize", variable=self.log_filter_var,
                       value="resize", command=self.refresh_log_display).pack(side=tk.LEFT, padx=5)

        # Log display area
        log_frame = ttk.LabelFrame(self.log_tab, text="Recent Operations", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Text widget for logs
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=20, font=("Courier", 10))
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscroll=log_scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure text tags for color coding
        self.log_text.tag_configure("rename", foreground="#0066cc")
        self.log_text.tag_configure("delete", foreground="#cc0000")
        self.log_text.tag_configure("organize", foreground="#009900")
        self.log_text.tag_configure("resize", foreground="#9900cc")
        self.log_text.tag_configure("timestamp", foreground="#666666")

        # Initial display
        self.refresh_log_display()

    def refresh_log_display(self):
        """Refresh the log display with current logs"""
        self.log_text.delete(1.0, tk.END)

        filter_type = self.log_filter_var.get()
        displayed_logs = self.logs if filter_type == "all" else [
            log for log in self.logs if log['type'] == filter_type
        ]

        if not displayed_logs:
            self.log_text.insert(tk.END, "No operations logged yet.\n\n")
            self.log_text.insert(tk.END, "Operations will appear here when you:\n")
            self.log_text.insert(tk.END, "  • Rename files\n")
            self.log_text.insert(tk.END, "  • Delete duplicates\n")
            self.log_text.insert(tk.END, "  • Organize files\n")
            self.log_text.insert(tk.END, "  • Resize images\n")
            return

        # Display logs in reverse order (newest first)
        for log in reversed(displayed_logs[-100:]):  # Show last 100 logs
            timestamp = log['timestamp']
            op_type = log['type']
            details = log['details']

            # Format the log entry
            self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")

            if op_type == "rename":
                self.log_text.insert(tk.END, "RENAME: ", "rename")
                self.log_text.insert(tk.END, f"{details}\n")
            elif op_type == "delete":
                self.log_text.insert(tk.END, "DELETE: ", "delete")
                self.log_text.insert(tk.END, f"{details}\n")
            elif op_type == "organize":
                self.log_text.insert(tk.END, "ORGANIZE: ", "organize")
                self.log_text.insert(tk.END, f"{details}\n")
            elif op_type == "resize":
                self.log_text.insert(tk.END, "RESIZE: ", "resize")
                self.log_text.insert(tk.END, f"{details}\n")

            self.log_text.insert(tk.END, "\n")

        self.log_text.see(1.0)  # Scroll to top

    def clear_all_logs(self):
        """Clear all logs after confirmation"""
        response = messagebox.askyesno(
            "Clear All Logs",
            "Are you sure you want to clear all operation logs?\nThis cannot be undone."
        )
        if response:
            self.logs = []
            self.save_logs()
            self.refresh_log_display()
            messagebox.showinfo("Logs Cleared", "All operation logs have been cleared.")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = FileToolsApp(root)
    root.mainloop()
