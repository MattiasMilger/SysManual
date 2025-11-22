# sysmanual_core.py

import tkinter as tk
from tkinter import ttk, messagebox # <-- FIX APPLIED HERE: Added ttk
import json
import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Set
import jsonschema
from jsonschema import validate
import copy

# Import schema
from sysmanual_schema import SYS_MANUAL_SCHEMA

class SysManualCore:
    """
    Contains core non-GUI business logic and low-level utilities.
    """
    def load_schema(self) -> dict:
        """Return the loaded JSON schema."""
        return SYS_MANUAL_SCHEMA

    def validate_sysmanual(self, sysmanual_data: dict, schema: dict) -> bool:
        """Validate sysmanual JSON against schema"""
        try:
            validate(instance=sysmanual_data, schema=schema)
            return True
        except jsonschema.exceptions.ValidationError as e:
            messagebox.showerror("Validation Error", f"Invalid sysmanual format:\n{e.message}")
            return False

    def copy_to_clipboard(self, root: tk.Tk, text: str):
        """Copy text to clipboard"""
        root.clipboard_clear()
        root.clipboard_append(text)
        messagebox.showinfo("Copied", "Copied to clipboard!")
        
    def create_context_menu_for_editor(self, root: tk.Toplevel, widget, content_to_copy: str) -> None:
        """Creates a right-click context menu for copying, primarily for text fields in the editor."""
        menu = tk.Menu(widget, tearoff=0)

        def copy_to_clipboard_full():
            # Use the latest content from the widget if possible, otherwise use the initial passed content
            try:
                if isinstance(widget, ttk.Entry):
                    current_content = widget.get()
                elif isinstance(widget, tk.Text):
                    current_content = widget.get('1.0', 'end-1c')
                else:
                    current_content = content_to_copy
            except Exception:
                current_content = content_to_copy
                
            self.copy_to_clipboard(root, current_content)
            
        def copy_selection():
            try:
                # Attempt to get selected text from Entry or Text widget
                if isinstance(widget, ttk.Entry):
                    selected = widget.selection_get()
                elif isinstance(widget, tk.Text):
                    selected = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                else:
                    return # Not a copyable widget type
                    
                if selected:
                    self.copy_to_clipboard(root, selected)
            except tk.TclError:
                # No selection, copy full content instead
                copy_to_clipboard_full()

        menu.add_command(label="Copy", command=copy_selection)
        menu.add_command(label="Copy All", command=copy_to_clipboard_full)

        def show_menu(event):
            try:
                # Ensure the selection is updated right before showing the menu
                if isinstance(widget, ttk.Entry):
                    widget.focus_set()
                elif isinstance(widget, tk.Text):
                    pass
                    
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        widget.bind("<Button-3>", show_menu)
        
        # Ensure 'Copy' command works on selection for Text/Entry widgets
        if isinstance(widget, (tk.Text, ttk.Entry)):
             widget.bind("<<Selection>>", lambda e: menu.entryconfig("Copy", command=copy_selection))
             widget.bind("<Button-1>", lambda e: menu.entryconfig("Copy", command=copy_selection))


    # --- ID/Name Generation Logic ---

    def get_all_entry_ids(self, sysmanual_data: dict) -> Set[str]:
        """Collects all entry IDs across all categories in the given sysmanual."""
        all_entry_ids = set()
        for cat in sysmanual_data.get('categories', []):
            for entry in cat.get('entries', []):
                all_entry_ids.add(entry['id'])
        return all_entry_ids

    def get_unique_name_and_id(self, original_name: str, original_id: str, existing_ids: List[str]) -> Tuple[str, str]:
        """Generates a new name and ID by appending a counter (e.g., (N) or _N) to avoid clashes."""
        
        def find_next_name_id(base_name, base_id, current_count):
            new_name = f"{base_name} ({current_count})"
            new_id = f"{base_id}_{current_count}"
            return new_name, new_id

        # Clean the original name and ID by removing existing (N) suffixes
        # Name pattern: "Name (N)" -> "Name"
        match_name = re.match(r"^(.*) \(\d+\)$", original_name)
        base_name = match_name.group(1).strip() if match_name else original_name.strip()
        
        # ID pattern: "id_N" -> "id"
        match_id = re.match(r"^(.*)_\d+$", original_id)
        base_id = match_id.group(1).strip() if match_id else original_id.strip()

        # Check if the base name/id is already in use
        if original_id not in existing_ids:
            return base_name, base_id

        i = 1
        while True:
            new_name, new_id = find_next_name_id(base_name, base_id, i)
            if new_id not in existing_ids:
                return new_name, new_id
            i += 1

    def process_duplicated_category(self, category_data: dict, existing_cat_ids: List[str], all_entry_ids: Set[str]) -> dict:
        """Deep copies a category and updates its ID, Name, and all child entry IDs/Names."""
        new_category = copy.deepcopy(category_data)
        
        # 1. Update Category ID/Name
        new_name, new_id = self.get_unique_name_and_id(new_category['name'], new_category['id'], existing_cat_ids)
        new_category['name'] = new_name
        new_category['id'] = new_id
        
        # 2. Update all child Entry IDs/Names
        # Convert set to list for existing_ids argument in get_unique_name_and_id
        current_entry_ids = list(all_entry_ids) 
        
        for entry in new_category.get('entries', []):
            # Need to prevent clashes with all existing entries, plus all entries already processed in the new category
            new_entry_name, new_entry_id = self.get_unique_name_and_id(entry['name'], entry['id'], current_entry_ids)
            entry['name'] = new_entry_name
            entry['id'] = new_entry_id
            current_entry_ids.append(new_entry_id) # Add the new ID to prevent clashes with subsequent entries
            
        return new_category

    def process_duplicated_entry(self, entry_data: dict, all_entry_ids: Set[str]) -> dict:
        """Deep copies an entry and updates its ID and Name."""
        new_entry = copy.deepcopy(entry_data)
        
        # Update Entry ID/Name
        new_name, new_id = self.get_unique_name_and_id(new_entry['name'], new_entry['id'], list(all_entry_ids))
        new_entry['name'] = new_name
        new_entry['id'] = new_id
        
        return new_entry


