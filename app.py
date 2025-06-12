#!/usr/bin/env python3
"""
Main application for transcript data editing and validation.
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from pathlib import Path
import tempfile
import subprocess

# Import utilities
from utils.logger_setup import setup_logging
from utils.config import config
from utils.file_operations import save_transcript, load_transcript, load_course_data
from utils.pdf_extractor import PDFExtractor
from utils.validation_adapter import ValidationAdapter

# Import data models
from data.transcript_model import TranscriptModel
from data.student_manager import StudentManager
from data.semester_manager import SemesterManager
from data.course_manager import CourseManager

# Import UI components
from ui.dialogs import CourseDataSelectorDialog, SemesterDetailsPanel
from ui.course_lookup import CourseLookupDialog
from ui.pdf_extraction_dialog import PDFExtractionDialog
from ui.validation_report import ValidationReportDialog

# Set up logging
logger = logging.getLogger("transcript_editor")

class TranscriptEditorApp(tk.Tk):
    """Main application for transcript data editing and validation."""
    
    def __init__(self):
        """Initialize the application."""
        super().__init__()
        self.title("Transcript Data Editor")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        # Initialize data model
        self.model = TranscriptModel()
        
        # Initialize managers
        self.student_manager = StudentManager(self.model)
        self.semester_manager = SemesterManager(self.model)
        self.course_manager = CourseManager(self.model)
        self.pdf_extractor = PDFExtractor()
        
        # Find validator path and create validation adapter
        validator_path = self.find_validator_path()
        if validator_path:
            logger.info(f"Using validator path: {validator_path}")
            self.validation_adapter = ValidationAdapter(str(validator_path))
        else:
            logger.warning("Using default validator path - may not work correctly")
            self.validation_adapter = ValidationAdapter()
        
        # Set up the UI
        self.create_menu()
        self.create_widgets()
        
        # Set up status bar frame
        status_frame = ttk.Frame(self)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Dedication to Raphin P.
        dedication_label = ttk.Label(status_frame, 
                                  text="Created for Raphin P.",
                                  font=("Arial", 10, "italic"),
                                  foreground="#555555")
        dedication_label.pack(side=tk.RIGHT, padx=10)
        
        logger.info("Application initialized")
        self.report_status("Ready")
        
        # Schedule checking for course data after the UI is shown
        self.after(100, self.check_course_data)
    
    def find_validator_path(self):
        """Find the path to validator.py"""
        # Get the package root directory
        try:
            import pkg_resources
            package_root = Path(pkg_resources.resource_filename(__name__, ''))
            logger.info(f"Using package root: {package_root}")
        except (ImportError, pkg_resources.DistributionNotFound):
            package_root = Path(os.path.dirname(os.path.abspath(__file__)))
            logger.info(f"Using local directory as root: {package_root}")

        # Attempt to find validator.py in several possible locations
        potential_paths = [
            package_root / "validator.py",                   # Same directory
            package_root.parent / "validator.py",            # Parent directory
            package_root.parent.parent / "validator.py",     # Grandparent directory
            Path(sys.executable).parent / "validator.py",    # Python executable directory
        ]
        
        # Also search in site-packages directories
        site_packages = [Path(p) for p in sys.path if 'site-packages' in str(p)]
        for site_dir in site_packages:
            potential_paths.append(site_dir / "validator.py")
            potential_paths.append(site_dir / "course-registration-validator" / "validator.py")
            potential_paths.append(site_dir / "course_registration_validator" / "validator.py")
        
        # Try to find the validator file
        for path in potential_paths:
            if path.exists():
                logger.info(f"Found validator.py at: {path}")
                return path
                
        # If not found through paths, try to find it as a module
        for module_name in ["validator", "course-registration-validator.validator", "course_registration_validator.validator"]:
            try:
                spec = importlib.util.find_spec(module_name)
                if spec and spec.origin:
                    path = Path(spec.origin)
                    if path.exists():
                        logger.info(f"Found validator module at: {path}")
                        return path
            except (ImportError, ValueError, AttributeError):
                pass
                
        logger.warning("validator.py not found in standard locations")
        return None
    
    def check_course_data(self):
        """Check if course data is available and prompt to select if not."""
        logger.info(f"Checking course data: {config.current_course_data}")
        
        if not config.current_course_data or not config.current_course_data.exists():
            # No course data available, show info dialog and then selector
            messagebox.showinfo(
                "Course Data Required",
                "Welcome to Transcript Editor!\n\n"
                "Please select a course data file to continue."
            )
            CourseDataSelectorDialog(self, self.on_course_data_selected)
        else:
            # Course data is available, load it
            self.load_course_data()
        
        # Update the course data display
        self.update_course_data_display()
    
    def load_course_data(self):
        """Load course data from the default file."""
        logger.info(f"Loading course data from {config.current_course_data}")
        
        if config.current_course_data and config.current_course_data.exists():
            course_data = load_course_data(str(config.current_course_data))
            self.course_manager.set_course_data(course_data)
            logger.info(f"Loaded {len(course_data.get('all_courses', {}))} courses")
        else:
            logger.warning("No course data file available")
            messagebox.showwarning(
                "Course Data",
                "No course data file found. Some features will be limited. "
                "Use 'File > Select Course Data' to choose a course data file."
            )
    
    def update_course_data_display(self):
        """Update the display of current course data file."""
        if config.current_course_data and config.current_course_data.exists():
            self.course_data_var.set(f"Current Course Data: {config.current_course_data.name}")
        else:
            self.course_data_var.set("No course data file selected")
    
    def create_menu(self):
        """Create the application menu bar."""
        # Menu bar
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Transcript", command=self.new_transcript)
        file_menu.add_command(label="Open JSON...", command=self.open_json)
        file_menu.add_command(label="Try Extract from PDF...", command=self.try_extract_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self.save_data)
        file_menu.add_command(label="Save As...", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Select Course Data...", command=self.select_course_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        # Tools menu
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Validate Transcript", command=self.validate_data)
        tools_menu.add_separator()
        tools_menu.add_command(label="Course Lookup", command=self.show_course_lookup)
    
    def create_widgets(self):
        """Create the main application widgets."""
        # Main container with two frames side by side
        main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Student info and semester navigation
        left_panel = ttk.Frame(main_container, padding=10)
        main_container.add(left_panel, weight=1)
        
        # Right panel - Current semester details
        right_panel = ttk.Frame(main_container, padding=10)
        main_container.add(right_panel, weight=2)
        
        # ===== LEFT PANEL =====
        # Quick action buttons
        quick_buttons_frame = ttk.Frame(left_panel)
        quick_buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(quick_buttons_frame, text="Read PDF", command=self.try_extract_pdf).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_buttons_frame, text="Save JSON", command=self.save_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_buttons_frame, text="Validate", command=self.quick_validate).pack(side=tk.LEFT, padx=2)
        
        # Student Information Section
        self.student_panel = self.student_manager.create_panel(left_panel)
        self.student_panel.pack(fill=tk.X, expand=False, pady=(0, 10))
        
        # Semester Navigation Section
        self.semester_panel = self.semester_manager.create_panel(
            left_panel, callback=self.on_semester_change)
        self.semester_panel.pack(fill=tk.BOTH, expand=True)
        
        # ===== RIGHT PANEL =====
        # Display for currently selected course data file at the top-right
        course_data_frame = ttk.Frame(right_panel)
        course_data_frame.pack(fill=tk.X, pady=(0, 5), anchor=tk.E)
        
        self.course_data_var = tk.StringVar(value="No course data file selected")
        course_data_label = ttk.Label(course_data_frame, textvariable=self.course_data_var, font=("Arial", 10, "italic"))
        course_data_label.pack(side=tk.RIGHT)
        
        # Current Semester Section
        self.semester_details_panel = SemesterDetailsPanel(
            right_panel, self.semester_manager, self.course_manager, callback=self.on_semester_details_change)
        self.semester_details_panel.pack(fill=tk.X, expand=False)
        
        # Courses Section
        self.course_panel = self.course_manager.create_panel(right_panel, self.semester_manager)
        self.course_panel.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def on_semester_change(self):
        """Handle semester selection change."""
        # Update semester details panel
        self.semester_details_panel.update_from_manager()
        
        # Update course panel
        self.course_panel.update_course_list()
    
    def on_semester_details_change(self):
        """Handle semester details change."""
        # Update semester panel to reflect changes
        self.semester_panel.update_listbox()
        
        # Update course panel
        self.course_panel.update_course_list()
    
    def new_transcript(self):
        """Create a new, empty transcript."""
        if self.model.changed:
            if not messagebox.askyesno("Unsaved Changes", 
                                      "You have unsaved changes. Are you sure you want to start a new transcript?"):
                return
        
        # Reset model
        self.model.reset()
        
        # Update UI
        self.student_panel.load_from_manager()
        self.semester_panel.update_listbox()
        self.semester_details_panel.update_from_manager()
        self.course_panel.update_course_list()
        
        # Update window title
        self.title("Transcript Data Editor - New Transcript")
        
        self.report_status("New transcript created")
    
    def open_json(self):
        """Open transcript data from a JSON file."""
        if self.model.changed:
            if not messagebox.askyesno("Unsaved Changes", 
                                      "You have unsaved changes. Are you sure you want to open a different file?"):
                return
        
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Open Transcript Data",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Load transcript
        if load_transcript(self.model, file_path):
            self.model.current_file_path = file_path
            
            # Update UI
            self.student_panel.load_from_manager()
            self.semester_panel.update_listbox()
            self.semester_details_panel.update_from_manager()
            self.course_panel.update_course_list()
            
            # Update window title
            self.title(f"Transcript Data Editor - {os.path.basename(file_path)}")
            
            self.report_status(f"Loaded transcript data from {os.path.basename(file_path)}")
        else:
            messagebox.showerror("Error", "Failed to load transcript data")
    
    def save_data(self):
        """Save transcript data to current file or prompt for new file."""
        if not self.model.current_file_path:
            return self.save_as()
        
        return self.save_to_file(self.model.current_file_path)
    
    def save_as(self):
        """Save transcript data to a new file."""
        file_path = filedialog.asksaveasfilename(
            title="Save Transcript Data",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return False
        
        return self.save_to_file(file_path)
    
    def save_to_file(self, file_path):
        """Save transcript data to specified file."""
        if save_transcript(self.model, file_path):
            self.model.current_file_path = file_path
            self.model.set_changed(False)
            
            # Update window title
            self.title(f"Transcript Data Editor - {os.path.basename(file_path)}")
            
            self.report_status(f"Saved to {os.path.basename(file_path)}")
            return True
        else:
            messagebox.showerror("Error", "Failed to save transcript data")
            return False
    
    def try_extract_pdf(self):
        """Attempt to extract transcript data from a PDF file."""
        if self.model.changed:
            if not messagebox.askyesno("Unsaved Changes", 
                                      "You have unsaved changes. Are you sure you want to extract data from a PDF?"):
                return
        
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Extract from PDF Transcript",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Ask if this is for a new transcript or to append to current
        if self.model.semesters:
            action = messagebox.askyesnocancel(
                "PDF Extraction",
                "Do you want to replace the current transcript (Yes) or append to it (No)?",
                default=messagebox.NO
            )
            
            if action is None:  # Cancel
                return
            
            append_mode = not action  # False for replace, True for append
        else:
            append_mode = False  # No existing data, so just create new
        
        # Extract text from PDF
        self.report_status(f"Extracting text from {os.path.basename(file_path)}...")
        extracted_text = self.pdf_extractor.extract_text_from_pdf(file_path)
        
        if not extracted_text:
            messagebox.showerror("Error", "Failed to extract text from PDF")
            self.report_status("PDF extraction failed")
            return
        
        # Show text for manual correction
        PDFExtractionDialog(
            self, 
            extracted_text, 
            lambda corrected_text: self.process_corrected_text(corrected_text, append_mode)
        )
    
    def process_corrected_text(self, corrected_text, append_mode):
        """
        Process corrected text from PDF extraction.
        
        Args:
            corrected_text: Corrected text from PDF
            append_mode: Whether to append to current transcript or replace
        """
        # Process the corrected text
        student_info, semesters, _ = self.pdf_extractor.process_pdf(
            None,  # No file path needed, using corrected text directly
            corrected_text
        )
        
        if not student_info or not semesters:
            messagebox.showerror("Error", "Failed to extract transcript data from text")
            self.report_status("PDF data extraction failed")
            return
        
        # Update model based on append_mode
        if not append_mode:
            # Replace existing data
            self.model.student_info = student_info
            self.model.semesters = semesters
            self.model.current_semester_index = 0 if semesters else 0
        else:
            # Append semesters to existing data
            self.model.semesters.extend(semesters)
            self.model.current_semester_index = len(self.model.semesters) - 1 if self.model.semesters else 0
        
        self.model.set_changed()
        
        # Update UI
        self.student_panel.load_from_manager()
        self.semester_panel.update_listbox()
        self.semester_details_panel.update_from_manager()
        self.course_panel.update_course_list()
        
        self.report_status(f"Extracted {len(semesters)} semesters from PDF")
    
    def validate_data(self):
        """Validate transcript data using validator."""
        # First, check if we have a course data file
        if not config.current_course_data or not config.current_course_data.exists():
            # Ask the user to select a course data file
            CourseDataSelectorDialog(self, self.on_course_data_selected_for_validation)
            return
        
        # If we have a course data file, proceed with validation
        self.perform_validation()
    
    def quick_validate(self):
        """Perform a quick validation with the current course data and open the report."""
        # Check if we have a course data file
        if not config.current_course_data or not config.current_course_data.exists():
            messagebox.showwarning(
                "Course Data Required",
                "A course data file is required for validation. Please select one."
            )
            CourseDataSelectorDialog(self, self.on_course_data_selected_for_quick_validation)
            return
        
        # Proceed with validation and auto-open report
        self.perform_validation(auto_open_report=True)
    
    def on_course_data_selected_for_quick_validation(self, file_path):
        """
        Handle course data selection for quick validation.
        
        Args:
            file_path: Selected course data file path
        """
        if not file_path:
            self.report_status("Validation cancelled - no course data selected")
            return
        
        # Set the current course data file
        config.set_current_course_data(file_path)
        
        # Update the course data display
        self.update_course_data_display()
        
        # Reload course data
        self.load_course_data()
        
        # Perform validation with auto-open
        self.perform_validation(auto_open_report=True)
    
    def on_course_data_selected_for_validation(self, file_path):
        """
        Handle course data selection for validation.
        
        Args:
            file_path: Selected course data file path
        """
        if not file_path:
            self.report_status("Validation cancelled - no course data selected")
            return
        
        # Set the current course data file
        config.set_current_course_data(file_path)
        
        # Update the course data display
        self.update_course_data_display()
        
        # Reload course data
        self.load_course_data()
        
        # Perform validation
        self.perform_validation()
    
    def perform_validation(self, auto_open_report=False):
        """Perform validation using the current course data."""
        # Make sure validator is initialized
        if not self.validation_adapter.initialize_validator(str(config.current_course_data)):
            messagebox.showerror("Error", "Failed to initialize validator")
            return
        
        # Validate the current transcript
        self.report_status("Validating transcript...")
        validation_results = self.validation_adapter.validate_transcript(
            self.model.student_info, self.model.semesters)
        
        if not validation_results:
            messagebox.showerror("Error", "Validation failed")
            return
        
        # Get student ID for filename
        student_id = self.model.student_info.get("id", "unknown")
        
        # Ask user for format
        from ui.dialogs import FormatSelectionDialog
        
        def save_report(format_type):
            if format_type is None:
                return
            
            # Choose file path based on format
            if format_type == "excel":
                report_path = config.reports_dir / f"validation_report_{student_id}.xlsx"
                # Import and use Excel export function
                from utils.file_operations import save_validation_report_excel
                success = save_validation_report_excel(
                    self.model.student_info, self.model.semesters, validation_results, report_path)
            else:
                # Text format (existing code)
                report_path = config.reports_dir / f"validation_report_{student_id}.txt"
                report = self.validation_adapter.generate_validation_report(
                    self.model.student_info, self.model.semesters, validation_results)
                with open(report_path, 'w', encoding='utf-8') as file:
                    file.write(report)
                success = True
            
            if success:
                invalid_count = len([r for r in validation_results if not r.get("is_valid", True)])
                self.report_status(f"Validation complete - {invalid_count} issues found")
                
                if auto_open_report:
                    # Open the file
                    if sys.platform == 'win32':
                        os.startfile(report_path)
                    elif sys.platform == 'darwin':
                        subprocess.call(['open', str(report_path)])
                    else:
                        subprocess.call(['xdg-open', str(report_path)])
            else:
                messagebox.showerror("Error", f"Failed to save {format_type} report")
        
        FormatSelectionDialog(self, save_report)
    
    def select_course_data(self):
        """Select a course data file."""
        CourseDataSelectorDialog(self, self.on_course_data_selected)
    
    def on_course_data_selected(self, file_path):
        """
        Handle course data selection.
        
        Args:
            file_path: Selected course data file path
        """
        if not file_path:
            self.report_status("Course data selection cancelled")
            
            # Show warning and prompt again if no file was selected
            retry = messagebox.askyesno(
                "Course Data Required",
                "No course data file selected. Some features will be limited without course data.\n\n"
                "Would you like to select a course data file now?"
            )
            
            if retry:
                CourseDataSelectorDialog(self, self.on_course_data_selected)
            
            return
        
        # Set the current course data file
        config.set_current_course_data(file_path)
        
        # Update the course data display
        self.update_course_data_display()
        
        # Reload course data
        self.load_course_data()
        
        self.report_status(f"Selected course data: {os.path.basename(file_path)}")
    
    def show_course_lookup(self):
        """Show course lookup dialog."""
        CourseLookupDialog(self, self.course_manager)
    
    def report_status(self, message):
        """
        Update status bar with a message.
        
        Args:
            message: Status message to display
        """
        self.status_var.set(message)
        logger.info(message)
    
    def quit(self):
        """Quit the application."""
        if self.model.changed:
            if not messagebox.askyesno("Unsaved Changes", 
                                      "You have unsaved changes. Are you sure you want to quit?"):
                return
        
        super().quit()
