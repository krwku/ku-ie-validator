#!/usr/bin/env python3
"""
Application configuration and path management.
"""
import os
from pathlib import Path
import logging
import appdirs
import pkg_resources

logger = logging.getLogger("config")

class Config:
    """Application configuration and paths."""
    
    def __init__(self):
        # Determine if running from installed package or local directory
        try:
            # Try to get the installed package location
            self.app_dir = Path(pkg_resources.resource_filename(__name__, '')).parent.parent
            logger.info(f"Using installed package at: {self.app_dir}")
            
            # Use appdirs for proper locations in user directory
            app_name = "course-registration-validator"
            app_author = "modern-research-group"
            
            user_data_dir = Path(appdirs.user_data_dir(app_name, app_author))
            user_data_dir.mkdir(exist_ok=True, parents=True)
            
            self.course_data_dir = user_data_dir / "course_data"
            self.reports_dir = user_data_dir / "reports"
            self.logs_dir = user_data_dir / "logs"
            
        except (ImportError, pkg_resources.DistributionNotFound):
            # Fall back to local directory if not installed as package
            self.app_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
            logger.info(f"Using local directory: {self.app_dir}")
            
            self.course_data_dir = self.app_dir / "course_data"
            self.reports_dir = self.app_dir / "reports"
            self.logs_dir = self.app_dir / "logs"
        
        # Ensure directories exist
        self.course_data_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Default files
        self.default_course_data = self.course_data_dir / "industrial-engineering-courses.json"
        
        # If the default course data doesn't exist in course_data dir but exists in root,
        # copy it to the course_data directory
        root_course_data = self.app_dir / "industrial-engineering-courses.json"
        if not self.default_course_data.exists() and root_course_data.exists():
            import shutil
            try:
                shutil.copy2(root_course_data, self.default_course_data)
                logger.info(f"Copied default course data to {self.default_course_data}")
            except Exception as e:
                logger.error(f"Failed to copy default course data: {e}")
        
        # Current course data file - can be changed during runtime
        self.current_course_data = self.default_course_data if self.default_course_data.exists() else None
    
    def get_available_course_data_files(self):
        """Get list of available course data files in course_data directory."""
        files = []
        
        if not self.course_data_dir.exists():
            return files
        
        for file_path in self.course_data_dir.glob("*.json"):
            try:
                # Attempt to read the file to extract a description
                description = "Course data file"
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Just check if it can be opened and read
                    content = f.read(200)
                    # Try to extract a description from the content
                    if "industrial_engineering_courses" in content:
                        description = "Industrial Engineering Courses"
                
                files.append({
                    "filename": file_path.name,
                    "description": description,
                    "path": str(file_path)
                })
            except Exception as e:
                logger.warning(f"Could not process course data file {file_path}: {e}")
        
        return files
    
    def set_current_course_data(self, file_path):
        """Set the current course data file."""
        self.current_course_data = Path(file_path)
        return self.current_course_data.exists()

# Create a global configuration instance
config = Config()
