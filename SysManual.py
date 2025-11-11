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
                                            "items": {"type": "string"}
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
        
        # Open file button
        ttk.Button(toolbar, text="Open SysManual File", command=self.open_sysmanual_file).pack(side=tk.LEFT, padx=5)
        
        # SysManual selector
        ttk.Label(toolbar, text="SysManual:").pack(side=tk.LEFT, padx=(15, 5))
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
        ttk.Button(toolbar, text="SysManual Editor", command=self.open_editor).pack(side=tk.RIGHT, padx=5)
        
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
        
        # Bind mousewheel
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    
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
        frame = ttk.LabelFrame(self.entries_container, text=entry['name'], padding=10)
        frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Description
        desc_label = ttk.Label(frame, text=entry['description'], wraplength=700)
        desc_label.pack(anchor=tk.W, pady=(0, 5))
        
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
        
        # Examples
        if entry.get('examples'):
            ttk.Label(frame, text="Examples:", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(5, 2))
            for example in entry['examples']:
                ex_frame = ttk.Frame(frame)
                ex_frame.pack(fill=tk.X, pady=2)
                
                ex_text = tk.Text(ex_frame, height=1, wrap=tk.NONE, font=('Courier', 8), bg='#f9f9f9')
                ex_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
                ex_text.insert('1.0', example)
                ex_text.config(state=tk.DISABLED)
                
                ttk.Button(ex_frame, text="Copy", width=6, command=lambda e=example: self.copy_to_clipboard(e)).pack(side=tk.LEFT)
        
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
    
    def open_editor(self):
        """Open sysmanual editor"""
        editor = SysManualEditor(self.root, self)

class SysManualEditor:
    def __init__(self, parent, framework):
        self.framework = framework
        self.window = tk.Toplevel(parent)
        self.window.title("SysManual Editor")
        self.window.geometry("800x600")
        
        # Toolbar
        toolbar = ttk.Frame(self.window)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="New SysManual", command=self.new_sysmanual).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Open File", command=self.open_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Save", command=self.save_sysmanual).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Validate", command=self.validate).pack(side=tk.LEFT, padx=5)
        
        # JSON editor
        ttk.Label(self.window, text="Edit SysManual JSON:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, padx=5)
        
        self.editor = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, font=('Courier', 10))
        self.editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Load template
        self.load_template()
    
    def load_template(self):
        """Load a template sysmanual"""
        template = {
            "id": "my-sysmanual",
            "name": "My SysManual",
            "description": "Description of my sysmanual",
            "theme": {
                "primary": "#4CAF50",
                "accent": "#2196F3"
            },
            "categories": [
                {
                    "id": "category-1",
                    "name": "Category 1",
                    "entries": [
                        {
                            "id": "entry-1",
                            "name": "example-entry",
                            "description": "This is an example entry",
                            "content": {
                                "Command": "example-command [options]",
                                "Port": "8080",
                                "Protocol": "TCP"
                            },
                            "examples": [
                                "example-command -h",
                                "example-command --verbose"
                            ],
                            "details": [
                                {
                                    "label": "-h, --help",
                                    "value": "Show help message"
                                }
                            ],
                            "notes": "Additional notes about this entry"
                        }
                    ]
                }
            ]
        }
        self.editor.delete('1.0', tk.END)
        self.editor.insert('1.0', json.dumps(template, indent=2))
    
    def new_sysmanual(self):
        """Create a new sysmanual"""
        if messagebox.askyesno("New SysManual", "This will clear the current editor. Continue?"):
            self.load_template()
    
    def open_file(self):
        """Open a sysmanual file in the editor"""
        filepath = filedialog.askopenfilename(
            title="Open SysManual JSON File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=Path("sysmanuals") if Path("sysmanuals").exists() else Path.cwd()
        )
        
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.editor.delete('1.0', tk.END)
                self.editor.insert('1.0', json.dumps(data, indent=2))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file:\n{str(e)}")
    
    def validate(self):
        """Validate the current JSON"""
        try:
            data = json.loads(self.editor.get('1.0', tk.END))
            if self.framework.validate_sysmanual(data):
                messagebox.showinfo("Valid", "SysManual JSON is valid!")
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"JSON parsing error:\n{str(e)}")
    
    def save_sysmanual(self):
        """Save the sysmanual"""
        try:
            data = json.loads(self.editor.get('1.0', tk.END))
            if not self.framework.validate_sysmanual(data):
                return
            
            # Ask where to save
            filepath = filedialog.asksaveasfilename(
                title="Save SysManual",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir=Path("sysmanuals") if Path("sysmanuals").exists() else Path.cwd(),
                initialfile=f"{data['id']}_sysmanual.json"
            )
            
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                messagebox.showinfo("Saved", f"SysManual saved to {Path(filepath).name}")
                
                # Reload if saved in sysmanuals directory
                if self.framework.load_sysmanual_file(filepath):
                    self.framework.sysmanual_var.set(data['id'])
                    self.framework.switch_sysmanual(data['id'])
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save:\n{str(e)}")

def main():
    root = tk.Tk()
    app = SysManualFramework(root)
    root.mainloop()

if __name__ == "__main__":
    main()