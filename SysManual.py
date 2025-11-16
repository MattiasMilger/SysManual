import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import jsonschema
from jsonschema import validate

class SysManualFramework:
    def __init__(self, root):
        self.root = root
        self.root.title("SysManual Framework")
        self.root.geometry("1200x800")
        
        # Data storage
        self.sysmanuals: Dict[str, dict] = {}
        self.current_sysmanual: Optional[str] = None
        self.current_category: Optional[str] = None
        self.favorites: List[str] = []
        
        # Load schema
        self.schema = self.load_schema()
        
        # Setup UI
        self.setup_ui()
        
        # Auto-load sysmanuals from sysmanuals directory if it exists
        self.load_sysmanuals_from_directory()
    
    def load_schema(self) -> dict:
        """Load JSON schema for sysmanual validation"""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["id", "name", "description", "categories"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "theme": {
                    "type": "object",
                    "properties": {
                        "primary": {"type": "string"},
                        "accent": {"type": "string"}
                    }
                },
                "categories": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "name", "entries"],
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "entries": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["id", "name", "description"],
                                    "properties": {
                                        "id": {"type": "string"},
                                        "name": {"type": "string"},
                                        "description": {"type": "string"},
                                        "content": {"type": "object"},
                                        "examples": {
                                            "type": "array",
                                            "items": {
                                                "oneOf": [
                                                    {"type": "string"},
                                                    {
                                                        "type": "object",
                                                        "required": ["command"],
                                                        "properties": {
                                                            "command": {"type": "string"},
                                                            "description": {"type": "string"}
                                                        }
                                                    }
                                                ]
                                            }
                                        },
                                        "details": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "label": {"type": "string"},
                                                    "value": {"type": "string"}
                                                }
                                            }
                                        },
                                        "notes": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def validate_sysmanual(self, sysmanual_data: dict) -> bool:
        """Validate sysmanual JSON against schema"""
        try:
            validate(instance=sysmanual_data, schema=self.schema)
            return True
        except jsonschema.exceptions.ValidationError as e:
            messagebox.showerror("Validation Error", f"Invalid sysmanual format:\n{e.message}")
            return False
    
    def load_sysmanuals_from_directory(self):
        """Load all sysmanual JSON files from sysmanuals directory"""
        sysmanuals_dir = Path("sysmanuals")
        if not sysmanuals_dir.exists():
            sysmanuals_dir.mkdir()
            messagebox.showinfo("Welcome", "Created 'sysmanuals' directory.\n\nUse 'Open SysManual File' to load sysmanual JSON files.")
            return
        
        loaded_count = 0
        for json_file in sysmanuals_dir.glob("*.json"):
            if self.load_sysmanual_file(json_file):
                loaded_count += 1
        
        if loaded_count == 0:
            messagebox.showinfo("No SysManuals", "No valid sysmanual files found in 'sysmanuals' directory.\n\nUse 'Open SysManual File' to load sysmanual JSON files.")
        else:
            # Load first sysmanual if available
            if self.sysmanuals:
                first_sysmanual = list(self.sysmanuals.keys())[0]
                self.switch_sysmanual(first_sysmanual)
    
    def load_sysmanual_file(self, filepath) -> bool:
        """Load a single sysmanual JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sysmanual_data = json.load(f)
            
            if self.validate_sysmanual(sysmanual_data):
                self.sysmanuals[sysmanual_data['id']] = sysmanual_data
                # Update combo box values
                self.sysmanual_combo['values'] = list(self.sysmanuals.keys())
                return True
            return False
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load {Path(filepath).name}:\n{str(e)}")
            return False
    
    def open_sysmanual_file(self):
        """Open file dialog to load a sysmanual"""
        filepath = filedialog.askopenfilename(
            title="Select SysManual JSON File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=Path("sysmanuals") if Path("sysmanuals").exists() else Path.cwd()
        )
        
        if filepath:
            if self.load_sysmanual_file(filepath):
                sysmanual_id = None
                # Find the sysmanual we just loaded
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sysmanual_id = data['id']
                
                messagebox.showinfo("Success", f"Loaded sysmanual: {data['name']}")
                
                # Switch to the newly loaded sysmanual
                if sysmanual_id:
                    self.sysmanual_var.set(sysmanual_id)
                    self.switch_sysmanual(sysmanual_id)
    
    def setup_ui(self):
        """Setup the main UI"""
        # Top toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # SysManual selector
        ttk.Label(toolbar, text="SysManual:").pack(side=tk.LEFT, padx=5)
        self.sysmanual_var = tk.StringVar()
        self.sysmanual_combo = ttk.Combobox(
            toolbar, 
            textvariable=self.sysmanual_var,
            values=list(self.sysmanuals.keys()),
            state="readonly",
            width=20
        )
        self.sysmanual_combo.pack(side=tk.LEFT, padx=5)
        self.sysmanual_combo.bind("<<ComboboxSelected>>", lambda e: self.switch_sysmanual(self.sysmanual_var.get()))
        
        # Search
        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=(20, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_entries())
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # Editor button
        ttk.Button(toolbar, text="GUI Editor", command=self.open_gui_editor).pack(side=tk.RIGHT, padx=5)
        
        # Main content area
        content = ttk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Categories
        left_panel = ttk.Frame(content, width=200)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_panel.pack_propagate(False)
        
        ttk.Label(left_panel, text="Categories", font=('Arial', 12, 'bold')).pack(pady=5)
        
        self.category_listbox = tk.Listbox(left_panel, font=('Arial', 10))
        self.category_listbox.pack(fill=tk.BOTH, expand=True)
        self.category_listbox.bind('<<ListboxSelect>>', self.on_category_select)
        
        # Right panel - Entries
        right_panel = ttk.Frame(content)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # SysManual info
        self.info_frame = ttk.Frame(right_panel)
        self.info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.sysmanual_title = ttk.Label(self.info_frame, text="No sysmanual loaded", font=('Arial', 16, 'bold'))
        self.sysmanual_title.pack(anchor=tk.W)
        
        self.sysmanual_desc = ttk.Label(self.info_frame, text="Use 'Open SysManual File' to load a sysmanual", font=('Arial', 10))
        self.sysmanual_desc.pack(anchor=tk.W)
        
        # Entries list
        entries_frame = ttk.Frame(right_panel)
        entries_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable canvas for entries
        canvas = tk.Canvas(entries_frame)
        scrollbar = ttk.Scrollbar(entries_frame, orient="vertical", command=canvas.yview)
        self.entries_container = ttk.Frame(canvas)
        
        self.entries_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.entries_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mousewheel to root window for scrolling anywhere
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        
        self.root.bind("<MouseWheel>", on_mousewheel)
    
    def switch_sysmanual(self, sysmanual_id: str):
        """Switch to a different sysmanual"""
        if sysmanual_id not in self.sysmanuals:
            return
        
        self.current_sysmanual = sysmanual_id
        sysmanual = self.sysmanuals[sysmanual_id]
        
        # Update UI
        self.sysmanual_title.config(text=sysmanual['name'])
        self.sysmanual_desc.config(text=sysmanual['description'])
        
        # Update categories
        self.category_listbox.delete(0, tk.END)
        for category in sysmanual['categories']:
            self.category_listbox.insert(tk.END, category['name'])
        
        # Select first category
        if sysmanual['categories']:
            self.category_listbox.selection_set(0)
            self.current_category = sysmanual['categories'][0]['id']
            self.display_entries()
    
    def on_category_select(self, event):
        """Handle category selection"""
        selection = self.category_listbox.curselection()
        if not selection or not self.current_sysmanual:
            return
        
        sysmanual = self.sysmanuals[self.current_sysmanual]
        category_idx = selection[0]
        self.current_category = sysmanual['categories'][category_idx]['id']
        self.display_entries()
    
    def display_entries(self):
        """Display entries for current category"""
        # Clear existing entries
        for widget in self.entries_container.winfo_children():
            widget.destroy()
        
        if not self.current_sysmanual or not self.current_category:
            return
        
        sysmanual = self.sysmanuals[self.current_sysmanual]
        category = next((c for c in sysmanual['categories'] if c['id'] == self.current_category), None)
        
        if not category:
            return
        
        search_term = self.search_var.get().lower()
        
        for entry in category['entries']:
            # Filter by search
            if search_term and search_term not in entry['name'].lower() and search_term not in entry['description'].lower():
                continue
            
            self.create_entry_widget(entry)
    
    def create_entry_widget(self, entry: dict):
        """Create a widget for an entry"""
        frame = ttk.LabelFrame(self.entries_container, text=entry['name'], padding=15)
        frame.pack(fill=tk.X, pady=8, padx=5)
        
        # Description - larger, more visible
        desc_label = ttk.Label(frame, text=entry['description'], wraplength=700, font=('Arial', 10))
        desc_label.pack(anchor=tk.W, pady=(0, 8))
        
        # Content (flexible key-value pairs)
        if entry.get('content'):
            for key, value in entry['content'].items():
                content_frame = ttk.Frame(frame)
                content_frame.pack(fill=tk.X, pady=3)
                
                ttk.Label(content_frame, text=f"{key}:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
                
                content_text = tk.Text(content_frame, height=1, wrap=tk.NONE, font=('Courier', 9), bg='#f0f0f0')
                content_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                content_text.insert('1.0', str(value))
                content_text.config(state=tk.DISABLED)
                
                ttk.Button(content_frame, text="Copy", width=6, command=lambda v=value: self.copy_to_clipboard(str(v))).pack(side=tk.LEFT)
        
        # Examples - support both old (string) and new (object) format
        if entry.get('examples'):
            ttk.Label(frame, text="Examples:", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(5, 2))
            for example in entry['examples']:
                ex_frame = ttk.Frame(frame)
                ex_frame.pack(fill=tk.X, pady=2)
                
                # Check if example is a string (old format) or dict (new format)
                if isinstance(example, str):
                    # Old format: just the command
                    command = example
                    description = None
                else:
                    # New format: object with command and description
                    command = example.get('command', '')
                    description = example.get('description', None)
                
                # Command text box
                ex_text = tk.Text(ex_frame, height=1, wrap=tk.NONE, font=('Courier', 8), bg='#f9f9f9')
                ex_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
                ex_text.insert('1.0', command)
                ex_text.config(state=tk.DISABLED)
                
                ttk.Button(ex_frame, text="Copy", width=6, command=lambda c=command: self.copy_to_clipboard(c)).pack(side=tk.LEFT)
                
                # Description (if new format)
                if description:
                    desc_frame = ttk.Frame(frame)
                    desc_frame.pack(fill=tk.X, pady=(0, 2))
                    ttk.Label(desc_frame, text=f"  → {description}", font=('Arial', 8), foreground='#555', wraplength=680).pack(anchor=tk.W, padx=(10, 0))
        
        # Details (expandable list)
        if entry.get('details'):
            details_btn = ttk.Button(frame, text="Show Details", command=lambda: self.show_details(entry))
            details_btn.pack(anchor=tk.W, pady=(5, 0))
        
        # Notes
        if entry.get('notes'):
            notes_label = ttk.Label(frame, text=f"Note: {entry['notes']}", wraplength=700, foreground='#666')
            notes_label.pack(anchor=tk.W, pady=(5, 0))
    
    def show_details(self, entry: dict):
        """Show entry details in a popup"""
        popup = tk.Toplevel(self.root)
        popup.title(f"{entry['name']} - Details")
        popup.geometry("600x400")
        
        text = scrolledtext.ScrolledText(popup, wrap=tk.WORD, font=('Courier', 9))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for detail in entry.get('details', []):
            text.insert(tk.END, f"{detail['label']}\n", 'label')
            text.insert(tk.END, f"  {detail['value']}\n\n")
        
        text.tag_config('label', font=('Courier', 9, 'bold'), foreground='#0066cc')
        text.config(state=tk.DISABLED)
    
    def filter_entries(self):
        """Filter entries based on search"""
        self.display_entries()
    
    def copy_to_clipboard(self, text: str):
        """Copy text to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copied", "Copied to clipboard!")
    
    def open_gui_editor(self):
        """Open GUI sysmanual editor"""
        editor = SysManualGUIEditor(self.root, self)

