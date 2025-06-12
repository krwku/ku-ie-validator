#!/usr/bin/env python3
"""
Common dialog components.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from utils.config import config

logger = logging.getLogger("dialogs")

class FormatSelectionDialog(tk.Toplevel):
    """Dialog for selecting report output format."""
    
    def __init__(self, parent, callback=None):
            super().__init__(parent)
            self.title("Select Report Format")
            self.geometry("400x250")
            self.transient(parent)
            self.grab_set()
            
            self.callback = callback
            
            # Main frame
            main_frame = ttk.Frame(self, padding=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            ttk.Label(main_frame, text="Choose report format:", font=("Arial", 10, "bold")).pack(pady=(0, 10))
            
            # Format selection
            self.format_var = tk.StringVar(value="text")
            ttk.Radiobutton(main_frame, text="Text File (.txt)", variable=self.format_var, value="text").pack(anchor=tk.W, pady=2)
            ttk.Radiobutton(main_frame, text="Excel File (.xlsx)", variable=self.format_var, value="excel").pack(anchor=tk.W, pady=2)
            
            # Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(20, 10))
            
            cancel_btn = tk.Button(button_frame, text="Cancel", 
                                  command=self.cancel, 
                                  width=12, height=2,
                                  font=("Arial", 10))
            cancel_btn.pack(side=tk.RIGHT, padx=8, pady=5)
            
            ok_btn = tk.Button(button_frame, text="OK", 
                              command=self.ok, 
                              width=12, height=2,
                              font=("Arial", 10))
            ok_btn.pack(side=tk.RIGHT, padx=8, pady=5)
            
            # Center window with CORRECT size
            self.update_idletasks()
            width = 400
            height = 250
            x = (self.winfo_screenwidth() // 2) - (width // 2)
            y = (self.winfo_screenheight() // 2) - (height // 2)
            self.geometry(f"{width}x{height}+{x}+{y}")
    
    def ok(self):
        if self.callback:
            self.callback(self.format_var.get())
        self.destroy()
    
    def cancel(self):
        if self.callback:
            self.callback(None)
        self.destroy()

class CourseDataSelectorDialog(tk.Toplevel):
    """Dialog for selecting a course data file."""
    
    def __init__(self, parent, callback=None):
        """
        Initialize the course data selector dialog.
        
        Args:
            parent: Parent tkinter widget
            callback: Function to call with selected file path
        """
        super().__init__(parent)
        self.title("Select Course Data")
        self.geometry("600x400")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)
        
        self.callback = callback
        self.selected_file_path = None
        
        # Create UI elements
        self.create_widgets()
        
        # Populate the list
        self.populate_course_data_list()
        
        # Center the dialog
        self.center_window()
    
    def create_widgets(self):
        """Create GUI widgets for the dialog."""
        # Main frame with padding
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and description
        ttk.Label(main_frame, 
                 text="Select Course Data Catalog", 
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        ttk.Label(main_frame, 
                 text="Choose the course catalog to use for validation:",
                 wraplength=550).pack(pady=(0, 10))
        
        # Course data list with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create columns for the treeview
        columns = ("filename", "description", "path")
        self.course_list = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        
        # Define column headings
        self.course_list.heading("filename", text="Filename")
        self.course_list.heading("description", text="Description")
        self.course_list.heading("path", text="Path")
        
        # Set column widths
        self.course_list.column("filename", width=150)
        self.course_list.column("description", width=300)
        self.course_list.column("path", width=150)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.course_list.yview)
        self.course_list.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.course_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add double-click binding
        self.course_list.bind("<Double-1>", lambda event: self.on_select())
        
        # Information about adding new files
        info_text = "Note: Place course data JSON files in the 'course_data' folder to make them available here."
        ttk.Label(main_frame, text=info_text, foreground="gray", wraplength=550).pack(pady=5)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Add New File button
        ttk.Button(button_frame, 
                  text="Add New File...", 
                  command=self.add_new_file).pack(side=tk.LEFT, padx=5)
        
        # Refresh button
        ttk.Button(button_frame, 
                  text="Refresh List", 
                  command=self.populate_course_data_list).pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        ttk.Button(button_frame, 
                  text="Cancel", 
                  command=self.cancel).pack(side=tk.RIGHT, padx=5)
        
        # Select button
        self.select_button = ttk.Button(button_frame, 
                                       text="Select", 
                                       command=self.on_select,
                                       state=tk.DISABLED)  # Initially disabled
        self.select_button.pack(side=tk.RIGHT, padx=5)
        
        # Enable select button when an item is selected
        self.course_list.bind("<<TreeviewSelect>>", self.on_item_selected)
    
    def on_item_selected(self, event):
        """Enable the select button when an item is selected."""
        selected_items = self.course_list.selection()
        if selected_items:
            self.select_button.config(state=tk.NORMAL)
        else:
            self.select_button.config(state=tk.DISABLED)
    
    def populate_course_data_list(self):
        """Populate the list with available course data files."""
        # Clear existing items
        for item in self.course_list.get_children():
            self.course_list.delete(item)
        
        # Get available files from the configuration
        files_list = config.get_available_course_data_files()
        
        # Add files to the treeview
        for file_info in files_list:
            self.course_list.insert("", "end", values=(
                file_info["filename"],
                file_info["description"],
                file_info["path"]
            ))
        
        # Select the first item if available
        if files_list:
            first_item = self.course_list.get_children()[0]
            self.course_list.selection_set(first_item)
            self.select_button.config(state=tk.NORMAL)
        else:
            # No files available, show a message
            messagebox.showinfo("No Course Data", 
                              "No course data files found. Please add JSON files to the 'course_data' folder.")
    
    def add_new_file(self):
        """Add a new course data file."""
        file_path = filedialog.askopenfilename(
            title="Select Course Data File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Get the filename
        file_name = os.path.basename(file_path)
        
        # Destination path
        dest_path = config.course_data_dir / file_name
        
        try:
            # Check if file already exists
            if dest_path.exists():
                overwrite = messagebox.askyesno(
                    "File Already Exists",
                    f"File {file_name} already exists in the course_data folder. Overwrite it?"
                )
                if not overwrite:
                    return
            
            # Copy the file
            import shutil
            shutil.copy2(file_path, dest_path)
            
            # Refresh the list
            self.populate_course_data_list()
            
            # Select the newly added file
            for item in self.course_list.get_children():
                if self.course_list.item(item)["values"][0] == file_name:
                    self.course_list.selection_set(item)
                    break
            
            messagebox.showinfo("File Added", f"Course data file {file_name} has been added.")
        
        except Exception as e:
            logger.error(f"Error adding course data file: {e}")
            messagebox.showerror("Error", f"Failed to add course data file: {e}")
    
    def on_select(self):
        """Handle selection of a course data file."""
        selected_items = self.course_list.selection()
        if not selected_items:
            return
        
        # Get the selected file path from the third column
        selected_item = selected_items[0]
        values = self.course_list.item(selected_item)["values"]
        self.selected_file_path = values[2]  # Path is in the third column
        
        # Call the callback if provided
        if self.callback:
            self.callback(self.selected_file_path)
        
        # Close the dialog
        self.destroy()
    
    def cancel(self):
        """Cancel selection and close the dialog."""
        self.selected_file_path = None
        
        # Call the callback with None if provided
        if self.callback:
            self.callback(None)
        
        # Close the dialog
        self.destroy()
    
    def center_window(self):
        """Center the window on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

