#!/usr/bin/env python3
"""
Course operations management.
"""
import re
import logging
import tkinter as tk
from tkinter import ttk, messagebox

logger = logging.getLogger("course_manager")

class CourseManager:
    """
    Manages course data in the transcript.
    Provides interface between UI and data model.
    """
    
    def __init__(self, model, course_data=None):
        """
        Initialize the course manager.
        
        Args:
            model: The transcript model to manage
            course_data: Dictionary with course information
        """
        self.model = model
        self.course_data = course_data or {}
        self.all_courses = self.course_data.get("all_courses", {})
    
    def set_course_data(self, course_data):
        """
        Set the course data.
        
        Args:
            course_data: Dictionary with course information
        """
        self.course_data = course_data or {}
        self.all_courses = self.course_data.get("all_courses", {})
    
    def get_course_info(self, course_code):
        """
        Get information about a course.
        
        Args:
            course_code: Course code to look up
            
        Returns:
            Dictionary with course information or None
        """
        return self.all_courses.get(course_code)
    
    def get_courses_for_semester(self, semester_index):
        """
        Get all courses for a semester.
        
        Args:
            semester_index: Index of the semester
            
        Returns:
            List of course dictionaries
        """
        if semester_index < len(self.model.semesters):
            return self.model.semesters[semester_index].get("courses", [])
        return []
    
    def add_course(self, semester_index, course_data):
        """
        Add a course to a semester.
        
        Args:
            semester_index: Index of the semester
            course_data: Dictionary with course data
            
        Returns:
            True if successful
        """
        return self.model.add_course(semester_index, course_data)
    
    def update_course(self, semester_index, course_index, course_data):
        """
        Update a course.
        
        Args:
            semester_index: Index of the semester
            course_index: Index of the course
            course_data: Dictionary with course data
            
        Returns:
            True if successful
        """
        return self.model.update_course(semester_index, course_index, course_data)
    
    def delete_course(self, semester_index, course_index):
        """
        Delete a course.
        
        Args:
            semester_index: Index of the semester
            course_index: Index of the course
            
        Returns:
            True if successful
        """
        return self.model.delete_course(semester_index, course_index)
    
    def move_course(self, src_semester_index, course_indices, dst_semester_index):
        """
        Move courses between semesters.
        
        Args:
            src_semester_index: Source semester index
            course_indices: List of course indices to move
            dst_semester_index: Destination semester index
            
        Returns:
            Number of courses moved
        """
        if src_semester_index >= len(self.model.semesters) or dst_semester_index >= len(self.model.semesters):
            return 0
        
        # Get source and destination semesters
        src_semester = self.model.semesters[src_semester_index]
        dst_semester = self.model.semesters[dst_semester_index]
        
        # Sort indices in reverse order to avoid shifting problems when removing
        sorted_indices = sorted(course_indices, reverse=True)
        
        # Move the courses
        moved_courses = []
        for idx in sorted_indices:
            if idx < len(src_semester.get("courses", [])):
                moved_courses.append(src_semester["courses"].pop(idx))
        
        # Add to destination semester in original order
        for course in reversed(moved_courses):
            dst_semester["courses"].append(course)
        
        # Recalculate credits for both semesters
        self.model.recalculate_semester_credits(src_semester_index)
        self.model.recalculate_semester_credits(dst_semester_index)
        
        self.model.set_changed()
        logger.info(f"Moved {len(moved_courses)} courses from semester {src_semester_index} to {dst_semester_index}")
        return len(moved_courses)
    
    def create_panel(self, parent, semester_manager):
        """
        Create a course management panel.
        
        Args:
            parent: Parent tkinter widget
            semester_manager: SemesterManager instance
            
        Returns:
            Course panel widget
        """
        return CoursePanel(parent, self, semester_manager)