class SysManualGUIEditor:
    def __init__(self, parent, framework):
        self.framework = framework
        self.window = tk.Toplevel(parent)
        self.window.title("SysManual GUI Editor")
        self.window.geometry("1400x900")
        
        self.current_sysmanual = None
        self.editing_item = None
        
        # Main container
        main_container = ttk.Frame(self.window)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar
        self.setup_toolbar()
        
        # Paned window for tree and editor
        paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: Tree view
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        self.setup_tree(left_frame)
        
        # Right: Edit panel
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)
        self.setup_edit_panel(right_frame)
        
        # Load current sysmanual if available
        if framework.current_sysmanual:
            self.load_sysmanual(framework.current_sysmanual)
    
    def setup_toolbar(self):
        toolbar = ttk.Frame(self.window)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="New SysManual", command=self.new_sysmanual).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Open File", command=self.open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_sysmanual).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        ttk.Label(toolbar, text="Load:").pack(side=tk.LEFT, padx=(5, 2))
        self.load_combo = ttk.Combobox(toolbar, values=list(self.framework.sysmanuals.keys()), 
                                       state="readonly", width=20)
        self.load_combo.pack(side=tk.LEFT, padx=2)
        self.load_combo.bind("<<ComboboxSelected>>", lambda e: self.load_sysmanual(self.load_combo.get()))
    
    def setup_tree(self, parent):
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(tree_frame, text="Structure", font=('Arial', 11, 'bold')).pack(anchor=tk.W, pady=5)
        
        # Tree with scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set)
        self.tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Button-3>', self.show_context_menu)  # Right-click
    
    def setup_edit_panel(self, parent):
        # Scrollable edit panel
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.edit_frame = ttk.Frame(canvas)
        
        self.edit_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.edit_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mousewheel - bind to relevant widgets in editor
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        
        # Bind to multiple widgets to ensure scrolling works anywhere in edit panel
        for widget in [canvas, self.edit_frame, right_frame]:
            widget.bind("<MouseWheel>", on_mousewheel)
        
        # Initial message
        ttk.Label(self.edit_frame, text="Select an item to edit", 
                 font=('Arial', 12)).pack(pady=20)
    
    def new_sysmanual(self):
        """Create new sysmanual"""
        if self.current_sysmanual and messagebox.askyesno("New SysManual", 
            "Create new sysmanual? Unsaved changes will be lost."):
            self.current_sysmanual = None
            self.tree.delete(*self.tree.get_children())
            self.clear_edit_panel()
        
        # Create template
        template = {
            "id": "new-sysmanual",
            "name": "New SysManual",
            "description": "Description",
            "theme": {"primary": "#4CAF50", "accent": "#2196F3"},
            "categories": []
        }
        self.current_sysmanual = template
        self.populate_tree()
        self.tree.selection_set(self.tree.get_children()[0])
        self.on_tree_select(None)
    
    def open_file(self):
        """Open file to edit"""
        filepath = filedialog.askopenfilename(
            title="Open SysManual JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=Path("sysmanuals") if Path("sysmanuals").exists() else Path.cwd()
        )
        
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if self.framework.validate_sysmanual(data):
                    self.current_sysmanual = data
                    self.populate_tree()
                    messagebox.showinfo("Success", "Loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open:\n{str(e)}")
    
    def load_sysmanual(self, sysmanual_id):
        """Load existing sysmanual for editing"""
        if sysmanual_id in self.framework.sysmanuals:
            # Create a deep copy to avoid modifying the original
            import copy
            self.current_sysmanual = copy.deepcopy(self.framework.sysmanuals[sysmanual_id])
            self.populate_tree()
    
    def populate_tree(self):
        """Populate tree with current sysmanual"""
        self.tree.delete(*self.tree.get_children())
        
        if not self.current_sysmanual:
            return
        
        # Root: SysManual
        root = self.tree.insert('', 'end', text=f"📘 {self.current_sysmanual['name']}", 
                               values=('sysmanual',), open=True)
        
        # Categories
        for cat_idx, category in enumerate(self.current_sysmanual.get('categories', [])):
            cat_node = self.tree.insert(root, 'end', text=f"📁 {category['name']}", 
                                       values=('category', cat_idx), open=True)
            
            # Entries
            for entry_idx, entry in enumerate(category.get('entries', [])):
                self.tree.insert(cat_node, 'end', text=f"📄 {entry['name']}", 
                               values=('entry', cat_idx, entry_idx))
        
        # Keep focus on editor window
        self.window.lift()
        self.window.focus_force()
    
    def on_tree_select(self, event):
        """Handle tree selection"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        
        if not values:
            return
        
        item_type = values[0]
        
        if item_type == 'sysmanual':
            self.show_sysmanual_editor()
        elif item_type == 'category':
            cat_idx = int(values[1])
            self.show_category_editor(cat_idx)
        elif item_type == 'entry':
            cat_idx = int(values[1])
            entry_idx = int(values[2])
            self.show_entry_editor(cat_idx, entry_idx)
    
    def clear_edit_panel(self):
        """Clear the edit panel"""
        for widget in self.edit_frame.winfo_children():
            widget.destroy()
    
    def show_sysmanual_editor(self):
        """Show editor for sysmanual metadata"""
        self.clear_edit_panel()
        
        ttk.Label(self.edit_frame, text="SysManual Settings", 
                 font=('Arial', 14, 'bold')).pack(anchor=tk.W, pady=(10, 20), padx=10)
        
        # ID
        self.create_field("ID:", self.current_sysmanual, 'id')
        
        # Name
        self.create_field("Name:", self.current_sysmanual, 'name')
        
        # Description
        self.create_text_field("Description:", self.current_sysmanual, 'description', height=3)
    
    def show_category_editor(self, cat_idx):
        """Show editor for category"""
        self.clear_edit_panel()
        
        category = self.current_sysmanual['categories'][cat_idx]
        
        ttk.Label(self.edit_frame, text="Category Settings", 
                 font=('Arial', 14, 'bold')).pack(anchor=tk.W, pady=(10, 20), padx=10)
        
        self.create_field("ID:", category, 'id')
        self.create_field("Name:", category, 'name')
        
        # Add entry button
        ttk.Button(self.edit_frame, text="+ Add Entry", 
                  command=lambda: self.add_entry(cat_idx)).pack(anchor=tk.W, padx=10, pady=10)
    
    def show_entry_editor(self, cat_idx, entry_idx):
        """Show editor for entry"""
        self.clear_edit_panel()
        
        category = self.current_sysmanual['categories'][cat_idx]
        entry = category['entries'][entry_idx]
        
        ttk.Label(self.edit_frame, text="Entry Editor", 
                 font=('Arial', 14, 'bold')).pack(anchor=tk.W, pady=(10, 20), padx=10)
        
        # Basic fields
        self.create_field("ID:", entry, 'id')
        self.create_field("Name:", entry, 'name')
        self.create_text_field("Description:", entry, 'description', height=3)
        
        # Content section (key-value pairs)
        content_frame = ttk.LabelFrame(self.edit_frame, text="Content", padding=10)
        content_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        
        if 'content' not in entry:
            entry['content'] = {}
        
        # Display existing content
        for key in list(entry['content'].keys()):
            self.create_content_row(content_frame, entry, key)
        
        # Add content button
        ttk.Button(content_frame, text="+ Add Content Field", 
                  command=lambda: self.add_content_field(content_frame, entry)).pack(anchor=tk.W, pady=5)
        
        # Examples section
        examples_frame = ttk.LabelFrame(self.edit_frame, text="Examples", padding=10)
        examples_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        
        if 'examples' not in entry:
            entry['examples'] = []
        
        for idx, example in enumerate(entry['examples']):
            self.create_example_row(examples_frame, entry, idx)
        
        ttk.Button(examples_frame, text="+ Add Example", 
                  command=lambda: self.add_example(examples_frame, entry)).pack(anchor=tk.W, pady=5)
        
        # Details section
        details_frame = ttk.LabelFrame(self.edit_frame, text="Details", padding=10)
        details_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        
        if 'details' not in entry:
            entry['details'] = []
        
        for idx, detail in enumerate(entry['details']):
            self.create_detail_row(details_frame, entry, idx)
        
        ttk.Button(details_frame, text="+ Add Detail", 
                  command=lambda: self.add_detail(details_frame, entry)).pack(anchor=tk.W, pady=5)
        
        # Notes
        self.create_text_field("Notes:", entry, 'notes', height=3)
    
    def create_field(self, label, data_dict, key, parent=None):
        """Create a simple text field"""
        if parent is None:
            parent = self.edit_frame
        
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame, text=label, width=15).pack(side=tk.LEFT)
        
        var = tk.StringVar(value=data_dict.get(key, ''))
        entry = ttk.Entry(frame, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Update data on change
        var.trace('w', lambda *args: data_dict.update({key: var.get()}))
    
    def create_text_field(self, label, data_dict, key, height=5, parent=None):
        """Create a text area field"""
        if parent is None:
            parent = self.edit_frame
        
        frame = ttk.LabelFrame(parent, text=label, padding=5)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        text = tk.Text(frame, height=height, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert('1.0', data_dict.get(key, ''))
        
        # Update data on change
        def update_text(*args):
            data_dict[key] = text.get('1.0', 'end-1c')
        
        text.bind('<KeyRelease>', update_text)
    
    def create_content_row(self, parent, entry, key):
        """Create a row for content key-value pair"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        key_var = tk.StringVar(value=key)
        value_var = tk.StringVar(value=entry['content'][key])
        
        ttk.Label(frame, text="Key:").pack(side=tk.LEFT)
        key_entry = ttk.Entry(frame, textvariable=key_var, width=15)
        key_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(frame, text="Value:").pack(side=tk.LEFT)
        value_entry = ttk.Entry(frame, textvariable=value_var)
        value_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Update on change
        def update_content(*args):
            new_key = key_var.get()
            if new_key != key and key in entry['content']:
                del entry['content'][key]
            entry['content'][new_key] = value_var.get()
        
        key_var.trace('w', update_content)
        value_var.trace('w', update_content)
        
        ttk.Button(frame, text="×", width=3, 
                  command=lambda: self.remove_content(parent, entry, key, frame)).pack(side=tk.LEFT)
    
    def add_content_field(self, parent, entry):
        """Add new content field"""
        key = f"field_{len(entry['content']) + 1}"
        entry['content'][key] = ""
        self.create_content_row(parent, entry, key)
    
    def remove_content(self, parent, entry, key, frame):
        """Remove content field"""
        if key in entry['content']:
            del entry['content'][key]
        frame.destroy()
    
    def create_example_row(self, parent, entry, idx):
        """Create a row for an example"""
        frame = ttk.LabelFrame(parent, text=f"Example {idx + 1}", padding=5)
        frame.pack(fill=tk.X, pady=5)
        
        example = entry['examples'][idx]
        
        # Handle both string and dict formats
        if isinstance(example, str):
            example = {"command": example, "description": ""}
            entry['examples'][idx] = example
        
        # Command
        cmd_frame = ttk.Frame(frame)
        cmd_frame.pack(fill=tk.X, pady=2)
        ttk.Label(cmd_frame, text="Command:").pack(side=tk.LEFT)
        cmd_var = tk.StringVar(value=example.get('command', ''))
        cmd_entry = ttk.Entry(cmd_frame, textvariable=cmd_var)
        cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        cmd_var.trace('w', lambda *args: example.update({'command': cmd_var.get()}))
        
        # Description
        desc_frame = ttk.Frame(frame)
        desc_frame.pack(fill=tk.X, pady=2)
        ttk.Label(desc_frame, text="Description:").pack(side=tk.LEFT)
        desc_var = tk.StringVar(value=example.get('description', ''))
        desc_entry = ttk.Entry(desc_frame, textvariable=desc_var)
        desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        desc_var.trace('w', lambda *args: example.update({'description': desc_var.get()}))
        
        # Remove button
        ttk.Button(frame, text="Remove Example", 
                  command=lambda: self.remove_example(parent, entry, idx, frame)).pack(anchor=tk.E, pady=2)
    
    def add_example(self, parent, entry):
        """Add new example"""
        entry['examples'].append({"command": "", "description": ""})
        self.create_example_row(parent, entry, len(entry['examples']) - 1)
    
    def remove_example(self, parent, entry, idx, frame):
        """Remove example"""
        if idx < len(entry['examples']):
            entry['examples'].pop(idx)
        frame.destroy()
        # Refresh to update indices
        for widget in parent.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                widget.destroy()
        for i, example in enumerate(entry['examples']):
            self.create_example_row(parent, entry, i)
    
    def create_detail_row(self, parent, entry, idx):
        """Create a row for a detail"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        detail = entry['details'][idx]
        
        ttk.Label(frame, text="Label:").pack(side=tk.LEFT)
        label_var = tk.StringVar(value=detail.get('label', ''))
        label_entry = ttk.Entry(frame, textvariable=label_var, width=20)
        label_entry.pack(side=tk.LEFT, padx=5)
        label_var.trace('w', lambda *args: detail.update({'label': label_var.get()}))
        
        ttk.Label(frame, text="Value:").pack(side=tk.LEFT)
        value_var = tk.StringVar(value=detail.get('value', ''))
        value_entry = ttk.Entry(frame, textvariable=value_var)
        value_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        value_var.trace('w', lambda *args: detail.update({'value': value_var.get()}))
        
        ttk.Button(frame, text="×", width=3,
                  command=lambda: self.remove_detail(parent, entry, idx, frame)).pack(side=tk.LEFT)
    
    def add_detail(self, parent, entry):
        """Add new detail"""
        entry['details'].append({"label": "", "value": ""})
        self.create_detail_row(parent, entry, len(entry['details']) - 1)
    
    def remove_detail(self, parent, entry, idx, frame):
        """Remove detail"""
        if idx < len(entry['details']):
            entry['details'].pop(idx)
        frame.destroy()
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        self.tree.selection_set(item)
        values = self.tree.item(item, 'values')
        
        # Create context menu dynamically
        context_menu = tk.Menu(self.tree, tearoff=0)
        
        if not values or values[0] == 'sysmanual':
            # Root sysmanual - only allow adding category
            context_menu.add_command(label="Add Category", command=self.add_category)
        elif values[0] == 'category':
            # Category node
            context_menu.add_command(label="Add Entry", command=self.add_entry)
            context_menu.add_separator()
            context_menu.add_command(label="Move Up ↑", command=self.move_item_up)
            context_menu.add_command(label="Move Down ↓", command=self.move_item_down)
            context_menu.add_separator()
            context_menu.add_command(label="Delete Category", command=self.delete_item)
        elif values[0] == 'entry':
            # Entry node
            context_menu.add_command(label="Move Up ↑", command=self.move_item_up)
            context_menu.add_command(label="Move Down ↓", command=self.move_item_down)
            context_menu.add_separator()
            context_menu.add_command(label="Delete Entry", command=self.delete_item)
        
        context_menu.post(event.x_root, event.y_root)
    
    def add_category(self):
        """Add new category"""
        if not self.current_sysmanual:
            return
        
        category = {
            "id": f"category_{len(self.current_sysmanual['categories']) + 1}",
            "name": "New Category",
            "entries": []
        }
        self.current_sysmanual['categories'].append(category)
        self.populate_tree()
    
    def add_entry(self, cat_idx=None):
        """Add new entry"""
        if not self.current_sysmanual:
            return
        
        # If no category specified, use selected one
        if cat_idx is None:
            selection = self.tree.selection()
            if not selection:
                return
            
            values = self.tree.item(selection[0], 'values')
            if not values or values[0] not in ['category', 'entry']:
                return
            
            cat_idx = int(values[1])
        
        category = self.current_sysmanual['categories'][cat_idx]
        entry = {
            "id": f"entry_{len(category['entries']) + 1}",
            "name": "New Entry",
            "description": "Description",
            "content": {},
            "examples": [],
            "details": [],
            "notes": ""
        }
        category['entries'].append(entry)
        self.populate_tree()
    
    def delete_item(self):
        """Delete selected item"""
        selection = self.tree.selection()
        if not selection:
            return
        
        values = self.tree.item(selection[0], 'values')
        if not values:
            return
        
        item_type = values[0]
        
        if item_type == 'sysmanual':
            return
        
        if not messagebox.askyesno("Confirm Delete", f"Delete this {item_type}?"):
            self.window.lift()
            self.window.focus_force()
            return
        
        if item_type == 'category':
            cat_idx = int(values[1])
            self.current_sysmanual['categories'].pop(cat_idx)
        elif item_type == 'entry':
            cat_idx = int(values[1])
            entry_idx = int(values[2])
            self.current_sysmanual['categories'][cat_idx]['entries'].pop(entry_idx)
        
        self.populate_tree()
        self.clear_edit_panel()
    
    def move_item_up(self):
        """Move selected item up in the list"""
        selection = self.tree.selection()
        if not selection:
            return
        
        values = self.tree.item(selection[0], 'values')
        if not values:
            return
        
        item_type = values[0]
        
        if item_type == 'sysmanual':
            return
        
        if item_type == 'category':
            cat_idx = int(values[1])
            if cat_idx == 0:
                return
            
            # Swap with previous
            categories = self.current_sysmanual['categories']
            categories[cat_idx], categories[cat_idx - 1] = categories[cat_idx - 1], categories[cat_idx]
            
        elif item_type == 'entry':
            cat_idx = int(values[1])
            entry_idx = int(values[2])
            if entry_idx == 0:
                return
            
            # Swap with previous
            entries = self.current_sysmanual['categories'][cat_idx]['entries']
            entries[entry_idx], entries[entry_idx - 1] = entries[entry_idx - 1], entries[entry_idx]
        
        self.populate_tree()
        # Try to reselect the moved item
        self.select_item_after_move(item_type, values, -1)
    
    def move_item_down(self):
        """Move selected item down in the list"""
        selection = self.tree.selection()
        if not selection:
            return
        
        values = self.tree.item(selection[0], 'values')
        if not values:
            return
        
        item_type = values[0]
        
        if item_type == 'sysmanual':
            return
        
        if item_type == 'category':
            cat_idx = int(values[1])
            categories = self.current_sysmanual['categories']
            if cat_idx >= len(categories) - 1:
                return
            
            # Swap with next
            categories[cat_idx], categories[cat_idx + 1] = categories[cat_idx + 1], categories[cat_idx]
            
        elif item_type == 'entry':
            cat_idx = int(values[1])
            entry_idx = int(values[2])
            entries = self.current_sysmanual['categories'][cat_idx]['entries']
            if entry_idx >= len(entries) - 1:
                return
            
            # Swap with next
            entries[entry_idx], entries[entry_idx + 1] = entries[entry_idx + 1], entries[entry_idx]
        
        self.populate_tree()
        # Try to reselect the moved item
        self.select_item_after_move(item_type, values, 1)
    
    def select_item_after_move(self, item_type, old_values, direction):
        """Reselect item after moving it"""
        if item_type == 'category':
            new_idx = int(old_values[1]) + direction
            # Find the item in tree with matching values
            for item in self.tree.get_children(self.tree.get_children()[0]):
                if self.tree.item(item, 'values') == ('category', new_idx):
                    self.tree.selection_set(item)
                    self.tree.see(item)
                    break
        elif item_type == 'entry':
            cat_idx = int(old_values[1])
            new_entry_idx = int(old_values[2]) + direction
            # Find category first
            root = self.tree.get_children()[0]
            categories = self.tree.get_children(root)
            if cat_idx < len(categories):
                cat_item = categories[cat_idx]
                # Find entry
                for entry_item in self.tree.get_children(cat_item):
                    if self.tree.item(entry_item, 'values') == ('entry', cat_idx, new_entry_idx):
                        self.tree.selection_set(entry_item)
                        self.tree.see(entry_item)
                        break
    
    def save_sysmanual(self):
        """Save the current sysmanual"""
        if not self.current_sysmanual:
            return
        
        if not self.framework.validate_sysmanual(self.current_sysmanual):
            self.window.lift()
            self.window.focus_force()
            return
        
        # Keep reference to editor window
        editor_window = self.window
        
        filepath = filedialog.asksaveasfilename(
            title="Save SysManual",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=Path("sysmanuals") if Path("sysmanuals").exists() else Path.cwd(),
            initialfile=f"{self.current_sysmanual['id']}_sysmanual.json",
            parent=self.window
        )
        
        # Immediately restore focus after file dialog
        editor_window.lift()
        editor_window.focus_force()
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.current_sysmanual, f, indent=2)
                
                # Just reload the data in framework without triggering any UI updates
                self.framework.load_sysmanual_file(filepath)
                
                # Update combo box options
                self.load_combo['values'] = list(self.framework.sysmanuals.keys())
                
                # Keep focus
                editor_window.lift()
                editor_window.focus_force()
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save:\n{str(e)}")
                editor_window.lift()
                editor_window.focus_force()

def main():
    root = tk.Tk()
    app = SysManualFramework(root)
    root.mainloop()

if __name__ == "__main__":
    main()
