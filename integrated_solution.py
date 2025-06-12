#!/usr/bin/env python3
"""
Course Registration Validation System - Integrated Solution
This script provides a simple launcher for the transcript editor and validator.
"""
import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import logging
from pathlib import Path
import importlib.resources
import importlib.util
import pkg_resources

# Set up logging
from utils.logger_setup import setup_logging
setup_logging()
logger = logging.getLogger("integrated_solution")

# Find the package root directory
try:
    # First try to get the installed package location
    package_root = Path(pkg_resources.resource_filename(__name__, ''))
    logger.info(f"Using installed package at: {package_root}")
except (ImportError, pkg_resources.DistributionNotFound):
    # Fall back to the current directory if not installed as package
    package_root = Path(__file__).parent
    logger.info(f"Using local directory: {package_root}")

# Add package root to path for imports
sys.path.append(str(package_root))

# Import utilities now that path is set up
from utils.config import config
from utils.validation_adapter import ValidationAdapter
from ui.dialogs import CourseDataSelectorDialog

class LauncherApp(tk.Tk):
    """Launcher application for the Course Registration Validation System."""
    
    def __init__(self):
        super().__init__()
        self.title("Course Registration Validation System")
        self.geometry("600x400")
        
        self.setup_paths()
        self.create_widgets()
    
    def setup_paths(self):
        """Set up paths to required files and check their existence."""
        # Use package paths instead of relative paths
        self.transcript_editor_path = package_root / "transcript_editor_app.py"
        self.validator_path = package_root / "validator.py"
        
        # Check if required files exist
        missing_files = []
        for path in [self.transcript_editor_path, self.validator_path]:
            if not path.exists():
                missing_files.append(str(path.name))
        
        if missing_files:
            logger.warning(f"Missing required files: {missing_files}")
            self.missing_files = missing_files
        else:
            self.missing_files = []
        
        # Initialize validation adapter with absolute path
        self.validation_adapter = ValidationAdapter(str(self.validator_path))
    
    def create_widgets(self):
        """Create the GUI widgets."""
        # Main frame with padding
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, 
                              text="Course Registration Validation System", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Description
        description = (
            "This system allows you to validate course registrations according to university rules. "
            "It uses a two-stage process:\n\n"
            "1. Edit transcript data manually or extract from PDF\n"
            "2. Validate registrations against prerequisites and other rules"
        )
        
        desc_label = ttk.Label(main_frame, text=description, wraplength=500, justify="center")
        desc_label.pack(pady=(0, 20))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=10)
        
        # Launch Transcript Editor button
        editor_button = ttk.Button(buttons_frame, 
                                text="Launch Transcript Editor", 
                                command=self.launch_transcript_editor,
                                width=25)
        editor_button.pack(pady=5)
        
        # Validate Transcript button
        validate_button = ttk.Button(buttons_frame, 
                                   text="Validate Transcript (JSON)", 
                                   command=self.validate_transcript,
                                   width=25)
        validate_button.pack(pady=5)
        
        # View Reports button
        reports_button = ttk.Button(buttons_frame, 
                                  text="View Reports", 
                                  command=self.open_reports_directory,
                                  width=25)
        reports_button.pack(pady=5)
        
        # Missing files warning if applicable
        if self.missing_files:
            warning_text = f"Warning: Missing required files: {', '.join(self.missing_files)}"
            warning_label = ttk.Label(main_frame, text=warning_text, 
                                    foreground="red", wraplength=500)
            warning_label.pack(pady=10)
        
        # Dedication to Raphin P.
        dedication_frame = ttk.Frame(main_frame)
        dedication_frame.pack(fill=tk.X, pady=(20, 0))
        dedication_label = ttk.Label(dedication_frame, 
                                  text="Created for Raphin P.",
                                  font=("Arial", 10, "italic"),
                                  foreground="#555555")
        dedication_label.pack(side=tk.RIGHT)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def launch_transcript_editor(self):
        """Launch the transcript editor application."""
        if not self.transcript_editor_path.exists():
            messagebox.showerror("Error", "Transcript Editor is missing. "
                               "Please ensure transcript_editor_app.py is available.")
            return
        
        try:
            self.status_var.set("Launching Transcript Editor...")
            subprocess.Popen([sys.executable, str(self.transcript_editor_path)])
            self.status_var.set("Transcript Editor launched")
        except Exception as e:
            logger.error(f"Error launching Transcript Editor: {e}")
            messagebox.showerror("Error", f"Failed to launch Transcript Editor: {e}")
            self.status_var.set("Error launching Transcript Editor")
    
    def validate_transcript(self):
        """Validate a JSON transcript file using the validation adapter."""
        if not self.validator_path.exists():
            messagebox.showerror("Error", "Validator is missing. "
                               "Please ensure validator.py is available.")
            return
        
        # Open file dialog to select JSON transcript
        json_path = filedialog.askopenfilename(
            title="Select JSON Transcript",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not json_path:
            return
        
        try:
            self.status_var.set(f"Preparing to validate {os.path.basename(json_path)}...")
            
            # Show course data selection dialog
            CourseDataSelectorDialog(self, lambda file_path: self.perform_validation(json_path, file_path))
            
        except Exception as e:
            logger.error(f"Error preparing validation: {e}")
            messagebox.showerror("Error", f"Failed to prepare validation: {e}")
            self.status_var.set("Error during validation preparation")
    
    def perform_validation(self, json_path, course_data_path):
        """
        Perform validation with selected files.
        
        Args:
            json_path: Path to JSON transcript file
            course_data_path: Path to course data file
        """
        if not course_data_path:
            self.status_var.set("Validation cancelled - no course data selected")
            return
        
        try:
            self.status_var.set(f"Validating using {os.path.basename(course_data_path)}...")
            
            # Initialize validator with selected course data
            self.validation_adapter.initialize_validator(course_data_path)
            
            # Process transcript
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            student_info = data.get("student_info", {})
            semesters = data.get("semesters", [])
            
            # Validate the transcript
            validation_results = self.validation_adapter.validate_transcript(student_info, semesters)
            
            # Generate student ID for report filename
            student_id = student_info.get("id", "unknown")
            
            # Generate and save report
            output_path = config.reports_dir / f"validation_report_{student_id}.txt"
            report = self.validation_adapter.generate_validation_report(
                student_info, semesters, validation_results)
            
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(report)
            
            # Show success message
            invalid_count = len([r for r in validation_results if not r.get("is_valid", True)])
            message = (f"Validation completed for {student_info.get('name')} (ID: {student_id})\n\n"
                     f"Semesters: {len(semesters)}\n"
                     f"Valid registrations: {len(validation_results) - invalid_count}\n"
                     f"Invalid registrations: {invalid_count}\n\n"
                     f"Course data: {os.path.basename(course_data_path)}\n"
                     f"Report saved to: {output_path}\n\n"
                     f"Would you like to view the report?")
            
            if messagebox.askyesno("Validation Complete", message):
                # Open the report file with the default text editor
                if sys.platform == 'win32':
                    os.startfile(output_path)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.call(['open', output_path])
                else:  # Linux
                    subprocess.call(['xdg-open', output_path])
            
            self.status_var.set(f"Validation complete - {invalid_count} issues found")
        
        except Exception as e:
            logger.error(f"Error validating transcript: {e}")
            import traceback
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to validate transcript: {e}")
            self.status_var.set("Error during validation")
    
    def on_course_data_selected(self, file_path):
        """
        Handle course data selection.
        
        Args:
            file_path: Selected course data file path
        """
        if file_path:
            config.set_current_course_data(file_path)
            self.status_var.set(f"Selected course data: {os.path.basename(file_path)}")
        else:
            self.status_var.set("Course data management closed")
    
    def open_reports_directory(self):
        """Open the reports directory in the file explorer."""
        try:
            if sys.platform == 'win32':
                os.startfile(config.reports_dir)
            elif sys.platform == 'darwin':  # macOS
                subprocess.call(['open', config.reports_dir])
            else:  # Linux
                subprocess.call(['xdg-open', config.reports_dir])
            
            self.status_var.set(f"Opened reports directory: {config.reports_dir}")
        except Exception as e:
            logger.error(f"Error opening reports directory: {e}")
            messagebox.showerror("Error", f"Failed to open reports directory: {e}")
            self.status_var.set("Error opening reports directory")

def main():
    """Main entry point for the application."""
    app = LauncherApp()
    app.mainloop()
    return 0

if __name__ == "__main__":
    sys.exit(main())