class SysManualSearch:
    """
    Contains all methods related to searching and scoring SysManual entries.
    """
    def tokenize(self, text: str) -> List[str]:
        """Split text into lowercase word tokens."""
        if not text:
            return []
        tokens = re.findall(r"\w+", text.lower())
        return tokens

    def best_match_score_for_token(self, token: str, text: str) -> float:
        """Return best match score in [0.0, 1.0] for token vs text."""
        if not token or not text:
            return 0.0
        token = token.lower()
        text_l = text.lower()
        
        if token == text_l:
            return 1.0
        if token in text_l:
            return 0.6
        
        words = re.findall(r"\w+", text_l)
        best = 0.0
        for w in words:
            if not w:
                continue
            if token == w:
                return 1.0
            if token in w or w in token:
                best = max(best, 0.7)
                continue
            ratio = SequenceMatcher(None, token, w).ratio()
            if ratio > best:
                best = ratio
        return best * 0.9

    def score_entry(self, entry: dict, tokens: List[str]) -> float:
        """Compute normalized relevance score for an entry given tokens."""
        if not tokens:
            return 1.0

        name_text = entry.get('name', '') or ''
        desc_text = entry.get('description', '') or ''
        content_val = ''
        if isinstance(entry.get('content'), dict):
            content_val = " ".join(str(v) for v in entry['content'].values())
        else:
            content_val = str(entry.get('content') or '')
        
        examples_val = ''
        if isinstance(entry.get('examples'), list):
            ex_parts = []
            for ex in entry['examples']:
                if isinstance(ex, str):
                    ex_parts.append(ex)
                elif isinstance(ex, dict):
                    ex_parts.append(str(ex.get('command', '')))
                    ex_parts.append(str(ex.get('description', '')))
            examples_val = " ".join(ex_parts)
        notes_text = entry.get('notes', '') or ''

        weights = {
            'name': 3.0,
            'description': 1.8,
            'content': 1.5,
            'examples': 1.2,
            'notes': 1.0
        }
        max_weight_sum = sum(weights.values())

        raw_score = 0.0
        for token in tokens:
            raw_score += self.best_match_score_for_token(token, name_text) * weights['name']
            raw_score += self.best_match_score_for_token(token, desc_text) * weights['description']
            raw_score += self.best_match_score_for_token(token, content_val) * weights['content']
            raw_score += self.best_match_score_for_token(token, examples_val) * weights['examples']
            raw_score += self.best_match_score_for_token(token, notes_text) * weights['notes']

        normalized = raw_score / (len(tokens) * max_weight_sum)
        return normalized

    def search_entries_in_category(self, entries: List[dict], query: str, min_score: float = 0.12) -> List[dict]:
        """Return entries matching query ordered by relevance."""
        query = (query or "").strip()
        if not query:
            return entries.copy()

        tokens = self.tokenize(query)
        if not tokens:
            return entries.copy()

        scored = []
        for entry in entries:
            score = self.score_entry(entry, tokens)
            if score >= min_score:
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for s, e in scored]