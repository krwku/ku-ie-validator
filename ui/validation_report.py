#!/usr/bin/env python3
"""
Validation report display component.
"""
import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger("validation_report")

class ValidationReportDialog(tk.Toplevel):
    """Dialog for displaying validation results."""
    
    def __init__(self, parent, report_text, validation_results):
        """
        Initialize the validation report dialog.
        
        Args:
            parent: Parent tkinter widget
            report_text: Formatted report text
            validation_results: List of validation result dictionaries
        """
        super().__init__(parent)
        self.title("Validation Report")
        self.geometry("900x700")
        self.transient(parent)
        self.grab_set()
        
        self.report_text = report_text
        self.validation_results = validation_results
        
        # Create UI elements
        self.create_widgets()
    
    def create_widgets(self):
        """Create UI widgets for the validation report dialog."""
        # Create main container
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook with tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Summary tab
        summary_frame = ttk.Frame(notebook, padding=10)
        notebook.add(summary_frame, text="Summary Report")
        
        # Report text with scrollbar
        report_frame = ttk.Frame(summary_frame)
        report_frame.pack(fill=tk.BOTH, expand=True)
        
        report_text = tk.Text(report_frame, wrap=tk.WORD)
        report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        report_text.insert(tk.END, self.report_text)
        report_text.config(state=tk.DISABLED)  # Make read-only
        
        scrollbar = ttk.Scrollbar(report_frame, orient="vertical", command=report_text.yview)
        report_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Detailed tab with all validation results
        details_frame = ttk.Frame(notebook, padding=10)
        notebook.add(details_frame, text="Detailed Results")
        
        # Create treeview for results
        columns = ("semester", "code", "name", "grade", "valid", "reason")
        results_tree = ttk.Treeview(details_frame, columns=columns, show="headings")
        
        # Define headings
        results_tree.heading("semester", text="Semester")
        results_tree.heading("code", text="Course Code")
        results_tree.heading("name", text="Course Name")
        results_tree.heading("grade", text="Grade")
        results_tree.heading("valid", text="Valid")
        results_tree.heading("reason", text="Reason")
        
        # Define columns
        results_tree.column("semester", width=100)
        results_tree.column("code", width=100)
        results_tree.column("name", width=200)
        results_tree.column("grade", width=50)
        results_tree.column("valid", width=50)
        results_tree.column("reason", width=300)
        
        results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=results_tree.yview)
        results_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate results tree
        for result in self.validation_results:
            is_valid = result.get("is_valid", True)
            
            # Set tag for row color
            tag = "valid" if is_valid else "invalid"
            
            results_tree.insert("", tk.END, values=(
                result.get("semester", ""),
                result.get("course_code", ""),
                result.get("course_name", ""),
                result.get("grade", ""),
                "Yes" if is_valid else "No",
                result.get("reason", "")
            ), tags=(tag,))
        
        # Configure tags for row colors
        results_tree.tag_configure("valid", background="white")
        results_tree.tag_configure("invalid", background="#ffcccc")
        
        # Close button
        ttk.Button(main_frame, text="Close", command=self.destroy).pack(pady=10)
