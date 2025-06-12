#!/usr/bin/env python3
"""
Semester operations management.
"""
import logging
import tkinter as tk
from tkinter import ttk, messagebox

logger = logging.getLogger("semester_manager")

class SemesterManager:
    """
    Manages semester data in the transcript.
    Provides interface between UI and data model.
    """
    
    def __init__(self, model):
        """
        Initialize the semester manager.
        
        Args:
            model: The transcript model to manage
        """
        self.model = model
    
    def get_semesters(self):
        """
        Get all semesters from the model.
        
        Returns:
            List of semester dictionaries
        """
        return self.model.semesters
    
    def get_current_semester(self):
        """
        Get the current semester.
        
        Returns:
            Current semester dictionary or None
        """
        return self.model.get_current_semester()
    
    def get_current_semester_index(self):
        """
        Get the index of the current semester.
        
        Returns:
            Current semester index
        """
        return self.model.current_semester_index
    
    def set_current_semester_index(self, index):
        """
        Set the current semester index.
        
        Args:
            index: New index
        """
        if index < len(self.model.semesters) and index >= 0:
            self.model.current_semester_index = index
    
    def add_semester(self):
        """
        Add a new semester.
        
        Returns:
            The newly added semester
        """
        return self.model.add_semester()
    
    def delete_semester(self, index=None):
        """
        Delete a semester.
        
        Args:
            index: Index of the semester to delete (defaults to current)
            
        Returns:
            True if successful
        """
        return self.model.delete_semester(index)
    
    def update_semester(self, index, data):
        """
        Update semester data.
        
        Args:
            index: Index of the semester to update
            data: Dictionary with semester data to update
            
        Returns:
            True if successful
        """
        return self.model.update_semester(index, data)
    
    def move_semester_up(self, index=None):
        """
        Move a semester up in the list.
        
        Args:
            index: Index of the semester to move (defaults to current)
            
        Returns:
            True if successful
        """
        return self.model.move_semester_up(index)
    
    def move_semester_down(self, index=None):
        """
        Move a semester down in the list.
        
        Args:
            index: Index of the semester to move (defaults to current)
            
        Returns:
            True if successful
        """
        return self.model.move_semester_down(index)
    
    def create_panel(self, parent, callback=None):
        """
        Create a semester navigation panel.
        
        Args:
            parent: Parent tkinter widget
            callback: Function to call when semester selection changes
            
        Returns:
            Semester panel widget
        """
        return SemesterPanel(parent, self, callback)

