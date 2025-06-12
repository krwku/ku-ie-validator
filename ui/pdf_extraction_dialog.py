#!/usr/bin/env python3
"""
PDF extraction dialog component.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger("pdf_extraction")

class PDFExtractionDialog(tk.Toplevel):
    """Dialog for extracting and correcting text from PDF transcripts."""
    
    def __init__(self, parent, extracted_text, callback):
            """
            Initialize the PDF extraction dialog.
            
            Args:
                parent: Parent tkinter widget
                extracted_text: Text extracted from PDF
                callback: Function to call with corrected text
            """
            super().__init__(parent)
            self.title("PDF Extraction - Manual Correction")
            self.geometry("900x700")  # Increased from 800x600
            self.transient(parent)
            self.grab_set()
            
            self.extracted_text = extracted_text
            self.callback = callback
            
            # Create UI elements
            self.create_widgets()
    
    def create_widgets(self):
        """Create UI widgets for the PDF extraction dialog."""
        # Main container
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        ttk.Label(main_frame, text="Review and correct the extracted text:").pack(pady=(0, 5))
        
        # Text editor with extracted text
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.text_editor = tk.Text(text_frame, wrap=tk.WORD)
        self.text_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.text_editor.insert(tk.END, self.extracted_text)
        
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_editor.yview)
        self.text_editor.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Help text
        help_text = (
            "Tips for better extraction:\n"
            "1. Make sure Student ID, Name, and Field of Study lines are clearly visible\n"
            "2. Each semester should start with 'First/Second/Summer Semester YYYY'\n"
            "3. Course entries should have format: '01234567 Course Name A/B+/B/... 3'\n"
            "4. Look for GPA values in format 'sem. G.P.A. = X.XX cum. G.P.A. = X.XX'"
        )
        
        help_frame = ttk.LabelFrame(main_frame, text="Help", padding=5)
        help_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(help_frame, text=help_text, wraplength=780, justify=tk.LEFT).pack(fill=tk.X)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)

        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # Use tk.Button for better size control
        proceed_btn = tk.Button(button_frame, text="Proceed with Extraction", 
                               command=self.proceed, 
                               width=20, height=2,
                               font=("Arial", 10))
        proceed_btn.pack(side=tk.RIGHT, padx=5)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                              command=self.destroy, 
                              width=15, height=2,
                              font=("Arial", 10))
        cancel_btn.pack(side=tk.RIGHT, padx=5)
    
    def proceed(self):
        """Process the corrected text and call the callback."""
        corrected_text = self.text_editor.get(1.0, tk.END)
        
        if not corrected_text.strip():
            messagebox.showwarning("Warning", "Extracted text is empty")
            return
        
        # Call the callback with the corrected text
        if self.callback:
            self.callback(corrected_text)
        
        # Close the dialog
        self.destroy()
