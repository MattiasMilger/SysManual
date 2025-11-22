# sysmanual_editor.py (Canvas/Frame layout fix applied previously)

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
from pathlib import Path
from typing import List, Tuple
import copy
import re

# Import the core utilities
from sysmanual_core import SysManualCore 

class SysManualGUIEditor:
    def __init__(self, parent, framework):
        self.framework = framework
        self.core = framework.core # Access the SysManualCore instance
        self.window = tk.Toplevel(parent)
        self.window.title("SysManual GUI Editor")
        self.window.geometry("1400x900")
        
        self.current_sysmanual = None
        self.editing_item = None
        
        main_container = ttk.Frame(self.window)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        self.setup_toolbar()
        
        paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        self.setup_tree(left_frame)
        
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)
        self.setup_edit_panel(right_frame)
        
        if framework.current_sysmanual:
            self.load_sysmanual(framework.current_sysmanual)
            
    def _create_context_menu(self, widget, content_to_copy):
        """Creates a right-click context menu for copying, primarily for text fields."""
        # This calls the method in sysmanual_core.py, which now has the 'ttk' import.
        return self.core.create_context_menu_for_editor(self.window, widget, content_to_copy)

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
        
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set)
        self.tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Button-3>', self.show_context_menu)
    
    def setup_edit_panel(self, parent):
        # 1. Create Canvas and Scrollbar
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        
        # 2. Create the inner frame that will hold the widgets
        self.edit_frame = ttk.Frame(canvas)
        
        # 3. Define the configuration function for the inner frame
        def on_edit_frame_configure(event):
            # This adjusts the scroll region to encompass all inner frame contents
            canvas.configure(scrollregion=canvas.bbox("all"))

        # 4. Define the configuration function for the canvas itself
        def on_canvas_configure(event):
            # CRITICAL FIX (PREVIOUSLY APPLIED): Ensure the inner frame (the window) always matches the canvas's width
            # This prevents widgets from packing off-screen horizontally
            canvas.itemconfig(self.canvas_window, width=event.width)
        
        # 5. Bind the inner frame and the canvas
        self.edit_frame.bind("<Configure>", on_edit_frame_configure)
        canvas.bind('<Configure>', on_canvas_configure) # New binding for width control

        # 6. Place the inner frame inside the canvas, saving the window ID
        self.canvas_window = canvas.create_window((0, 0), window=self.edit_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 7. Pack everything
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mousewheel scrolling
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        
        for widget in [canvas, self.edit_frame, parent]:
            widget.bind("<MouseWheel>", on_mousewheel)
        
        ttk.Label(self.edit_frame, text="Select an item to edit", 
                 font=('Arial', 12)).pack(pady=20)
    
    def new_sysmanual(self):
        if self.current_sysmanual and messagebox.askyesno("New SysManual", 
            "Create new sysmanual? Unsaved changes will be lost."):
            self.current_sysmanual = None
            self.tree.delete(*self.tree.get_children())
            self.clear_edit_panel()
        
        template = {
            "id": "new-sysmanual",
            "name": "New SysManual",
            "description": "Description",
            "theme": {"primary": "#4CAF50", "accent": "#2196F3"},
            "categories": []
        }
        self.current_sysmanual = template
        self.populate_tree()
        
        # Check if there are children before trying to select
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self.on_tree_select(None)
    
    def open_file(self):
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
        if sysmanual_id in self.framework.sysmanuals:
            # Use deepcopy to prevent editing the framework's live data
            self.current_sysmanual = copy.deepcopy(self.framework.sysmanuals[sysmanual_id])
            self.populate_tree()
    
    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        
        if not self.current_sysmanual:
            return
        
        root = self.tree.insert('', 'end', text=f"📘 {self.current_sysmanual['name']}", 
                               values=('sysmanual',), open=True)
        
        for cat_idx, category in enumerate(self.current_sysmanual.get('categories', [])):
            cat_node = self.tree.insert(root, 'end', text=f"📁 {category['name']}", 
                                       values=('category', cat_idx), open=True)
            
            for entry_idx, entry in enumerate(category.get('entries', [])):
                self.tree.insert(cat_node, 'end', text=f"📄 {entry['name']}", 
                               values=('entry', cat_idx, entry_idx))
        
        self.window.lift()
        self.window.focus_force()
    
    def on_tree_select(self, event):
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
        for widget in self.edit_frame.winfo_children():
            widget.destroy()
    
    # --- Edit Panel Creators ---

    def create_field(self, label, data_dict, key, parent=None):
        if parent is None:
            parent = self.edit_frame
        
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame, text=label, width=15).pack(side=tk.LEFT)
        
        var = tk.StringVar(value=data_dict.get(key, ''))
        entry = ttk.Entry(frame, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        var.trace('w', lambda *args: data_dict.update({key: var.get()}))
        
        # Add right-click copy (This calls the fixed core method)
        self._create_context_menu(entry, var.get())
        
        return entry
    
    def create_text_field(self, label, data_dict, key, height=5, parent=None):
        if parent is None:
            parent = self.edit_frame
        
        frame = ttk.LabelFrame(parent, text=label, padding=5)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        text = tk.Text(frame, height=height, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert('1.0', data_dict.get(key, ''))
        
        def update_text(*args):
            data_dict[key] = text.get('1.0', 'end-1c')
        
        text.bind('<KeyRelease>', update_text)
        
        # Add right-click copy
        self._create_context_menu(text, data_dict.get(key, ''))

        return text

    def create_content_row(self, parent, entry, key):
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
        
        def update_content(*args):
            new_key = key_var.get()
            # Ensure we only perform the delete/re-add if the key has actually changed.
            if new_key != key and key in entry['content']:
                value_to_save = entry['content'].pop(key)
                entry['content'][new_key] = value_to_save
                # NOTE: This dynamic re-keying is tricky in Tkinter as the lambda
                # is bound to the *original* key variable. For full correctness 
                # after a key change, the entire editor would need to be reloaded 
                # or a more complex rebinding scheme used. For simplicity, we rely 
                # on the dictionary structure for saving.
            else:
                entry['content'][new_key] = value_var.get()
        
        key_var.trace('w', update_content)
        value_var.trace('w', update_content)
        
        # Add right-click copy for the Content fields
        self._create_context_menu(key_entry, key_var.get())
        self._create_context_menu(value_entry, value_var.get())
        
        # Using lambda to pass 'key' for proper deletion (based on current key)
        ttk.Button(frame, text="×", width=3, 
                  command=lambda k=key, f=frame: self.remove_content(parent, entry, k, f)).pack(side=tk.LEFT)

    # --- Editor Displays ---

    def show_sysmanual_editor(self):
        self.clear_edit_panel()
        
        ttk.Label(self.edit_frame, text="SysManual Settings", 
                 font=('Arial', 14, 'bold')).pack(anchor=tk.W, pady=(10, 20), padx=10)
        
        self.create_field("ID:", self.current_sysmanual, 'id')
        self.create_field("Name:", self.current_sysmanual, 'name')
        self.create_text_field("Description:", self.current_sysmanual, 'description', height=3)
    
    def show_category_editor(self, cat_idx):
        self.clear_edit_panel()
        
        category = self.current_sysmanual['categories'][cat_idx]
        
        ttk.Label(self.edit_frame, text="Category Settings", 
                 font=('Arial', 14, 'bold')).pack(anchor=tk.W, pady=(10, 20), padx=10)
        
        self.create_field("ID:", category, 'id')
        self.create_field("Name:", category, 'name')
        
        ttk.Button(self.edit_frame, text="+ Add Entry", 
                  command=lambda: self.add_entry(cat_idx)).pack(anchor=tk.W, padx=10, pady=10)
    
    def show_entry_editor(self, cat_idx, entry_idx):
        self.clear_edit_panel()
        
        category = self.current_sysmanual['categories'][cat_idx]
        entry = category['entries'][entry_idx]
        
        ttk.Label(self.edit_frame, text="Entry Editor", 
                 font=('Arial', 14, 'bold')).pack(anchor=tk.W, pady=(10, 20), padx=10)
        
        self.create_field("ID:", entry, 'id')
        self.create_field("Name:", entry, 'name')
        self.create_text_field("Description:", entry, 'description', height=3)
        
        # Content
        content_frame = ttk.LabelFrame(self.edit_frame, text="Content", padding=10)
        content_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        if 'content' not in entry: entry['content'] = {}
        for key in list(entry['content'].keys()):
            self.create_content_row(content_frame, entry, key)
        ttk.Button(content_frame, text="+ Add Content Field", 
                  command=lambda: self.add_content_field(content_frame, entry)).pack(anchor=tk.W, pady=5)
        
        # Examples
        examples_frame = ttk.LabelFrame(self.edit_frame, text="Examples", padding=10)
        examples_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        if 'examples' not in entry: entry['examples'] = []
        for idx, example in enumerate(entry['examples']):
            self.create_example_row(examples_frame, entry, idx)
        ttk.Button(examples_frame, text="+ Add Example", 
                  command=lambda: self.add_example(examples_frame, entry)).pack(anchor=tk.W, pady=5)
        
        # Details
        details_frame = ttk.LabelFrame(self.edit_frame, text="Details", padding=10)
        details_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        if 'details' not in entry: entry['details'] = []
        for idx, detail in enumerate(entry['details']):
            self.create_detail_row(details_frame, entry, idx)
        ttk.Button(details_frame, text="+ Add Detail", 
                  command=lambda: self.add_detail(details_frame, entry)).pack(anchor=tk.W, pady=5)
        
        # Notes
        self.create_text_field("Notes:", entry, 'notes', height=3)
        
    # --- Item Manipulators (Add/Remove) ---
        
    def add_content_field(self, parent, entry):
        key = f"field_{len(entry['content']) + 1}"
        entry['content'][key] = ""
        self.create_content_row(parent, entry, key)
    
    def remove_content(self, parent, entry, key_to_delete, frame):
        # Delete based on key or value if key was renamed
        if key_to_delete in entry['content']:
            del entry['content'][key_to_delete]
        else:
             # Fallback if key was renamed but the old key is still referenced by the lambda
             for k, v in list(entry['content'].items()):
                 if v == entry['content'].get(key_to_delete):
                     del entry['content'][k]
                     break
        frame.destroy()

    def create_example_row(self, parent, entry, idx):
        frame = ttk.LabelFrame(parent, text=f"Example {idx + 1}", padding=5)
        frame.pack(fill=tk.X, pady=5)
        
        example = entry['examples'][idx]
        
        if isinstance(example, str):
            example = {"command": example, "description": ""}
            entry['examples'][idx] = example
        
        cmd_frame = ttk.Frame(frame); cmd_frame.pack(fill=tk.X, pady=2)
        ttk.Label(cmd_frame, text="Command:").pack(side=tk.LEFT)
        cmd_var = tk.StringVar(value=example.get('command', ''))
        cmd_entry = ttk.Entry(cmd_frame, textvariable=cmd_var)
        cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        cmd_var.trace('w', lambda *args: example.update({'command': cmd_var.get()}))
        self._create_context_menu(cmd_entry, cmd_var.get())
        
        desc_frame = ttk.Frame(frame); desc_frame.pack(fill=tk.X, pady=2)
        ttk.Label(desc_frame, text="Description:").pack(side=tk.LEFT)
        desc_var = tk.StringVar(value=example.get('description', ''))
        desc_entry = ttk.Entry(desc_frame, textvariable=desc_var)
        desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        desc_var.trace('w', lambda *args: example.update({'description': desc_var.get()}))
        self._create_context_menu(desc_entry, desc_var.get())
        
        # Using lambda to capture the current frame and index for removal
        ttk.Button(frame, text="Remove Example", 
                  command=lambda p=parent, e=entry, i=idx, f=frame: self.remove_example(p, e, i, f)).pack(anchor=tk.E, pady=2)
    
    def add_example(self, parent, entry):
        entry['examples'].append({"command": "", "description": ""})
        # Re-draw the examples to ensure idx is correct
        for widget in parent.winfo_children():
            if isinstance(widget, ttk.LabelFrame): # Only destroy dynamic example label frames
                widget.destroy()
        for i, example in enumerate(entry['examples']):
            self.create_example_row(parent, entry, i)
    
    def remove_example(self, parent, entry, idx, frame):
        if idx < len(entry['examples']):
            entry['examples'].pop(idx)
        frame.destroy()
        # Re-draw the examples to ensure idx is correct
        for widget in parent.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                widget.destroy()
        for i, example in enumerate(entry['examples']):
            self.create_example_row(parent, entry, i)
    
    def create_detail_row(self, parent, entry, idx):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        detail = entry['details'][idx]
        
        ttk.Label(frame, text="Label:").pack(side=tk.LEFT)
        label_var = tk.StringVar(value=detail.get('label', ''))
        label_entry = ttk.Entry(frame, textvariable=label_var, width=20)
        label_entry.pack(side=tk.LEFT, padx=5)
        label_var.trace('w', lambda *args: detail.update({'label': label_var.get()}))
        self._create_context_menu(label_entry, label_var.get())

        
        ttk.Label(frame, text="Value:").pack(side=tk.LEFT)
        value_var = tk.StringVar(value=detail.get('value', ''))
        value_entry = ttk.Entry(frame, textvariable=value_var)
        value_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        value_var.trace('w', lambda *args: detail.update({'value': value_var.get()}))
        self._create_context_menu(value_entry, value_var.get())

        
        ttk.Button(frame, text="×", width=3,
                  command=lambda p=parent, e=entry, i=idx, f=frame: self.remove_detail(p, e, i, f)).pack(side=tk.LEFT)
    
    def add_detail(self, parent, entry):
        entry['details'].append({"label": "", "value": ""})
        # Re-create the new row only
        self.create_detail_row(parent, entry, len(entry['details']) - 1)
    
    def remove_detail(self, parent, entry, idx, frame):
        if idx < len(entry['details']):
            entry['details'].pop(idx)
        frame.destroy()

        # Re-draw all details to fix indexing (optional but cleaner)
        for w in parent.winfo_children():
            if isinstance(w, ttk.Frame) and w != parent.winfo_children()[-1]: # Don't destroy the Add button
                 w.destroy()
        for i, detail in enumerate(entry['details']):
            self.create_detail_row(parent, entry, i)
    
    # --- Duplication Methods ---
    
    def duplicate_category(self, cat_idx: int):
        if not self.current_sysmanual:
            return

        categories = self.current_sysmanual['categories']
        original_category = categories[cat_idx]
        
        existing_cat_ids = [c['id'] for c in categories]
        all_entry_ids = self.core.get_all_entry_ids(self.current_sysmanual)

        # Use the core utility for deep copy and ID/Name processing
        new_category = self.core.process_duplicated_category(original_category, existing_cat_ids, all_entry_ids)
        
        # Insert the new category right after the original
        categories.insert(cat_idx + 1, new_category)
        
        self.populate_tree()
        
        # Select the newly created category (index increases by 1)
        self.select_item_after_move('category', ('category', cat_idx), 1)

    def duplicate_entry(self, cat_idx: int, entry_idx: int):
        if not self.current_sysmanual:
            return
        
        category = self.current_sysmanual['categories'][cat_idx]
        entries = category['entries']
        original_entry = entries[entry_idx]

        all_entry_ids = self.core.get_all_entry_ids(self.current_sysmanual)
        
        # Use the core utility for deep copy and ID/Name processing
        new_entry = self.core.process_duplicated_entry(original_entry, all_entry_ids)

        # Insert the new entry right after the original
        entries.insert(entry_idx + 1, new_entry)
        
        self.populate_tree()
        
        # Select the newly created entry (entry index increases by 1)
        self.select_item_after_move('entry', ('entry', cat_idx, entry_idx), 1)

    # --- Tree/Data Manipulators (Move/Delete/Context) ---

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        self.tree.selection_set(item)
        values = self.tree.item(item, 'values')
        
        context_menu = tk.Menu(self.tree, tearoff=0)
        
        if not values or values[0] == 'sysmanual':
            context_menu.add_command(label="Add Category", command=self.add_category)
        elif values[0] == 'category':
            cat_idx = int(values[1])
            context_menu.add_command(label="Add Entry", command=lambda: self.add_entry(cat_idx))
            context_menu.add_command(label="Duplicate Category", command=lambda: self.duplicate_category(cat_idx))
            context_menu.add_separator()
            context_menu.add_command(label="Move Up ↑", command=self.move_item_up)
            context_menu.add_command(label="Move Down ↓", command=self.move_item_down)
            context_menu.add_separator()
            context_menu.add_command(label="Delete Category", command=self.delete_item)
        elif values[0] == 'entry':
            cat_idx = int(values[1])
            entry_idx = int(values[2])
            context_menu.add_command(label="Duplicate Entry", command=lambda: self.duplicate_entry(cat_idx, entry_idx))
            context_menu.add_separator()
            context_menu.add_command(label="Move Up ↑", command=self.move_item_up)
            context_menu.add_command(label="Move Down ↓", command=self.move_item_down)
            context_menu.add_separator()
            context_menu.add_command(label="Delete Entry", command=self.delete_item)
        
        context_menu.post(event.x_root, event.y_root)
    
    def add_category(self):
        if not self.current_sysmanual:
            return
        
        existing_cat_ids = [c['id'] for c in self.current_sysmanual['categories']]
        base_id = "new-category"
        base_name = "New Category"
        
        new_name, new_id = self.core.get_unique_name_and_id(base_name, base_id, existing_cat_ids)
        
        category = {
            "id": new_id,
            "name": new_name,
            "entries": []
        }
        self.current_sysmanual['categories'].append(category)
        self.populate_tree()
    
    def add_entry(self, cat_idx=None):
        if not self.current_sysmanual:
            return
        
        if cat_idx is None:
            selection = self.tree.selection()
            if not selection:
                return
            
            values = self.tree.item(selection[0], 'values')
            if not values or values[0] not in ['category', 'entry']:
                return
            
            cat_idx = int(values[1])
        
        category = self.current_sysmanual['categories'][cat_idx]
        entries = category['entries']
        
        # Get existing entry IDs for safe creation (across all categories)
        all_entry_ids = self.core.get_all_entry_ids(self.current_sysmanual)
        
        base_id = "new-entry"
        base_name = "New Entry"
        
        new_name, new_id = self.core.get_unique_name_and_id(base_name, base_id, all_entry_ids)

        entry = {
            "id": new_id,
            "name": new_name,
            "description": "Description",
            "content": {},
            "examples": [],
            "details": [],
            "notes": ""
        }
        entries.append(entry)
        self.populate_tree()
    
    def delete_item(self):
        selection = self.tree.selection()
        if not selection: return
        
        values = self.tree.item(selection[0], 'values')
        if not values: return
        
        item_type = values[0]
        
        if item_type == 'sysmanual': return
        
        if not messagebox.askyesno("Confirm Delete", f"Delete this {item_type}?"):
            self.window.lift(); self.window.focus_force(); return
        
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
        selection = self.tree.selection()
        if not selection: return
        
        values = self.tree.item(selection[0], 'values')
        if not values: return
        
        item_type = values[0]
        
        if item_type == 'sysmanual': return
        
        if item_type == 'category':
            cat_idx = int(values[1])
            if cat_idx == 0: return
            
            categories = self.current_sysmanual['categories']
            categories[cat_idx], categories[cat_idx - 1] = categories[cat_idx - 1], categories[cat_idx]
            
        elif item_type == 'entry':
            cat_idx = int(values[1])
            entry_idx = int(values[2])
            if entry_idx == 0: return
            
            entries = self.current_sysmanual['categories'][cat_idx]['entries']
            entries[entry_idx], entries[entry_idx - 1] = entries[entry_idx - 1], entries[entry_idx]
        
        self.populate_tree()
        self.select_item_after_move(item_type, values, -1)
    
    def move_item_down(self):
        selection = self.tree.selection()
        if not selection: return
        
        values = self.tree.item(selection[0], 'values')
        if not values: return
        
        item_type = values[0]
        
        if item_type == 'sysmanual': return
        
        if item_type == 'category':
            cat_idx = int(values[1])
            categories = self.current_sysmanual['categories']
            if cat_idx >= len(categories) - 1: return
            
            categories[cat_idx], categories[cat_idx + 1] = categories[cat_idx + 1], categories[cat_idx]
            
        elif item_type == 'entry':
            cat_idx = int(values[1])
            entry_idx = int(values[2])
            entries = self.current_sysmanual['categories'][cat_idx]['entries']
            if entry_idx >= len(entries) - 1: return
            
            entries[entry_idx], entries[entry_idx + 1] = entries[entry_idx + 1], entries[entry_idx]
        
        self.populate_tree()
        self.select_item_after_move(item_type, values, 1)
    
    def select_item_after_move(self, item_type, old_values, direction):
        if item_type == 'category':
            new_idx = int(old_values[1]) + direction
            for item in self.tree.get_children(self.tree.get_children()[0]):
                if self.tree.item(item, 'values') == ('category', new_idx):
                    self.tree.selection_set(item)
                    self.tree.see(item)
                    break
        elif item_type == 'entry':
            cat_idx = int(old_values[1])
            new_entry_idx = int(old_values[2]) + direction
            root = self.tree.get_children()[0]
            categories = self.tree.get_children(root)
            if cat_idx < len(categories):
                cat_item = categories[cat_idx]
                for entry_item in self.tree.get_children(cat_item):
                    if self.tree.item(entry_item, 'values') == ('entry', cat_idx, new_entry_idx):
                        self.tree.selection_set(entry_item)
                        self.tree.see(entry_item)
                        break
    
    def save_sysmanual(self):
        if not self.current_sysmanual: return
        
        if not self.framework.validate_sysmanual(self.current_sysmanual):
            self.window.lift(); self.window.focus_force(); return
        
        editor_window = self.window
        
        filepath = filedialog.asksaveasfilename(
            title="Save SysManual",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=Path("sysmanuals") if Path("sysmanuals").exists() else Path.cwd(),
            initialfile=f"{self.current_sysmanual['id']}_sysmanual.json",
            parent=self.window
        )
        
        editor_window.lift(); editor_window.focus_force()
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.current_sysmanual, f, indent=2)
                
                # Reload the saved file into the main framework
                self.framework.load_sysmanual_file(filepath)
                # Update the load combobox
                self.load_combo['values'] = list(self.framework.sysmanuals.keys())
                
                editor_window.lift(); editor_window.focus_force()
                messagebox.showinfo("Success", f"SysManual saved to {Path(filepath).name}")
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save:\n{str(e)}")
                editor_window.lift(); editor_window.focus_force()