class SemesterDetailsPanel(ttk.LabelFrame):
    """Panel for displaying and editing current semester details."""
    
    def __init__(self, parent, semester_manager, course_manager, callback=None):
        """
        Initialize the semester details panel.
        
        Args:
            parent: Parent tkinter widget
            semester_manager: SemesterManager instance
            course_manager: CourseManager instance
            callback: Function to call when semester data changes
        """
        super().__init__(parent, text="Current Semester", padding=10)
        self.semester_manager = semester_manager
        self.course_manager = course_manager
        self.callback = callback
        
        # Create semester detail variables
        self.semester_type_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self.sem_gpa_var = tk.StringVar()
        self.cum_gpa_var = tk.StringVar()
        self.total_credits_var = tk.StringVar()
        
        # Create UI elements
        self.create_widgets()
        
        # Update with current semester data
        self.update_from_manager()
    
    def create_widgets(self):
        """Create UI widgets for semester details."""
        # Semester details frame
        details_frame = ttk.Frame(self)
        details_frame.pack(fill=tk.X, pady=5)
        
        # Semester Type (First/Second/Summer)
        sem_type_frame = ttk.Frame(details_frame)
        sem_type_frame.pack(fill=tk.X, pady=2)
        ttk.Label(sem_type_frame, text="Semester Type:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Combobox(sem_type_frame, textvariable=self.semester_type_var, 
                    values=["First", "Second", "Summer"]).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Year
        year_frame = ttk.Frame(details_frame)
        year_frame.pack(fill=tk.X, pady=2)
        ttk.Label(year_frame, text="Year:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(year_frame, textvariable=self.year_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # GPA info
        gpa_frame = ttk.Frame(details_frame)
        gpa_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(gpa_frame, text="Semester GPA:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(gpa_frame, textvariable=self.sem_gpa_var, width=8).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(gpa_frame, text="Cumulative GPA:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(gpa_frame, textvariable=self.cum_gpa_var, width=8).pack(side=tk.LEFT)
        
        # Credits
        credits_frame = ttk.Frame(details_frame)
        credits_frame.pack(fill=tk.X, pady=2)
        ttk.Label(credits_frame, text="Total Credits:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(credits_frame, textvariable=self.total_credits_var, width=8, state="readonly").pack(side=tk.LEFT)
        
        # Apply button for semester changes
        ttk.Button(details_frame, text="Apply Changes", 
                 command=self.apply_changes).pack(pady=10)
    
    def update_from_manager(self):
        """Update UI with current semester data from the manager."""
        semester = self.semester_manager.get_current_semester()
        
        if not semester:
            # Clear UI if no semester selected
            self.semester_type_var.set("")
            self.year_var.set("")
            self.sem_gpa_var.set("")
            self.cum_gpa_var.set("")
            self.total_credits_var.set("")
            return
        
        # Update UI with semester data
        self.semester_type_var.set(semester.get("semester_type", ""))
        self.year_var.set(semester.get("year", ""))
        
        sem_gpa = semester.get("sem_gpa")
        cum_gpa = semester.get("cum_gpa")
        
        self.sem_gpa_var.set(str(sem_gpa) if sem_gpa is not None else "")
        self.cum_gpa_var.set(str(cum_gpa) if cum_gpa is not None else "")
        
        self.total_credits_var.set(str(semester.get("total_credits", 0)))
    
    def apply_changes(self):
        """Apply changes to the current semester."""
        # Get the current semester index
        semester_index = self.semester_manager.get_current_semester_index()
        
        # Create data dictionary from UI values
        data = {
            "semester_type": self.semester_type_var.get(),
            "year": self.year_var.get(),
            "sem_gpa": None,
            "cum_gpa": None
        }
        
        # Parse GPA values
        try:
            if self.sem_gpa_var.get():
                data["sem_gpa"] = float(self.sem_gpa_var.get())
        except ValueError:
            messagebox.showwarning("Warning", "Invalid semester GPA value")
        
        try:
            if self.cum_gpa_var.get():
                data["cum_gpa"] = float(self.cum_gpa_var.get())
        except ValueError:
            messagebox.showwarning("Warning", "Invalid cumulative GPA value")
        
        # Update the semester
        self.semester_manager.update_semester(semester_index, data)
        
        # Call the callback if provided
        if self.callback:
            self.callback()
