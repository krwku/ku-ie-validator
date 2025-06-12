#!/usr/bin/env python3
"""
Data model for transcript information.
"""
import logging
from datetime import datetime

logger = logging.getLogger("transcript_model")

class TranscriptModel:
    """Data model for transcript information."""
    
    def __init__(self):
        """Initialize the transcript model with default values."""
        self.student_info = {
            "id": "",
            "name": "",
            "field_of_study": "",
            "date_admission": ""
        }
        
        self.semesters = []
        self.current_semester_index = 0
        self.current_file_path = None
        self.changed = False
    
    def reset(self):
        """Reset to a new empty transcript."""
        self.student_info = {
            "id": "",
            "name": "",
            "field_of_study": "",
            "date_admission": ""
        }
        self.semesters = []
        self.current_semester_index = 0
        self.current_file_path = None
        self.changed = False
        
        logger.info("Transcript model reset to empty state")
    
    def set_changed(self, changed=True):
        """Mark data as changed."""
        self.changed = changed
    
    def get_current_semester(self):
        """Get the current semester or None if no semesters exist."""
        if not self.semesters or self.current_semester_index >= len(self.semesters):
            return None
        return self.semesters[self.current_semester_index]
    
    def add_semester(self):
        """
        Add a new semester to the transcript.
        
        Returns:
            The newly created semester
        """
        # Default to next logical semester
        next_type = "First"
        next_year = datetime.now().year
        
        if self.semesters:
            # Try to determine next logical semester
            last_semester = self.semesters[-1]
            last_type = last_semester.get("semester_type", "")
            last_year = last_semester.get("year", str(datetime.now().year))
            
            try:
                last_year_int = int(last_year)
            except ValueError:
                last_year_int = datetime.now().year
            
            if last_type == "First":
                next_type = "Second"
                next_year = last_year_int
            elif last_type == "Second":
                next_type = "Summer"
                next_year = last_year_int
            elif last_type == "Summer":
                next_type = "First"
                next_year = last_year_int + 1
        
        # Create new semester
        new_semester = {
            "semester": f"{next_type} {next_year}",
            "semester_type": next_type,
            "year": str(next_year),
            "year_int": next_year,
            "semester_order": 1 if next_type == "First" else (2 if next_type == "Second" else 0),
            "courses": [],
            "sem_gpa": None,
            "cum_gpa": None,
            "total_credits": 0
        }
        
        # Add to list of semesters
        self.semesters.append(new_semester)
        self.current_semester_index = len(self.semesters) - 1
        self.set_changed()
        
        logger.info(f"Added new semester: {new_semester['semester']}")
        return new_semester
    
    def delete_semester(self, index=None):
        """
        Delete a semester from the transcript.
        
        Args:
            index: Index of the semester to delete (defaults to current semester)
            
        Returns:
            True if the semester was deleted, False otherwise
        """
        if index is None:
            index = self.current_semester_index
        
        if not self.semesters or index >= len(self.semesters):
            logger.warning("Cannot delete semester - invalid index")
            return False
        
        # Delete the semester
        deleted = self.semesters.pop(index)
        
        # Update current semester index
        if self.semesters:
            if self.current_semester_index >= len(self.semesters):
                self.current_semester_index = len(self.semesters) - 1
        else:
            self.current_semester_index = 0
        
        self.set_changed()
        logger.info(f"Deleted semester: {deleted.get('semester', '')}")
        return True
    
    def move_semester_up(self, index=None):
        """
        Move a semester up in the list (earlier in time).
        
        Args:
            index: Index of the semester to move (defaults to current semester)
            
        Returns:
            True if the semester was moved, False otherwise
        """
        if index is None:
            index = self.current_semester_index
        
        if not self.semesters or index >= len(self.semesters) or index == 0:
            return False
        
        # Swap with previous semester
        self.semesters[index], self.semesters[index-1] = \
            self.semesters[index-1], self.semesters[index]
        
        # Update current semester index
        if index == self.current_semester_index:
            self.current_semester_index -= 1
        
        self.set_changed()
        logger.info(f"Moved semester up: {self.semesters[index-1].get('semester', '')}")
        return True
    
    def move_semester_down(self, index=None):
        """
        Move a semester down in the list (later in time).
        
        Args:
            index: Index of the semester to move (defaults to current semester)
            
        Returns:
            True if the semester was moved, False otherwise
        """
        if index is None:
            index = self.current_semester_index
        
        if not self.semesters or index >= len(self.semesters) - 1:
            return False
        
        # Swap with next semester
        self.semesters[index], self.semesters[index+1] = \
            self.semesters[index+1], self.semesters[index]
        
        # Update current semester index
        if index == self.current_semester_index:
            self.current_semester_index += 1
        
        self.set_changed()
        logger.info(f"Moved semester down: {self.semesters[index+1].get('semester', '')}")
        return True
    
    def update_semester(self, index, data):
        """
        Update semester data.
        
        Args:
            index: Index of the semester to update
            data: Dictionary with semester data to update
            
        Returns:
            True if the semester was updated, False otherwise
        """
        if not self.semesters or index >= len(self.semesters):
            return False
        
        semester = self.semesters[index]
        
        # Update fields
        for key, value in data.items():
            semester[key] = value
        
        # Update semester display name
        semester_type = semester.get("semester_type", "")
        year = semester.get("year", "")
        if semester_type and year:
            semester["semester"] = f"{semester_type} {year}"
        
        # Update year_int
        try:
            year_int = int(year)
            semester["year_int"] = year_int
        except (ValueError, TypeError):
            semester["year_int"] = 0
        
        # Update semester_order
        if semester_type == "Summer":
            semester["semester_order"] = 0
        elif semester_type == "First":
            semester["semester_order"] = 1
        elif semester_type == "Second":
            semester["semester_order"] = 2
        else:
            semester["semester_order"] = 3
        
        self.set_changed()
        logger.info(f"Updated semester: {semester['semester']}")
        return True
    
    def add_course(self, semester_index, course_data):
        """
        Add a course to a semester.
        
        Args:
            semester_index: Index of the semester to add to
            course_data: Dictionary with course data
            
        Returns:
            True if the course was added, False otherwise
        """
        if not self.semesters or semester_index >= len(self.semesters):
            return False
        
        # Add course to semester
        self.semesters[semester_index]["courses"].append(course_data)
        
        # Recalculate total credits
        self.recalculate_semester_credits(semester_index)
        
        self.set_changed()
        logger.info(f"Added course {course_data.get('code', '')} to semester {self.semesters[semester_index].get('semester', '')}")
        return True
    
    def update_course(self, semester_index, course_index, course_data):
        """
        Update a course.
        
        Args:
            semester_index: Index of the semester
            course_index: Index of the course
            course_data: Dictionary with course data to update
            
        Returns:
            True if the course was updated, False otherwise
        """
        if not self.semesters or semester_index >= len(self.semesters):
            return False
        
        courses = self.semesters[semester_index].get("courses", [])
        if course_index >= len(courses):
            return False
        
        # Update course
        courses[course_index] = course_data
        
        # Recalculate total credits
        self.recalculate_semester_credits(semester_index)
        
        self.set_changed()
        logger.info(f"Updated course {course_data.get('code', '')} in semester {self.semesters[semester_index].get('semester', '')}")
        return True
    
    def delete_course(self, semester_index, course_index):
        """
        Delete a course from a semester.
        
        Args:
            semester_index: Index of the semester
            course_index: Index of the course
            
        Returns:
            True if the course was deleted, False otherwise
        """
        if not self.semesters or semester_index >= len(self.semesters):
            return False
        
        courses = self.semesters[semester_index].get("courses", [])
        if course_index >= len(courses):
            return False
        
        # Delete course
        deleted = courses.pop(course_index)
        
        # Recalculate total credits
        self.recalculate_semester_credits(semester_index)
        
        self.set_changed()
        logger.info(f"Deleted course {deleted.get('code', '')} from semester {self.semesters[semester_index].get('semester', '')}")
        return True
    
    def recalculate_semester_credits(self, semester_index):
        """
        Recalculate total credits for a semester.
        
        Args:
            semester_index: Index of the semester
        """
        if not self.semesters or semester_index >= len(self.semesters):
            return
        
        semester = self.semesters[semester_index]
        total_credits = 0
        
        for course in semester.get("courses", []):
            # Only count credits for non-withdrawn courses
            if course.get("grade") not in ['W', 'N']:
                total_credits += course.get("credits", 0)
        
        semester["total_credits"] = total_credits
        logger.debug(f"Recalculated credits for semester {semester.get('semester', '')}: {total_credits}")
    
    def to_dict(self):
        """
        Convert model to dictionary for saving.
        
        Returns:
            Dictionary representation of the model
        """
        return {
            "student_info": self.student_info,
            "semesters": self.semesters
        }
    
    def from_dict(self, data):
        """
        Load model from dictionary.
        
        Args:
            data: Dictionary with transcript data
        """
        if "student_info" in data and isinstance(data["student_info"], dict):
            self.student_info = data["student_info"]
        
        if "semesters" in data and isinstance(data["semesters"], list):
            self.semesters = data["semesters"]
            self.current_semester_index = 0 if self.semesters else 0
