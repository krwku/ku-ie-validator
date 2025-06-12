#!/usr/bin/env python3
"""
Student information management.
"""
import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger("student_manager")

class StudentManager:
    """
    Manages student information in the transcript data.
    Provides interface between UI and data model.
    """
    
    def __init__(self, model):
        """
        Initialize the student manager.
        
        Args:
            model: The transcript model to manage
        """
        self.model = model
    
    def update_student_info(self, info):
        """
        Update student information in the model.
        
        Args:
            info: Dictionary with student information to update
            
        Returns:
            True if successful
        """
        # Update each field provided
        for key, value in info.items():
            self.model.student_info[key] = value
        
        self.model.set_changed()
        logger.info(f"Updated student info: {info}")
        return True
    
    def get_student_info(self):
        """
        Get student information from the model.
        
        Returns:
            Dictionary with student information
        """
        return self.model.student_info.copy()
    
    def create_panel(self, parent):
        """
        Create a student information panel.
        
        Args:
            parent: Parent tkinter widget
            
        Returns:
            Student panel widget
        """
        return StudentPanel(parent, self)

class StudentPanel(ttk.LabelFrame):
    """Panel for editing student information."""
    
    def __init__(self, parent, manager):
        """
        Initialize the student panel.
        
        Args:
            parent: Parent tkinter widget
            manager: StudentManager instance
        """
        super().__init__(parent, text="Student Information", padding=10)
        self.manager = manager
        
        # Create student information variables
        self.student_id_var = tk.StringVar()
        self.student_name_var = tk.StringVar()
        self.field_of_study_var = tk.StringVar()
        self.date_admission_var = tk.StringVar()
        
        # Create UI elements
        self.create_widgets()
        
        # Load initial data
        self.load_from_manager()
    
    def create_widgets(self):
        """Create UI widgets for student information."""
        # Student ID
        id_frame = ttk.Frame(self)
        id_frame.pack(fill=tk.X, pady=2)
        ttk.Label(id_frame, text="Student ID:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(id_frame, textvariable=self.student_id_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Student Name
        name_frame = ttk.Frame(self)
        name_frame.pack(fill=tk.X, pady=2)
        ttk.Label(name_frame, text="Name:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(name_frame, textvariable=self.student_name_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Field of Study
        field_frame = ttk.Frame(self)
        field_frame.pack(fill=tk.X, pady=2)
        ttk.Label(field_frame, text="Field of Study:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(field_frame, textvariable=self.field_of_study_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Date of Admission
        date_frame = ttk.Frame(self)
        date_frame.pack(fill=tk.X, pady=2)
        ttk.Label(date_frame, text="Date of Admission:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(date_frame, textvariable=self.date_admission_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Apply button
        ttk.Button(self, text="Apply Changes", command=self.apply_changes).pack(pady=10)
    
    def load_from_manager(self):
        """Load student information from the manager."""
        info = self.manager.get_student_info()
        
        self.student_id_var.set(info.get("id", ""))
        self.student_name_var.set(info.get("name", ""))
        self.field_of_study_var.set(info.get("field_of_study", ""))
        self.date_admission_var.set(info.get("date_admission", ""))
    
    def apply_changes(self):
        """Apply changes to the manager."""
        info = {
            "id": self.student_id_var.get(),
            "name": self.student_name_var.get(),
            "field_of_study": self.field_of_study_var.get(),
            "date_admission": self.date_admission_var.get()
        }
        
        self.manager.update_student_info(info)
