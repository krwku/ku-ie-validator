#!/usr/bin/env python3
"""
Application configuration and path management.
Fixed to work with Streamlit Cloud by removing pkg_resources dependency.
"""
import os
from pathlib import Path
import logging

logger = logging.getLogger("config")

class Config:
    """Application configuration and paths."""
    
    def __init__(self):
        # Simplified for Streamlit Cloud compatibility
        self.app_dir = Path.cwd()
        self.course_data_dir = self.app_dir / "course_data"
        self.reports_dir = self.app_dir / "reports" 
        self.logs_dir = self.app_dir / "logs"
        
        # Create directories if they don't exist
        for directory in [self.course_data_dir, self.reports_dir, self.logs_dir]:
            try:
                directory.mkdir(exist_ok=True)
            except:
                pass
        
        self.default_course_data = self.course_data_dir / "ie_core_courses.json"
        self.current_course_data = self.default_course_data if self.default_course_data.exists() else None
    
    def get_available_course_data_files(self):
        """Get list of available course data files."""
        files = []
        if not self.course_data_dir.exists():
            return files
        
        for file_path in self.course_data_dir.glob("*.json"):
            try:
                files.append({
                    "filename": file_path.name,
                    "description": file_path.stem.replace("_", " ").title(),
                    "path": str(file_path)
                })
            except:
                pass
        return files
    
    def set_current_course_data(self, file_path):
        """Set the current course data file."""
        self.current_course_data = Path(file_path)
        return self.current_course_data.exists()

config = Config()