class SemesterPanel(ttk.LabelFrame):
    """Panel for navigating and managing semesters."""
    
    def __init__(self, parent, manager, callback=None):
        """
        Initialize the semester panel.
        
        Args:
            parent: Parent tkinter widget
            manager: SemesterManager instance
            callback: Function to call when semester selection changes
        """
        super().__init__(parent, text="Semesters", padding=10)
        self.manager = manager
        self.callback = callback
        
        # Create UI elements
        self.create_widgets()
        
        # Load initial data
        self.update_listbox()
    
    def create_widgets(self):
        """Create UI widgets for semester management."""
        # Semester list with scrollbar
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.semester_listbox = tk.Listbox(list_frame, height=10, selectmode=tk.SINGLE)
        self.semester_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.semester_listbox.bind('<<ListboxSelect>>', self.on_semester_select)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.semester_listbox.yview)
        self.semester_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Semester management buttons
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(nav_frame, text="Add Semester", command=self.add_semester).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="Edit Semester", command=self.edit_semester).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="Delete", command=self.delete_semester).pack(side=tk.LEFT, padx=2)
        
        # Semester reordering buttons
        reorder_frame = ttk.Frame(self)
        reorder_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(reorder_frame, text="Move Up ↑", command=self.move_semester_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(reorder_frame, text="Move Down ↓", command=self.move_semester_down).pack(side=tk.LEFT, padx=2)
    
    def update_listbox(self):
        """Update the semester listbox from the manager."""
        self.semester_listbox.delete(0, tk.END)
        
        for semester in self.manager.get_semesters():
            semester_name = semester.get("semester", "Unnamed Semester")
            self.semester_listbox.insert(tk.END, semester_name)
        
        # Select the current semester
        current_index = self.manager.get_current_semester_index()
        if current_index < self.semester_listbox.size():
            self.semester_listbox.selection_set(current_index)
    
    def on_semester_select(self, event):
        """Handle semester selection."""
        selection = self.semester_listbox.curselection()
        if selection:
            index = selection[0]
            self.manager.set_current_semester_index(index)
            
            # Call the callback
            if self.callback:
                self.callback()
    
    def add_semester(self):
        """Add a new semester."""
        self.manager.add_semester()
        self.update_listbox()
        
        # Select the new semester
        self.semester_listbox.selection_set(self.manager.get_current_semester_index())
        
        # Call the callback
        if self.callback:
            self.callback()
    
    def edit_semester(self):
        """Edit the current semester."""
        current_semester = self.manager.get_current_semester()
        if not current_semester:
            messagebox.showinfo("Info", "No semester selected")
            return
        
        # Create a simple dialog to edit semester details
        dialog = tk.Toplevel(self)
        dialog.title("Edit Semester")
        dialog.transient(self)
        dialog.grab_set()
        
        # Create variables
        semester_type_var = tk.StringVar(value=current_semester.get("semester_type", ""))
        year_var = tk.StringVar(value=current_semester.get("year", ""))
        sem_gpa_var = tk.StringVar(value=str(current_semester.get("sem_gpa", "")))
        cum_gpa_var = tk.StringVar(value=str(current_semester.get("cum_gpa", "")))
        
        # Create form
        form_frame = ttk.Frame(dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Semester Type
        type_frame = ttk.Frame(form_frame)
        type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(type_frame, text="Semester Type:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Combobox(type_frame, textvariable=semester_type_var, 
                   values=["First", "Second", "Summer"]).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Year
        year_frame = ttk.Frame(form_frame)
        year_frame.pack(fill=tk.X, pady=5)
        ttk.Label(year_frame, text="Year:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(year_frame, textvariable=year_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # GPA info
        gpa_frame = ttk.Frame(form_frame)
        gpa_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(gpa_frame, text="Semester GPA:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(gpa_frame, textvariable=sem_gpa_var, width=8).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(gpa_frame, text="Cumulative GPA:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(gpa_frame, textvariable=cum_gpa_var, width=8).pack(side=tk.LEFT)
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def save_changes():
            data = {
                "semester_type": semester_type_var.get(),
                "year": year_var.get(),
                "sem_gpa": None,
                "cum_gpa": None
            }
            
            # Parse GPAs
            try:
                if sem_gpa_var.get():
                    data["sem_gpa"] = float(sem_gpa_var.get())
            except ValueError:
                pass
            
            try:
                if cum_gpa_var.get():
                    data["cum_gpa"] = float(cum_gpa_var.get())
            except ValueError:
                pass
            
            # Update semester
            self.manager.update_semester(self.manager.get_current_semester_index(), data)
            
            # Update UI
            self.update_listbox()
            
            # Call the callback
            if self.callback:
                self.callback()
            
            dialog.destroy()
        
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Save", command=save_changes).pack(side=tk.RIGHT, padx=5)
    
    def delete_semester(self):
        """Delete the current semester."""
        current_semester = self.manager.get_current_semester()
        if not current_semester:
            messagebox.showinfo("Info", "No semester selected")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this semester?"):
            self.manager.delete_semester()
            self.update_listbox()
            
            # Select the new current semester
            current_index = self.manager.get_current_semester_index()
            if current_index < self.semester_listbox.size():
                self.semester_listbox.selection_set(current_index)
            
            # Call the callback
            if self.callback:
                self.callback()
    
    def move_semester_up(self):
        """Move the current semester up in the list."""
        if self.manager.move_semester_up():
            self.update_listbox()
            
            # Select the moved semester
            current_index = self.manager.get_current_semester_index()
            self.semester_listbox.selection_set(current_index)
            
            # Call the callback
            if self.callback:
                self.callback()
    
    def move_semester_down(self):
        """Move the current semester down in the list."""
        if self.manager.move_semester_down():
            self.update_listbox()
            
            # Select the moved semester
            current_index = self.manager.get_current_semester_index()
            self.semester_listbox.selection_set(current_index)
            
            # Call the callback
            if self.callback:
                self.callback()
