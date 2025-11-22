# SysManual.py

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import copy

# Import modularized components
from sysmanual_core import SysManualCore, SysManualSearch
from sysmanual_editor import SysManualGUIEditor

class SysManualFramework:
    def __init__(self, root):
        self.root = root
        self.root.title("SysManual Framework")
        self.root.geometry("1200x800")
        
        # Core utility instance
        self.core = SysManualCore()
        self.searcher = SysManualSearch()
        
        # Data storage
        self.sysmanuals: Dict[str, dict] = {}
        self.current_sysmanual: Optional[str] = None
        self.current_category: Optional[str] = None
        self.favorites: List[str] = []
        
        # Load schema and setup UI
        self.schema = self.core.load_schema()
        self.setup_ui()
        
        # Auto-load sysmanuals from sysmanuals directory
        self.load_sysmanuals_from_directory()
    
    def validate_sysmanual(self, sysmanual_data: dict) -> bool:
        """Validate sysmanual JSON against schema using SysManualCore."""
        return self.core.validate_sysmanual(sysmanual_data, self.schema)
    
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
                try:
                    self.sysmanual_combo['values'] = list(self.sysmanuals.keys())
                except Exception:
                    pass
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
        
        # Open File button
        ttk.Button(toolbar, text="Open SysManual File", command=self.open_sysmanual_file).pack(side=tk.LEFT, padx=5)

        # Editor button
        ttk.Button(toolbar, text="SysManual Editor", command=self.open_gui_editor).pack(side=tk.RIGHT, padx=5)

        # Advanced Search button
        ttk.Button(toolbar, text="Advanced Search", command=self.open_advanced_search).pack(side=tk.RIGHT, padx=5)
        
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
        self.entries_canvas = tk.Canvas(entries_frame)
        scrollbar = ttk.Scrollbar(entries_frame, orient="vertical", command=self.entries_canvas.yview)
        self.entries_container = ttk.Frame(self.entries_canvas)
        
        self.entries_container.bind(
            "<Configure>",
            lambda e: self.entries_canvas.configure(scrollregion=self.entries_canvas.bbox("all"))
        )
        
        self.entries_canvas.create_window((0, 0), window=self.entries_container, anchor="nw")
        self.entries_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.entries_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mousewheel to root window for scrolling anywhere
        def on_mousewheel(e):
            self.entries_canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        
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
            self.display_entries(from_category=True)
    
    def on_category_select(self, event):
        """Handle category selection"""
        selection = self.category_listbox.curselection()
        if not selection or not self.current_sysmanual:
            return

        self.search_var.set("")

        sysmanual = self.sysmanuals[self.current_sysmanual]
        category_idx = selection[0]
        self.current_category = sysmanual['categories'][category_idx]['id']

        self.display_entries(from_category=True)
    
    def display_entries(self, from_category: bool = False):
        """Display entries for current category or run fast category-only search."""
        for w in self.entries_container.winfo_children():
            w.destroy()

        if not self.current_sysmanual:
            return

        sysmanual = self.sysmanuals[self.current_sysmanual]
        search_term = (self.search_var.get() or "").strip()

        if search_term:
            if not self.current_category:
                return

            category = next(
                (c for c in sysmanual['categories'] if c['id'] == self.current_category),
                None
            )
            if not category:
                return

            entries = category.get('entries', [])
            
            # Use the searcher's scoring logic for a faster internal search
            # min_score is intentionally low (0.12) to be inclusive in the fast view
            matches = self.searcher.search_entries_in_category(entries, search_term)

            for entry in matches:
                self.create_entry_widget(entry)
            return

        if not self.current_category:
            return

        category = next(
            (c for c in sysmanual['categories'] if c['id'] == self.current_category),
            None
        )
        if not category:
            return

        for entry in category.get('entries', []):
            self.create_entry_widget(entry)

        if from_category and hasattr(self, "entries_canvas"):
            try:
                self.entries_canvas.yview_moveto(0)
            except Exception:
                pass
    
    def create_entry_widget(self, entry: dict):
        """Create a widget for an entry"""
        frame = ttk.LabelFrame(self.entries_container, text=entry['name'], padding=15)
        frame.pack(fill=tk.X, pady=8, padx=5)
        
        desc_label = ttk.Label(frame, text=entry['description'], wraplength=700, font=('Arial', 10))
        desc_label.pack(anchor=tk.W, pady=(0, 8))
        
        if entry.get('content'):
            for key, value in entry['content'].items():
                content_frame = ttk.Frame(frame)
                content_frame.pack(fill=tk.X, pady=3)
                
                ttk.Label(content_frame, text=f"{key}:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
                
                content_text = tk.Text(content_frame, height=1, wrap=tk.NONE, font=('Courier', 9), bg='#f0f0f0')
                content_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                content_text.insert('1.0', str(value))
                content_text.config(state=tk.DISABLED)
                
                ttk.Button(content_frame, text="Copy", width=6, command=lambda v=value: self.core.copy_to_clipboard(self.root, str(v))).pack(side=tk.LEFT)
        
        if entry.get('examples'):
            ttk.Label(frame, text="Examples:", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(5, 2))
            for example in entry['examples']:
                ex_frame = ttk.Frame(frame)
                ex_frame.pack(fill=tk.X, pady=2)
                
                if isinstance(example, str):
                    command = example
                    description = None
                else:
                    command = example.get('command', '')
                    description = example.get('description', None)
                
                ex_text = tk.Text(ex_frame, height=1, wrap=tk.NONE, font=('Courier', 8), bg='#f9f9f9')
                ex_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                ex_text.insert('1.0', command)
                ex_text.config(state=tk.DISABLED)
                
                ttk.Button(ex_frame, text="Copy", width=6, command=lambda c=command: self.core.copy_to_clipboard(self.root, c)).pack(side=tk.LEFT)
                
                if description:
                    desc_frame = ttk.Frame(frame)
                    desc_frame.pack(fill=tk.X, pady=(0, 2))
                    ttk.Label(desc_frame, text=f"  → {description}", font=('Arial', 8), foreground='#555', wraplength=680).pack(anchor=tk.W, padx=(10, 0))
        
        if entry.get('details'):
            details_btn = ttk.Button(frame, text="Show Details", command=lambda: self.show_details(entry))
            details_btn.pack(anchor=tk.W, pady=(5, 0))
        
        if entry.get('notes'):
            notes_label = ttk.Label(frame, text=f"Note: {entry['notes']}", wraplength=700, foreground='#666')
            notes_label.pack(anchor=tk.W, pady=(5, 0))
    
    def create_entry_widget_popup(self, entry, parent):
        """Smaller version of entry widget for popup results."""
        frame = ttk.LabelFrame(parent, text=entry.get('name',''), padding=10)
        frame.pack(fill=tk.X, pady=8)

        ttk.Label(frame, text=entry.get('description',''), wraplength=750).pack(anchor=tk.W)

        if entry.get('examples'):
            ttk.Label(frame, text="Examples:", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(5, 2))
            for ex in entry['examples']:
                if isinstance(ex, str):
                    cmd = ex
                else:
                    cmd = ex.get('command', '')

                row = ttk.Frame(frame)
                row.pack(fill=tk.X, pady=1)
                txt = tk.Text(row, height=1, wrap=tk.NONE, font=('Courier', 8), bg='#f9f9f9')
                txt.insert('1.0', cmd)
                txt.config(state=tk.DISABLED)
                txt.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                ttk.Button(row, text="Copy", command=lambda c=cmd: self.core.copy_to_clipboard(self.root, c)).pack(side=tk.LEFT)
    
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
        """Fast search inside current category only."""
        self.display_entries(from_category=False)
    
    def open_gui_editor(self):
        """Open GUI sysmanual editor"""
        # Pass the current framework instance to the editor
        editor = SysManualGUIEditor(self.root, self)
    
    def open_advanced_search(self):
        """Open the advanced cross-category search popup."""
        popup = tk.Toplevel(self.root)
        popup.title("Advanced Search (Across All Categories)")
        popup.geometry("900x700")
        popup.resizable(True, True)

        query_var = tk.StringVar()
        ttk.Label(popup, text="Search Across All Categories:", font=('Arial', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10,4))
        entry = ttk.Entry(popup, textvariable=query_var, width=50)
        entry.pack(padx=10, pady=(0,10), anchor=tk.W)

        results_frame = ttk.Frame(popup)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        results_canvas = tk.Canvas(results_frame)
        results_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=results_canvas.yview)
        container = ttk.Frame(results_canvas)

        container.bind("<Configure>", lambda e: results_canvas.configure(scrollregion=results_canvas.bbox("all")))
        results_canvas.create_window((0, 0), window=container, anchor="nw")
        results_canvas.configure(yscrollcommand=results_scroll.set)

        results_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        def run_advanced_search(event=None):
            for w in container.winfo_children():
                w.destroy()

            query = query_var.get().strip()
            if not query:
                return

            sysmanual = self.sysmanuals.get(self.current_sysmanual)
            if not sysmanual:
                return

            for category in sysmanual['categories']:
                entries = category.get('entries', [])
                # Use the searcher from the core module
                matches = self.searcher.search_entries_in_category(entries, query, min_score=0.15) 

                if not matches:
                    continue

                header = ttk.Label(
                    container,
                    text=f"=== {category['name']} ===",
                    font=('Arial', 12, 'bold'),
                    foreground="#444"
                )
                header.pack(anchor=tk.W, pady=(10, 3))

                for entry_item in matches:
                    self.create_entry_widget_popup(entry_item, container)

        ttk.Button(popup, text="Search", command=run_advanced_search).pack(anchor=tk.W, padx=10)
        entry.bind('<Return>', run_advanced_search)


def main():
    root = tk.Tk()
    app = SysManualFramework(root)
    root.mainloop()

if __name__ == "__main__":
    main()
