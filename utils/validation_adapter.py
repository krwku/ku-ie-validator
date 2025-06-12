#!/usr/bin/env python3
"""
Adapter for interfacing with the validation logic.
"""
import os
import sys
import importlib.util
import logging
from pathlib import Path
from utils.config import config

logger = logging.getLogger("validation_adapter")

class ValidationAdapter:
    """Class to adapt between the transcript editor and validator."""
    
    def __init__(self, validator_path=None):
        """
        Initialize the validation adapter.
        
        Args:
            validator_path: Path to the validator.py file
        """
        self.validator_path = validator_path or "validator.py"
        self.validator_module = None
        self.validator = None
        
        # Try to load the validator module
        self.load_validator_module()
    
    def load_validator_module(self):
        """Load the validator module dynamically."""
        try:
            # Check if the validator file exists
            if not os.path.exists(self.validator_path):
                logger.error(f"Validator file not found: {self.validator_path}")
                return False
            
            # Load the module
            spec = importlib.util.spec_from_file_location("validator", self.validator_path)
            if spec is None:
                logger.error(f"Could not create spec for {self.validator_path}")
                return False
                
            self.validator_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.validator_module)
            
            logger.info(f"Loaded validator module from {self.validator_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to load validator module: {e}")
            return False
    
    def initialize_validator(self, course_data_path=None):
        """
        Initialize the validator with course data.
        
        Args:
            course_data_path: Path to the course data file
        """
        if self.validator_module is None:
            if not self.load_validator_module():
                return False
        
        try:
            # Use provided course data path or default
            course_data_path = course_data_path or (
                config.current_course_data if config.current_course_data else 
                config.default_course_data)
            
            # Initialize the validator
            self.validator = self.validator_module.CourseRegistrationValidator(str(course_data_path))
            logger.info(f"Initialized validator with course data from {course_data_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize validator: {e}")
            return False
    
    def get_available_course_data_files(self):
        """Get a list of available course data files."""
        return config.get_available_course_data_files()
    
    def validate_transcript(self, student_info, semesters):
        """
        Validate transcript data.
        
        Args:
            student_info: Dictionary with student information
            semesters: List of semester dictionaries
            
        Returns:
            List of validation results
        """
        if self.validator is None:
            if not self.initialize_validator():
                logger.error("Cannot validate - validator not initialized")
                return []
        
        try:
            # Build a history of passed courses for each semester
            passed_courses_history = self.build_passed_courses_history(semesters)
            
            # Validate each semester
            all_results = []
            
            for i, semester in enumerate(semesters):
                # Check credit limit
                credit_valid, credit_reason = self.validator.validate_credit_limit(semester)
                if not credit_valid:
                    all_results.append({
                        "semester": semester.get("semester", ""),
                        "semester_index": i,
                        "course_code": "CREDIT_LIMIT",
                        "course_name": "Credit Limit Validation",
                        "grade": "N/A",
                        "is_valid": True,  # Mark as valid since it's just a warning
                        "reason": credit_reason,
                        "type": "credit_limit",
                        "student_id": student_info.get("id", ""),
                        "student_name": student_info.get("name", ""),
                        "transcript_file": "json_data"
                    })
                
                # Validate each course
                for course in semester.get("courses", []):
                    # Skip validation for withdrawn courses
                    if course.get("grade") == "W":
                        all_results.append({
                            "semester": semester.get("semester", ""),
                            "semester_index": i,
                            "course_code": course.get("code", ""),
                            "course_name": course.get("name", ""),
                            "grade": course.get("grade", ""),
                            "is_valid": True,
                            "reason": "Course was withdrawn",
                            "type": "prerequisite",
                            "student_id": student_info.get("id", ""),
                            "student_name": student_info.get("name", ""),
                            "transcript_file": "json_data"
                        })
                        continue
                    
                    # For courses that aren't withdrawn, check if they're valid
                    is_valid, reason = self.validator.validate_course(
                        course, i, semesters, passed_courses_history, all_results)
                    
                    all_results.append({
                        "semester": semester.get("semester", ""),
                        "semester_index": i,
                        "course_code": course.get("code", ""),
                        "course_name": course.get("name", ""),
                        "grade": course.get("grade", ""),
                        "is_valid": is_valid,
                        "reason": reason,
                        "type": "prerequisite",
                        "student_id": student_info.get("id", ""),
                        "student_name": student_info.get("name", ""),
                        "transcript_file": "json_data"
                    })
            
            # Propagate invalidation to dependent courses
            self.validator.propagate_invalidation(semesters, all_results)
            
            return all_results
        
        except Exception as e:
            logger.error(f"Error validating transcript: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def build_passed_courses_history(self, semesters):
        """
        Build a semester-by-semester history of all passed courses.
        
        Args:
            semesters: List of semester dictionaries
            
        Returns:
            List of dictionaries mapping course codes to grades
        """
        passing_grades = {"A", "B+", "B", "C+", "C", "D+", "D", "P"}
        passed_courses_history = []
        cumulative_passed = {}
        
        # Build a cumulative history of passed courses
        for semester in semesters:
            # Start with all previously passed courses
            semester_passed = dict(cumulative_passed)
            
            # Add courses passed in this semester
            for course in semester.get("courses", []):
                course_code = course.get("code", "")
                grade = course.get("grade", "")
                
                if grade in passing_grades:
                    semester_passed[course_code] = grade
                    cumulative_passed[course_code] = grade
            
            passed_courses_history.append(semester_passed)
        
        return passed_courses_history
    
    def generate_validation_report(self, student_info, semesters, validation_results):
        """
        Generate a validation report.
        
        Args:
            student_info: Dictionary with student information
            semesters: List of semester dictionaries
            validation_results: List of validation results
            
        Returns:
            Report text
        """
        if self.validator is None:
            if not self.initialize_validator():
                return "Validator not initialized - cannot generate report"
        
        try:
            # Use the validator's report generation method
            report = self.validator.generate_summary_report(
                student_info, semesters, validation_results)
            return report
        
        except Exception as e:
            logger.error(f"Error generating validation report: {e}")
            return f"Error generating report: {e}"
