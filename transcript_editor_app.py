#!/usr/bin/env python3
"""
Transcript Editor Application - Entry Point
"""
import sys
import os
import logging
from pathlib import Path
import traceback

# Ensure the root directory is in the path for imports
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

# Set up logging
from utils.logger_setup import setup_logging
setup_logging()

logger = logging.getLogger("transcript_editor_app")

def main():
    """Main entry point for the application."""
    try:
        # Import main application
        from app import TranscriptEditorApp
        
        logger.info("Starting Transcript Editor Application")
        app = TranscriptEditorApp()
        app.mainloop()
        
        return 0
    
    except Exception as e:
        logger.critical(f"Error starting application: {e}")
        logger.critical(traceback.format_exc())
        
        # Show a simple error dialog if tkinter is available
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Application Error", 
                               f"Error starting application: {e}\n\n"
                               f"Please check the logs for details.")
            root.destroy()
        except Exception:
            print(f"ERROR: Failed to start application: {e}")
            print("See logs for details.")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