class CoursePanel(ttk.LabelFrame):
    """Panel for managing courses in a semester."""
    
    def __init__(self, parent, manager, semester_manager):
        """
        Initialize the course panel.
        
        Args:
            parent: Parent tkinter widget
            manager: CourseManager instance
            semester_manager: SemesterManager instance
        """
        super().__init__(parent, text="Courses", padding=10)
        self.manager = manager
        self.semester_manager = semester_manager
        
        # Create UI elements
        self.create_widgets()
        
        # Load initial data
        self.update_course_list()
    
    def create_widgets(self):
        """Create UI widgets for course management."""
        # Treeview for courses with scrollbar
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("code", "name", "grade", "credits")
        self.courses_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10, selectmode="extended")
        
        # Define headings
        self.courses_tree.heading("code", text="Course Code")
        self.courses_tree.heading("name", text="Course Name")
        self.courses_tree.heading("grade", text="Grade")
        self.courses_tree.heading("credits", text="Credits")
        
        # Define columns
        self.courses_tree.column("code", width=100)
        self.courses_tree.column("name", width=300)
        self.courses_tree.column("grade", width=80)
        self.courses_tree.column("credits", width=80)
        
        self.courses_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.courses_tree.yview)
        self.courses_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Course buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Add Course", command=self.add_course).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Edit Course", command=self.edit_course).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Delete Course", command=self.delete_course).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Move Course", command=self.move_course_to_semester).pack(side=tk.LEFT, padx=2)
    
    def update_course_list(self):
        """Update the course treeview with data from the current semester."""
        # Clear the treeview
        for item in self.courses_tree.get_children():
            self.courses_tree.delete(item)
        
        # Get current semester index
        semester_index = self.semester_manager.get_current_semester_index()
        
        # Get courses for the current semester
        courses = self.manager.get_courses_for_semester(semester_index)
        
        # Add courses to the treeview
        for course in courses:
            self.courses_tree.insert("", tk.END, values=(
                course.get("code", ""),
                course.get("name", ""),
                course.get("grade", ""),
                course.get("credits", "")
            ))
    
    def add_course(self):
        """Add a new course to the current semester."""
        current_semester = self.semester_manager.get_current_semester()
        if not current_semester:
            messagebox.showinfo("Info", "No semester selected")
            return
        
        # Create course entry dialog
        self.open_course_dialog()
    
    def edit_course(self):
        """Edit the selected course."""
        selection = self.courses_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No course selected")
            return
        
        # Get selected course index
        item_id = selection[0]
        course_index = self.courses_tree.index(item_id)
        
        # Open course dialog with current data
        self.open_course_dialog(course_index)
    
    def delete_course(self):
        """Delete the selected course."""
        selection = self.courses_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No course selected")
            return
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this course?"):
            # Get selected course index
            item_id = selection[0]
            course_index = self.courses_tree.index(item_id)
            
            # Delete course
            semester_index = self.semester_manager.get_current_semester_index()
            if self.manager.delete_course(semester_index, course_index):
                # Update UI
                self.update_course_list()
    
    def move_course_to_semester(self):
        """Move selected courses to a different semester."""
        # Check if any courses are selected
        selection = self.courses_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No courses selected")
            return
        
        # Get the selected course indices
        selected_indices = [self.courses_tree.index(item_id) for item_id in selection]
        
        # Get the current semester index
        src_semester_index = self.semester_manager.get_current_semester_index()
        
        # Create dialog to select target semester
        dialog = tk.Toplevel(self)
        dialog.title("Move Courses to Semester")
        dialog.geometry("650x450")  # Increased size to ensure buttons are visible
        dialog.minsize(600, 400)    # Increased minimum size
        dialog.transient(self)
        dialog.grab_set()
        
        # Display course info
        info_frame = ttk.Frame(dialog, padding=10)
        info_frame.pack(fill=tk.X)
        
        # Get courses for display
        courses = self.manager.get_courses_for_semester(src_semester_index)
        selected_courses = [courses[idx] for idx in selected_indices if idx < len(courses)]
        
        num_courses = len(selected_courses)
        ttk.Label(info_frame, text=f"Selected {num_courses} course{'s' if num_courses > 1 else ''}:").pack(anchor=tk.W)
        
        # Show list of selected courses
        courses_text = tk.Text(info_frame, height=5, width=60, wrap=tk.WORD)
        courses_text.pack(fill=tk.X, pady=5)
        
        for course in selected_courses:
            courses_text.insert(tk.END, f"{course.get('code', '')} - {course.get('name', '')}\n")
        
        courses_text.config(state=tk.DISABLED)  # Make read-only
        
        current_semester = self.semester_manager.get_current_semester()
        ttk.Label(info_frame, text=f"From semester: {current_semester.get('semester', '')}").pack(anchor=tk.W)
        
        # Select target semester
        select_frame = ttk.LabelFrame(dialog, text="Select Target Semester", padding=10)
        select_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Listbox with semesters
        list_frame = ttk.Frame(select_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        semester_listbox = tk.Listbox(list_frame)
        semester_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=semester_listbox.yview)
        semester_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate with semesters other than the current one
        target_semester_indices = []  # To map listbox indices to actual semester indices
        semesters = self.semester_manager.get_semesters()
        for i, semester in enumerate(semesters):
            if i != src_semester_index:  # Skip current semester
                semester_listbox.insert(tk.END, semester.get("semester", ""))
                target_semester_indices.append(i)
        
        if semester_listbox.size() == 0:
            ttk.Label(select_frame, text="No other semesters available.").pack(pady=10)
        
        # Button frame
        button_frame = ttk.Frame(dialog, padding=(10, 5, 10, 10))  # Add more padding
        button_frame.pack(fill=tk.X, pady=10)
        
        def move_courses():
            # Get selected target semester
            selection = semester_listbox.curselection()
            if not selection:
                messagebox.showinfo("Info", "No target semester selected")
                return
            
            # Get the actual target semester index
            target_index = target_semester_indices[selection[0]]
            
            # Move the courses
            num_moved = self.manager.move_course(src_semester_index, selected_indices, target_index)
            
            # Update UI
            self.update_course_list()
            
            # Close dialog
            dialog.destroy()
            
            # Show confirmation message
            messagebox.showinfo("Success", 
                              f"{num_moved} course{'s' if num_moved > 1 else ''} moved to {semesters[target_index].get('semester', '')}")
        
        # Make the buttons larger and more visible
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy,
                 width=20, padding=(5, 5)).pack(side=tk.RIGHT, padx=10, pady=10)
        ttk.Button(button_frame, text="Move Courses", command=move_courses,
                 width=20, padding=(5, 5)).pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Center the dialog on the screen
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def open_course_dialog(self, course_index=None):
        """
        Open dialog to add or edit a course.
        
        Args:
            course_index: Index of the course to edit (None for new course)
        """
        # Create a new top-level window
        dialog = tk.Toplevel(self)
        dialog.title("Add Course" if course_index is None else "Edit Course")
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Create variables for course fields
        course_code_var = tk.StringVar()
        course_name_var = tk.StringVar()
        grade_var = tk.StringVar()
        credits_var = tk.StringVar()
        
        # If editing, populate with existing course data
        if course_index is not None:
            semester_index = self.semester_manager.get_current_semester_index()
            courses = self.manager.get_courses_for_semester(semester_index)
            if course_index < len(courses):
                course = courses[course_index]
                course_code_var.set(course.get("code", ""))
                course_name_var.set(course.get("name", ""))
                grade_var.set(course.get("grade", ""))
                credits_var.set(str(course.get("credits", "")))
        
        # Create form fields
        form_frame = ttk.Frame(dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Course code with lookup button
        code_frame = ttk.Frame(form_frame)
        code_frame.pack(fill=tk.X, pady=5)
        ttk.Label(code_frame, text="Course Code:").pack(side=tk.LEFT, padx=(0, 5))
        code_entry = ttk.Entry(code_frame, textvariable=course_code_var)
        code_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        lookup_button = ttk.Button(code_frame, text="Lookup", 
                                  command=lambda: self.lookup_course_code(course_code_var, course_name_var, credits_var))
        lookup_button.pack(side=tk.LEFT)
        
        # Course name
        name_frame = ttk.Frame(form_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="Course Name:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(name_frame, textvariable=course_name_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Grade with dropdown
        grade_frame = ttk.Frame(form_frame)
        grade_frame.pack(fill=tk.X, pady=5)
        ttk.Label(grade_frame, text="Grade:").pack(side=tk.LEFT, padx=(0, 5))
        grade_combo = ttk.Combobox(grade_frame, textvariable=grade_var, 
                                 values=["A", "B+", "B", "C+", "C", "D+", "D", "F", "W", "P", "N"])
        grade_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Credits
        credits_frame = ttk.Frame(form_frame)
        credits_frame.pack(fill=tk.X, pady=5)
        ttk.Label(credits_frame, text="Credits:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(credits_frame, textvariable=credits_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Course info display (from course data if available)
        info_frame = ttk.LabelFrame(form_frame, text="Course Information", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        course_info_text = tk.Text(info_frame, wrap=tk.WORD, height=8)
        course_info_text.pack(fill=tk.BOTH, expand=True)
        
        # Function to update course info display
        def update_course_info():
            code = course_code_var.get()
            course_info_text.delete(1.0, tk.END)
            
            course = self.manager.get_course_info(code)
            if course:
                course_name_var.set(course.get("name", ""))
                
                # Extract credits from format like "3(3-0-6)"
                credit_match = re.match(r'(\d+)\(', course.get("credits", ""))
                if credit_match:
                    credits_var.set(credit_match.group(1))
                
                # Display course info
                course_info_text.insert(tk.END, f"Name: {course.get('name', '')}\n")
                course_info_text.insert(tk.END, f"Credits: {course.get('credits', '')}\n")
                
                # Show prerequisites
                prereqs = course.get("prerequisites", [])
                if prereqs:
                    prereq_names = []
                    for prereq_code in prereqs:
                        prereq_course = self.manager.get_course_info(prereq_code)
                        if prereq_course:
                            prereq_names.append(f"{prereq_code} ({prereq_course.get('name', '')})")
                        else:
                            prereq_names.append(prereq_code)
                    
                    course_info_text.insert(tk.END, f"Prerequisites: {', '.join(prereq_names)}\n")
                else:
                    course_info_text.insert(tk.END, "Prerequisites: None\n")
                
                # Show corequisites
                coreqs = course.get("corequisites", [])
                if coreqs:
                    coreq_names = []
                    for coreq_code in coreqs:
                        coreq_course = self.manager.get_course_info(coreq_code)
                        if coreq_course:
                            coreq_names.append(f"{coreq_code} ({coreq_course.get('name', '')})")
                        else:
                            coreq_names.append(coreq_code)
                    
                    course_info_text.insert(tk.END, f"Corequisites: {', '.join(coreq_names)}\n")
        
        # Bind code entry to update course info
        course_code_var.trace("w", lambda *args: update_course_info())
        
        # Update initial display if editing
        if course_index is not None:
            update_course_info()
        
        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Save function
        def save_course():
            code = course_code_var.get()
            name = course_name_var.get()
            grade = grade_var.get()
            credits_str = credits_var.get()
            
            # Validate input
            if not code:
                messagebox.showerror("Error", "Course code is required")
                return
            
            if not name:
                messagebox.showerror("Error", "Course name is required")
                return
            
            try:
                credits = int(credits_str) if credits_str else 0
            except ValueError:
                messagebox.showerror("Error", "Credits must be a number")
                return
            
            # Create course object
            course = {
                "code": code,
                "name": name,
                "grade": grade,
                "credits": credits
            }
            
            # Add or update course
            semester_index = self.semester_manager.get_current_semester_index()
            
            if course_index is None:
                # Add new course
                self.manager.add_course(semester_index, course)
            else:
                # Update existing course
                self.manager.update_course(semester_index, course_index, course)
            
            # Update UI
            self.update_course_list()
            
            # Close dialog
            dialog.destroy()
        
        # Save/cancel buttons
        ttk.Button(button_frame, text="Save", command=save_course).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def lookup_course_code(self, code_var, name_var, credits_var):
        """
        Look up a course code and update fields.
        
        Args:
            code_var: StringVar for course code
            name_var: StringVar for course name
            credits_var: StringVar for credits
        """
        code = code_var.get()
        course = self.manager.get_course_info(code)
        
        if course:
            name_var.set(course.get("name", ""))
            
            # Extract credits from format like "3(3-0-6)"
            credit_match = re.match(r'(\d+)\(', course.get("credits", ""))
            if credit_match:
                credits_var.set(credit_match.group(1))
        else:
            messagebox.showinfo("Course Lookup", f"Course code {code} not found in course data.")
