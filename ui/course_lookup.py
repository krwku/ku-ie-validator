#!/usr/bin/env python3
"""
Course lookup dialog component.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger("course_lookup")

class CourseLookupDialog(tk.Toplevel):
    """Dialog for looking up courses in the course catalog."""
    
    def __init__(self, parent, course_manager, callback=None):
        """
        Initialize the course lookup dialog.
        
        Args:
            parent: Parent tkinter widget
            course_manager: CourseManager instance
            callback: Function to call with selected course code
        """
        super().__init__(parent)
        self.title("Course Lookup")
        self.geometry("800x600")
        self.transient(parent)
        self.grab_set()
        
        self.course_manager = course_manager
        self.callback = callback
        
        # Create UI elements
        self.create_widgets()
        
        # Populate the treeview
        self.populate_courses()
    
    def create_widgets(self):
        """Create UI widgets for the course lookup dialog."""
        # Search frame
        search_frame = ttk.Frame(self, padding=10)
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Bind search box to filter courses
        self.search_var.trace("w", lambda *args: self.populate_courses(self.search_var.get()))
        
        # Courses treeview
        tree_frame = ttk.Frame(self, padding=10)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("code", "name", "credits", "prerequisites")
        self.courses_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        # Define headings
        self.courses_tree.heading("code", text="Course Code")
        self.courses_tree.heading("name", text="Course Name")
        self.courses_tree.heading("credits", text="Credits")
        self.courses_tree.heading("prerequisites", text="Prerequisites")
        
        # Define columns
        self.courses_tree.column("code", width=100)
        self.courses_tree.column("name", width=300)
        self.courses_tree.column("credits", width=100)
        self.courses_tree.column("prerequisites", width=200)
        
        self.courses_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.courses_tree.yview)
        self.courses_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click to select a course
        self.courses_tree.bind("<Double-1>", self.on_course_select)
        
        # Button frame
        button_frame = ttk.Frame(self, padding=10)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Select", command=self.select_course).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
    
    def populate_courses(self, search_term=""):
        """
        Populate the treeview with course data, filtered by search term.
        
        Args:
            search_term: Term to filter courses by
        """
        # Clear existing items
        self.courses_tree.delete(*self.courses_tree.get_children())
        
        # Get all course data
        all_courses = self.course_manager.all_courses
        
        # Add each course to the treeview
        for code, course in all_courses.items():
            # Filter by search term if provided
            if search_term and search_term.lower() not in code.lower() and search_term.lower() not in course.get("name", "").lower():
                continue
            
            # Format prerequisites
            prereq_str = ", ".join(course.get("prerequisites", []))
            
            # Insert into treeview
            self.courses_tree.insert("", tk.END, values=(
                code,
                course.get("name", ""),
                course.get("credits", ""),
                prereq_str
            ))
    
    def on_course_select(self, event):
        """Handle double-click on a course in the treeview."""
        self.select_course()
    
    def select_course(self):
        """Select the current course and call the callback."""
        # Get selected item
        selection = self.courses_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No course selected")
            return
        
        # Get the course code
        item = self.courses_tree.item(selection[0])
        code = item["values"][0]
        
        # Call the callback if provided
        if self.callback:
            self.callback(code)
        
        # Close the dialog
        self.destroy()
