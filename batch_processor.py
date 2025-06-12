#!/usr/bin/env python3
"""
Batch Processor for Course Registration Validation System.
This script provides a GUI for batch processing PDF transcripts.
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import threading
import queue
from pathlib import Path
import time
import importlib.resources
import importlib.util
import pkg_resources

# Set up logging first with basic configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("batch_processor")

# Find useful paths
try:
    # First try to get the installed package location
    package_root = Path(pkg_resources.resource_filename(__name__, ''))
    logger.info(f"Using installed package at: {package_root}")
    
    # Use appdirs for proper locations in user directory
    import appdirs
    app_name = "course-registration-validator"
    app_author = "modern-research-group"
    
    user_data_dir = Path(appdirs.user_data_dir(app_name, app_author))
    user_data_dir.mkdir(exist_ok=True, parents=True)
    
except (ImportError, pkg_resources.DistributionNotFound):
    # Fall back to the current directory if not installed as package
    package_root = Path(os.path.dirname(os.path.abspath(__file__)))
    logger.info(f"Using local directory: {package_root}")

# Add package root to path for imports
sys.path.append(str(package_root))

# Additionally, add potential validator locations to path
for potential_path in [
    package_root.parent,
    package_root.parent.parent,
    # The package root might be the site-packages/course_registration_validator directory
    # where validator.py might be one level up
    Path(os.path.dirname(package_root))
]:
    if potential_path not in sys.path and potential_path.exists():
        sys.path.append(str(potential_path))
        logger.info(f"Added potential path: {potential_path}")

# Now try to import
from utils.logger_setup import setup_logging
from utils.config import config
from utils.validation_adapter import ValidationAdapter
from utils.pdf_extractor import PDFExtractor

# Reinitialize logging with proper setup
setup_logging()
logger = logging.getLogger("batch_processor")

class BatchProcessorApp(tk.Tk):
    """GUI application for batch processing PDF transcripts."""
    
    def __init__(self):
        """Initialize the application."""
        super().__init__()
        self.title("Course Registration Validation - Batch Processor")
        self.geometry("1200x920")
        self.minsize(1150, 870)
        
        # Initialize components
        self.pdf_extractor = PDFExtractor()
        
        # Initialize the validation adapter
        # Try to find validator.py in several possible locations
        validator_path = self.find_validator_path()
        if validator_path:
            logger.info(f"Using validator path: {validator_path}")
            self.validation_adapter = ValidationAdapter(str(validator_path))
        else:
            logger.warning("Using default validator path - may not work correctly")
            self.validation_adapter = ValidationAdapter()
        
        # Initialize state variables
        self.course_data_path = None
        self.pdf_directory = None
        self.output_directory = None
        self.processing_queue = queue.Queue()
        self.stop_requested = False
        
        # Create UI
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
        
        logger.info("Batch Processor initialized")
    
    def find_validator_path(self):
        """Find the path to validator.py"""
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
        
        # Try to find the validator file
        for path in potential_paths:
            if path.exists():
                logger.info(f"Found validator.py at: {path}")
                return path
                
        # If not found through paths, try to find it as a module
        for module_name in ["validator", "course-registration-validator.validator"]:
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
    
    def create_widgets(self):
        """Create the GUI widgets."""
        # Main frame with padding
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, 
                              text="Batch Process PDF Transcripts", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Warning message
        warning_frame = ttk.Frame(main_frame)
        warning_frame.pack(fill=tk.X, pady=10)
        
        warning_text = "WARNING: This batch processor was created for my own use only.\n" + \
                       "It was NOT designed with other users in mind. If you're not me,\n" + \
                       "please use integrated_solution.py which has proper safeguards."
        
        warning_label = ttk.Label(warning_frame, 
                                text=warning_text, 
                                foreground="red",
                                font=("Arial", 11, "bold"),
                                justify="center")
        warning_label.pack(pady=5)
        
        # Motto frame (placed between warning and course selection)
        motto_frame = ttk.Frame(main_frame)
        motto_frame.pack(fill=tk.X, pady=(0, 10))
        
        motto_label = ttk.Label(motto_frame, 
                             text="Be smart folk, don't be a joke.",
                             font=("Arial", 11, "italic", "bold"),
                             foreground="#006400")
        motto_label.pack(side=tk.RIGHT, padx=15)
        
        # Course Data Selection Frame
        course_frame = ttk.LabelFrame(main_frame, text="Step 1: Select Course Data", padding=10)
        course_frame.pack(fill=tk.X, pady=5)
        
        course_row = ttk.Frame(course_frame)
        course_row.pack(fill=tk.X, expand=True)
        
        self.course_path_var = tk.StringVar()
        ttk.Label(course_row, text="Course Data File:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(course_row, textvariable=self.course_path_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(course_row, text="Browse...", command=self.select_course_data).pack(side=tk.LEFT)
        
        # PDF Directory Selection Frame
        pdf_frame = ttk.LabelFrame(main_frame, text="Step 2: Select PDF Directory", padding=10)
        pdf_frame.pack(fill=tk.X, pady=5)
        
        pdf_row = ttk.Frame(pdf_frame)
        pdf_row.pack(fill=tk.X, expand=True)
        
        self.pdf_dir_var = tk.StringVar()
        ttk.Label(pdf_row, text="PDF Directory:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(pdf_row, textvariable=self.pdf_dir_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(pdf_row, text="Browse...", command=self.select_pdf_directory).pack(side=tk.LEFT)
        
        # Output Directory Selection Frame
        output_frame = ttk.LabelFrame(main_frame, text="Step 3: Select Output Directory", padding=10)
        output_frame.pack(fill=tk.X, pady=5)
        
        output_row = ttk.Frame(output_frame)
        output_row.pack(fill=tk.X, expand=True)
        
        self.output_dir_var = tk.StringVar()
        ttk.Label(output_row, text="Output Directory:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(output_row, textvariable=self.output_dir_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(output_row, text="Browse...", command=self.select_output_directory).pack(side=tk.LEFT)
        
        # Processing Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding=10)
        options_frame.pack(fill=tk.X, pady=5)
        
        self.recursion_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Include subdirectories", variable=self.recursion_var).pack(anchor=tk.W)
        
        # Progress Frame
        progress_frame = ttk.LabelFrame(main_frame, text="Step 4: Process Files", padding=10)
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Progress information
        info_frame = ttk.Frame(progress_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text="Total Files:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.total_files_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.total_files_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(info_frame, text="Processed:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.processed_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.processed_var).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(info_frame, text="Successful:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.success_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.success_var).grid(row=0, column=3, sticky=tk.W, padx=5)
        
        ttk.Label(info_frame, text="Failed:").grid(row=1, column=2, sticky=tk.W, padx=5)
        self.failed_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.failed_var).grid(row=1, column=3, sticky=tk.W, padx=5)
        
        # Current file being processed
        ttk.Label(progress_frame, text="Current File:").pack(anchor=tk.W, pady=(10, 0))
        self.current_file_var = tk.StringVar(value="None")
        ttk.Label(progress_frame, textvariable=self.current_file_var, wraplength=750).pack(anchor=tk.W, fill=tk.X)
        
        # Progress bar
        ttk.Label(progress_frame, text="Progress:").pack(anchor=tk.W, pady=(10, 0))
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate", length=700)
        self.progress_bar.pack(fill=tk.X, pady=(5, 10))
        
        # Log display (make this scrollable)
        ttk.Label(progress_frame, text="Processing Log:").pack(anchor=tk.W)
        log_frame = ttk.Frame(progress_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=8)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Processing", command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Open Output Directory", command=self.open_output_directory).pack(side=tk.LEFT, padx=5)
        
    def select_course_data(self):
        """Open file dialog to select course data file."""
        file_path = filedialog.askopenfilename(
            title="Select Course Data File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            self.course_data_path = file_path
            self.course_path_var.set(file_path)
            self.report_status(f"Course data file selected: {os.path.basename(file_path)}")
    
    def select_pdf_directory(self):
        """Open directory dialog to select PDF directory."""
        directory = filedialog.askdirectory(title="Select PDF Directory")
        
        if directory:
            self.pdf_directory = directory
            self.pdf_dir_var.set(directory)
            self.report_status(f"PDF directory selected: {directory}")
            
            # Count PDF files
            pdfs = self.count_pdf_files(directory, self.recursion_var.get())
            self.total_files_var.set(str(len(pdfs)))
    
    def select_output_directory(self):
        """Open directory dialog to select output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        
        if directory:
            self.output_directory = directory
            self.output_dir_var.set(directory)
            self.report_status(f"Output directory selected: {directory}")
    
    def count_pdf_files(self, directory, recursive=False):
        """Count PDF files in directory."""
        pdf_files = []
        
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(directory):
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(directory, file))
        
        return pdf_files
    
    def start_processing(self):
        """Start processing PDF files."""
        # Validate inputs
        if not self.course_data_path or not os.path.exists(self.course_data_path):
            messagebox.showerror("Error", "Please select a valid course data file")
            return
        
        if not self.pdf_directory or not os.path.exists(self.pdf_directory):
            messagebox.showerror("Error", "Please select a valid PDF directory")
            return
        
        if not self.output_directory or not os.path.exists(self.output_directory):
            messagebox.showerror("Error", "Please select a valid output directory")
            return
        
        # Initialize the validation adapter
        if not self.validation_adapter.initialize_validator(self.course_data_path):
            messagebox.showerror("Error", "Failed to initialize validator with selected course data")
            return
        
        # Get PDF files
        pdf_files = self.count_pdf_files(self.pdf_directory, self.recursion_var.get())
        
        if not pdf_files:
            messagebox.showwarning("Warning", "No PDF files found in the selected directory")
            return
        
        # Update UI
        self.total_files_var.set(str(len(pdf_files)))
        self.processed_var.set("0")
        self.success_var.set("0")
        self.failed_var.set("0")
        self.progress_bar["maximum"] = len(pdf_files)
        self.progress_bar["value"] = 0
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Disable start button, enable stop button
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Reset stop flag
        self.stop_requested = False
        
        # Add files to queue
        for pdf_file in pdf_files:
            self.processing_queue.put(pdf_file)
        
        # Start processing thread
        processing_thread = threading.Thread(target=self.process_files_worker)
        processing_thread.daemon = True
        processing_thread.start()
        
        self.report_status(f"Started processing {len(pdf_files)} PDF files")
    
    def process_files_worker(self):
        """Worker function for processing files in a thread."""
        processed = 0
        successful = 0
        failed = 0
        
        while not self.processing_queue.empty() and not self.stop_requested:
            # Get next file
            pdf_file = self.processing_queue.get()
            
            # Update UI
            self.current_file_var.set(pdf_file)
            self.log_append(f"Processing: {pdf_file}")
            
            try:
                # Process the file
                result = self.process_pdf_file(pdf_file)
                
                if result:
                    successful += 1
                    self.log_append(f"✓ Succeeded: {os.path.basename(pdf_file)}")
                else:
                    failed += 1
                    self.log_append(f"✗ Failed: {os.path.basename(pdf_file)}")
                
            except Exception as e:
                failed += 1
                self.log_append(f"✗ Error processing {os.path.basename(pdf_file)}: {str(e)}")
                logger.error(f"Error processing {pdf_file}: {e}")
            
            # Update counters
            processed += 1
            
            # Update UI on main thread
            self.after(0, self.update_progress, processed, successful, failed)
            
            # Give UI time to update
            time.sleep(0.1)
        
        # Processing complete or stopped
        if self.stop_requested:
            self.after(0, self.processing_stopped)
        else:
            self.after(0, self.processing_complete)
    
    def update_progress(self, processed, successful, failed):
        """Update progress indicators."""
        self.processed_var.set(str(processed))
        self.success_var.set(str(successful))
        self.failed_var.set(str(failed))
        self.progress_bar["value"] = processed
    
    def processing_complete(self):
        """Handle completion of processing."""
        self.report_status("Processing complete")
        self.current_file_var.set("None")
        self.log_append("Processing complete")
        
        # Enable start button, disable stop button
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # Show completion message
        messagebox.showinfo(
            "Processing Complete", 
            f"Processed {self.processed_var.get()} files\n"
            f"Successful: {self.success_var.get()}\n"
            f"Failed: {self.failed_var.get()}"
        )
    
    def processing_stopped(self):
        """Handle stop of processing."""
        self.report_status("Processing stopped")
        self.current_file_var.set("None")
        self.log_append("Processing stopped by user")
        
        # Enable start button, disable stop button
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def stop_processing(self):
        """Stop processing files."""
        self.stop_requested = True
        self.report_status("Stopping processing...")
    
    def process_pdf_file(self, pdf_file):
        """
        Process a single PDF file.
        
        Args:
            pdf_file: Path to the PDF file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract transcript data from PDF
            student_info, semesters, _ = self.pdf_extractor.process_pdf(pdf_file)
            
            if not student_info or not semesters:
                self.log_append(f"Could not extract transcript data from {os.path.basename(pdf_file)}")
                return False
            
            # Validate the transcript
            validation_results = self.validation_adapter.validate_transcript(
                student_info, semesters)
            
            if not validation_results:
                self.log_append(f"Failed to validate transcript from {os.path.basename(pdf_file)}")
                return False
            
            # Generate report
            student_id = student_info.get("id", "unknown")
            
            # Use filename if student ID is unknown
            if student_id == "unknown":
                student_id = os.path.splitext(os.path.basename(pdf_file))[0]
            
            # Count invalid courses
            invalid_results = [r for r in validation_results if not r.get("is_valid", True) and r.get("course_code") != "CREDIT_LIMIT"]
            invalid_count = len(invalid_results)
            
            # Generate report
            report = self.validation_adapter.generate_validation_report(
                student_info, semesters, validation_results)
            
            # Save report to output directory
            output_path = os.path.join(self.output_directory, f"validation_report_{student_id}.txt")
            
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(report)
            
            # Log invalid course count if any
            if invalid_count > 0:
                self.log_append(f"Student ID: {student_id} has {invalid_count} invalid courses", color="red")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {e}")
            raise
    
    def log_append(self, message, color=None):
        """
        Append message to log.
        
        Args:
            message: Message to append
            color: Optional text color (e.g., "red", "green")
        """
        self.log_text.insert(tk.END, message + "\n")
        
        # Apply color tag if specified
        if color:
            end_pos = self.log_text.index(tk.END)
            start_pos = f"{float(end_pos) - 1 - len(message)/10000} linestart"
            end_pos = f"{float(end_pos) - 1 + 0.0} lineend"
            
            # Create a tag for this color if it doesn't exist
            tag_name = f"color_{color}"
            if tag_name not in self.log_text.tag_names():
                self.log_text.tag_configure(tag_name, foreground=color)
            
            # Apply the tag
            self.log_text.tag_add(tag_name, start_pos, end_pos)
        
        self.log_text.see(tk.END)
    
    def report_status(self, message):
        """Update status bar."""
        self.status_var.set(message)
        logger.info(message)
    
    def open_output_directory(self):
        """Open the output directory in file explorer."""
        if not self.output_directory or not os.path.exists(self.output_directory):
            messagebox.showerror("Error", "Output directory not set or doesn't exist")
            return
        
        try:
            if sys.platform == 'win32':
                os.startfile(self.output_directory)
            elif sys.platform == 'darwin':  # macOS
                import subprocess
                subprocess.call(['open', self.output_directory])
            else:  # Linux
                import subprocess
                subprocess.call(['xdg-open', self.output_directory])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open directory: {e}")

def main():
    """Main entry point for the application."""
    app = BatchProcessorApp()
    app.mainloop()
    return 0

if __name__ == "__main__":
    sys.exit(main())
