import json
import os
import sys
from typing import Dict, List, Tuple, Set, Any, Optional
from datetime import datetime
import logging

# Configure logging
log_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_directory, exist_ok=True)
log_file_path = os.path.join(log_directory, "validator.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file_path)
    ]
)
logger = logging.getLogger("course_validator")

class CourseRegistrationValidator:
    """
    Improved validator for course registrations based on university rules.
    """
    def __init__(self, course_data_path: str):
        """Initialize the validator with course data."""
        self.course_data = self.load_course_data(course_data_path)
        self.all_courses = {}
        
        # Create a flattened dictionary of all courses for easy lookup
        for course in self.course_data.get("industrial_engineering_courses", []):
            self.all_courses[course["code"]] = course
        
        for course in self.course_data.get("other_related_courses", []):
            self.all_courses[course["code"]] = course
            
        logger.info(f"Loaded {len(self.all_courses)} courses from course data")
    
    def load_course_data(self, json_file_path: str) -> Dict:
        """Load course data from JSON file."""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            logger.error(f"Course data file not found: {json_file_path}")
            sys.exit(1)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in file: {json_file_path}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading course data from {json_file_path}: {e}")
            sys.exit(1)
    
    def build_passed_courses_history(self, semesters: List[Dict]) -> List[Dict[str, str]]:
        """
        Build a semester-by-semester history of all passed courses.
        
        Args:
            semesters: List of all semesters
            
        Returns:
            List of dictionaries with course codes and grades, one for each semester
        """
        passing_grades = {"A", "B+", "B", "C+", "C", "D+", "D", "P"}
        passed_courses_history = []
        cumulative_passed = {}
        
        # Build a cumulative history of passed courses
        for semester in semesters:
            # Start with all previously passed courses
            semester_passed = dict(cumulative_passed)
            
            # Add courses passed in this semester
            for course in semester["courses"]:
                course_code = course["code"]
                grade = course["grade"]
                
                if grade in passing_grades:
                    semester_passed[course_code] = grade
                    cumulative_passed[course_code] = grade
            
            passed_courses_history.append(semester_passed)
        
        return passed_courses_history
    
    def get_passed_courses_before_semester(self, semester_index: int, passed_courses_history: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Get all courses passed before a specific semester.
        
        Args:
            semester_index: Index of the current semester
            passed_courses_history: List of passed courses per semester
            
        Returns:
            Dictionary of courses passed before the given semester
        """
        if semester_index == 0:
            # No courses passed before the first semester
            return {}
        
        # Return courses passed up to the previous semester
        return passed_courses_history[semester_index - 1]
    
    def get_courses_in_semester(self, semester: Dict) -> Dict[str, str]:
        """
        Get all courses being taken in a specific semester.
        
        Args:
            semester: The semester to check
            
        Returns:
            Dictionary with course codes as keys and grades as values
        """
        courses_in_semester = {}
        for course in semester["courses"]:
            courses_in_semester[course["code"]] = course["grade"]
        return courses_in_semester
    
    def has_failed_before(self, course_code: str, semesters: List[Dict], semester_index: int) -> bool:
        """
        Check if a course has been failed before a specific semester.
        
        Args:
            course_code: The course code to check
            semesters: List of all semesters
            semester_index: Index of the current semester
            
        Returns:
            True if the course has been failed before, False otherwise
        """
        for i in range(semester_index):
            for course in semesters[i]["courses"]:
                if course["code"] == course_code and course["grade"] == "F":
                    return True
        return False
    
    def is_taking_in_semester(self, course_code: str, semester: Dict) -> bool:
        """
        Check if a student is taking a specific course in a semester.
        
        Args:
            course_code: The course code to check
            semester: The semester to check
            
        Returns:
            True if the student is taking the course, False otherwise
        """
        for course in semester["courses"]:
            if course["code"] == course_code:
                return True
        return False
    
    def has_withdrawn_before(self, course_code: str, semesters: List[Dict], semester_index: int) -> bool:
        """
        Check if a course has been withdrawn before a specific semester.
        
        Args:
            course_code: The course code to check
            semesters: List of all semesters
            semester_index: Index of the current semester
            
        Returns:
            True if the course has been withdrawn before, False otherwise
        """
        for i in range(semester_index):
            for course in semesters[i]["courses"]:
                if course["code"] == course_code and course["grade"] == "W":
                    return True
        return False
    
    def get_invalid_courses(self, semester_index: int, validation_results: List[Dict]) -> Set[str]:
        """
        Get a set of course codes that have been marked as invalid in the current semester.
        
        Args:
            semester_index: Index of the current semester
            validation_results: List of validation results
            
        Returns:
            Set of invalid course codes
        """
        invalid_courses = set()
        
        for result in validation_results:
            # Skip credit limit validations
            if result.get("course_code") == "CREDIT_LIMIT":
                continue
            
            # Only consider results for the current semester
            if result.get("semester_index") == semester_index and not result.get("is_valid", True):
                invalid_courses.add(result.get("course_code"))
        
        return invalid_courses
    
    def check_prerequisite_group_satisfied(self, 
                                          prereq_group: Dict, 
                                          passed_courses_before: Dict[str, str], 
                                          current_semester: Dict, 
                                          semesters: List[Dict], 
                                          semester_index: int,
                                          invalid_courses: Set[str]) -> Tuple[bool, str]:
        """
        Check if a prerequisite group is satisfied.
        
        Args:
            prereq_group: The prerequisite group to check
            passed_courses_before: Courses passed before this semester
            current_semester: The current semester
            semesters: List of all semesters
            semester_index: Index of the current semester
            invalid_courses: Set of invalid courses in current semester
            
        Returns:
            Tuple of (is_satisfied, reason)
        """
        # Get list of courses in this prerequisite group
        req_courses = prereq_group.get("courses", [])
        
        # If no courses are required, the group is satisfied
        if not req_courses:
            return True, "No prerequisites required"
            
        # Check if concurrent enrollment is allowed for this group
        concurrent_allowed = prereq_group.get("concurrent_allowed", False)
        
        # Check each required course in the group
        for prereq_code in req_courses:
            # Case 1: Course has been passed before
            if prereq_code in passed_courses_before:
                continue
                
            # Case 2: Concurrent enrollment is allowed and student is taking the course
            if concurrent_allowed and self.is_taking_in_semester(prereq_code, current_semester):
                # If the prerequisite is being taken concurrently but is already marked as invalid,
                # then this course is also invalid
                if prereq_code in invalid_courses:
                    return False, f"Prerequisite {prereq_code} is invalid in current semester"
                    
                # Valid concurrent enrollment
                continue
                
            # Case 3: Special case for concurrent registration after failing
            if concurrent_allowed and self.has_failed_before(prereq_code, semesters, semester_index) and self.is_taking_in_semester(prereq_code, current_semester):
                continue
                
            # If we get here, the prerequisite is not satisfied
            if concurrent_allowed:
                return False, f"Prerequisite {prereq_code} not satisfied (not passed before and not taking concurrently)"
            else:
                return False, f"Prerequisite {prereq_code} not satisfied"
        
        # If we get here, all prerequisites in this group are satisfied
        return True, "All prerequisites in group satisfied"
    
    def validate_course(self, course: Dict, semester_index: int, semesters: List[Dict], 
                        passed_courses_history: List[Dict[str, str]], validation_results: List[Dict]) -> Tuple[bool, str]:
        """
        Validate prerequisites for a course.
        
        Args:
            course: The course to validate
            semester_index: Index of the current semester
            semesters: List of all semesters
            passed_courses_history: History of passed courses per semester
            validation_results: Current validation results (to check if prerequisites are valid)
            
        Returns:
            Tuple of (is_valid, reason)
        """
        course_code = course["code"]
        grade = course["grade"]
        current_semester = semesters[semester_index]
        
        logger.debug(f"Validating {course_code} in {current_semester['semester']}")
        
        # Skip validation for withdrawn courses
        if grade == "W":
            return True, "Course was withdrawn"
            
        # Skip validation for N grade (not graded yet) courses
        if grade == "N":
            return True, "Course not graded yet"
        
        # Get course info from data
        course_info = self.all_courses.get(course_code)
        
        # If course not found in data, validation passes
        if not course_info:
            logger.debug(f"Course {course_code} not found in course data")
            return True, f"Course {course_code} not found in course data"
        
        # Get passed courses before this semester
        passed_courses_before = self.get_passed_courses_before_semester(semester_index, passed_courses_history)
        
        # Get the list of invalid courses in this semester so far
        invalid_courses = self.get_invalid_courses(semester_index, validation_results)
        
        # Create a mapping of withdrawn courses in this semester
        withdrawn_courses = set()
        for c in current_semester.get("courses", []):
            if c.get("grade") == "W":
                withdrawn_courses.add(c.get("code"))
        
        logger.debug(f"Passed courses before: {passed_courses_before}")
        logger.debug(f"Invalid courses so far: {invalid_courses}")
        logger.debug(f"Withdrawn courses in this semester: {withdrawn_courses}")
        
        # Check if the course has prerequisite groups defined
        if "prerequisite_groups" in course_info and course_info["prerequisite_groups"]:
            # Course uses the new prerequisite groups structure
            # At least one group must be satisfied
            logger.debug(f"Course {course_code} has prerequisite groups")
            
            for group_idx, prereq_group in enumerate(course_info["prerequisite_groups"]):
                is_satisfied, reason = self.check_prerequisite_group_satisfied(
                    prereq_group, 
                    passed_courses_before, 
                    current_semester, 
                    semesters, 
                    semester_index,
                    invalid_courses
                )
                
                if is_satisfied:
                    logger.debug(f"Prerequisite group {group_idx} is satisfied: {reason}")
                    return True, f"Prerequisite group satisfied: {reason}"
            
            # If we get here, none of the prerequisite groups are satisfied
            return False, "No prerequisite groups are satisfied"
        
        # Legacy prerequisite validation using the old structure
        if not course_info.get("prerequisites"):
            logger.debug(f"Course {course_code} has no prerequisites")
            return True, "No prerequisites required"
            
        # Check each prerequisite
        for prereq_code in course_info.get("prerequisites", []):
            logger.debug(f"Checking prerequisite: {prereq_code}")
            
            # Case 1: Prerequisite has been passed before this semester
            if prereq_code in passed_courses_before:
                logger.debug(f"Prerequisite {prereq_code} has been passed with grade {passed_courses_before[prereq_code]}")
                continue
            
            # Case 2: The prerequisite is being withdrawn in the current semester
            if prereq_code in withdrawn_courses:
                return False, f"Prerequisite {prereq_code} was withdrawn (W) in this semester"
            
            # Case 3: Prerequisites are being taken concurrently
            if self.is_taking_in_semester(prereq_code, current_semester):
                # If the prerequisite is being taken concurrently but is already marked as invalid,
                # then this course is also invalid
                if prereq_code in invalid_courses:
                    return False, f"Prerequisite {prereq_code} is invalid in current semester"
                
                # Only allow concurrent registration if the student has failed the prerequisite before
                if self.has_failed_before(prereq_code, semesters, semester_index):
                    logger.debug(f"Prerequisite {prereq_code} failed before and taking now - eligible for concurrent registration")
                    continue
                
                # If the student has withdrawn from the prerequisite before, they're not eligible
                # for concurrent registration
                if self.has_withdrawn_before(prereq_code, semesters, semester_index):
                    return False, f"Prerequisite {prereq_code} withdrawn before - not eligible for concurrent registration"
                
                # If neither failed nor withdrawn, prerequisite is not satisfied
                return False, f"Prerequisite {prereq_code} not satisfied for concurrent registration"
            
            # If we get here, the prerequisite is not satisfied
            return False, f"Prerequisite {prereq_code} not satisfied and not eligible for concurrent registration"
        
        # All prerequisites satisfied
        return True, "All prerequisites satisfied or eligible for concurrent registration"
    
    def validate_credit_limit(self, semester: Dict) -> Tuple[bool, str]:
        """
        Validate credit limit for a semester.
        Returns tuple of (is_valid, reason).
        Credit limits are just warnings, not errors.
        """
        total_credits = semester["total_credits"]
        semester_type = semester["semester_type"]
        
        if semester_type == "Summer":
            if total_credits > 9:
                return False, f"NOTICE: Exceeds typical 9 credits for summer (registered: {total_credits})"
        else:  # Regular semester
            if total_credits > 22:
                return False, f"NOTICE: Exceeds typical 22 credits for regular semester (registered: {total_credits})"
        
        return True, f"Credit limit valid: {total_credits} credits"
    
    def propagate_invalidation(self, semesters: List[Dict], validation_results: List[Dict]) -> None:
        """
        Propagate invalidation from invalid courses to their dependent courses.
        This handles the chain reaction of invalid prerequisites.
        
        Rules:
        1. If a prerequisite is withdrawn (W) in the same semester, dependent courses are invalid
        2. If a prerequisite is failed (F) in the same semester, dependent courses remain valid (concurrent registration)
        3. If a prerequisite is invalid from previous validation, all dependent courses are invalid
        """
        logger.debug("Starting invalidation propagation...")
        
        # Map course codes to their validation results
        course_results = {}
        for result in validation_results:
            if result.get("course_code") != "CREDIT_LIMIT":
                key = (result.get("course_code"), result.get("semester_index"))
                course_results[key] = result
        
        # Create a map of courses to their prerequisites (combining old and new formats)
        course_prereqs = {}
        for semester_index, semester in enumerate(semesters):
            for course in semester.get("courses", []):
                course_code = course.get("code")
                course_info = self.all_courses.get(course_code, {})
                
                if course_info:
                    prereqs = set()
                    
                    # Add prerequisites from the old format
                    if "prerequisites" in course_info and course_info["prerequisites"]:
                        prereqs.update(course_info["prerequisites"])
                    
                    # Add prerequisites from the new prerequisite_groups format
                    if "prerequisite_groups" in course_info:
                        for group in course_info.get("prerequisite_groups", []):
                            prereqs.update(group.get("courses", []))
                    
                    if prereqs:
                        course_prereqs[(course_code, semester_index)] = list(prereqs)
        
        # Create a mapping of withdrawn courses in each semester
        # We specifically track withdrawn courses not failed courses as per requirement
        withdrawn_courses = {}
        for semester_index, semester in enumerate(semesters):
            withdrawn_courses[semester_index] = set()
            for course in semester.get("courses", []):
                if course.get("grade") == "W":
                    withdrawn_courses[semester_index].add(course.get("code"))
        
        # Propagate invalidation
        iterations = 0
        changes_made = True
        
        while changes_made and iterations < 10:  # Limit iterations to prevent infinite loops
            iterations += 1
            changes_made = False
            logger.debug(f"Propagation iteration {iterations}")
            
            for (course_code, semester_index), prereqs in course_prereqs.items():
                # Skip if this course is already invalid
                result_key = (course_code, semester_index)
                if result_key not in course_results or not course_results[result_key].get("is_valid", True):
                    continue
                
                # Get the course with this code in this semester
                semester = semesters[semester_index]
                course = next((c for c in semester.get("courses", []) if c.get("code") == course_code), None)
                
                # Skip courses not graded yet
                if not course or course.get("grade") == "N":
                    continue
                
                # Handle within-semester dependencies specifically for withdrawn courses
                # If a prerequisite was withdrawn in the same semester, the course is invalid
                for prereq_code in prereqs:
                    # Check if the prerequisite was withdrawn in the same semester
                    if prereq_code in withdrawn_courses.get(semester_index, set()):
                        logger.debug(f"Marking {course_code} in semester {semester_index} as invalid because prerequisite {prereq_code} was withdrawn (W) in this semester")
                        course_results[result_key]["is_valid"] = False
                        course_results[result_key]["reason"] = f"Prerequisite {prereq_code} was withdrawn (W) or failed (F) in this semester"
                        changes_made = True
                        break
                
                # Skip withdrawn courses after handling within-semester dependencies
                if course.get("grade") == "W":
                    continue
                
                # Check if any prerequisite is invalid in current or previous semesters
                for prereq_code in prereqs:
                    prereq_invalid = False
                    invalid_semester = None
                    
                    # Check current and all previous semesters
                    for i in range(semester_index + 1):
                        prereq_key = (prereq_code, i)
                        
                        # If prerequisite exists in this semester and is invalid
                        if prereq_key in course_results and not course_results[prereq_key].get("is_valid", True):
                            prereq_invalid = True
                            invalid_semester = i
                            break
                    
                    if prereq_invalid:
                        # Mark this course as invalid
                        logger.debug(f"Marking {course_code} in semester {semester_index} as invalid because prerequisite {prereq_code} is invalid in semester {invalid_semester}")
                        course_results[result_key]["is_valid"] = False
                        course_results[result_key]["reason"] = f"Prerequisite {prereq_code} is invalid"
                        changes_made = True
                        break
        
        logger.debug(f"Invalidation propagation completed after {iterations} iterations")
    
    def calculate_cumulative_gpa(self, semesters, up_to_index):
        """
        Calculate cumulative GPA up to and including the specified semester index.
        
        Args:
            semesters: List of all semesters
            up_to_index: Index of the last semester to include
            
        Returns:
            Cumulative GPA as float
        """
        all_courses = []
        for i in range(up_to_index + 1):
            all_courses.extend(semesters[i].get("courses", []))
        
        cumulative_gpa, _ = self.calculate_gpa(all_courses)
        return cumulative_gpa
    
    def calculate_valid_cumulative_gpa(self, semesters, validation_results, up_to_index):
        """
        Calculate cumulative GPA for valid courses up to and including the specified semester index.
        
        Args:
            semesters: List of all semesters
            validation_results: List of validation results
            up_to_index: Index of the last semester to include
            
        Returns:
            Cumulative GPA of valid courses as float
        """
        valid_courses = []
        
        for i in range(up_to_index + 1):
            # Get valid course codes for this semester
            results_for_semester = [r for r in validation_results 
                                  if r.get("semester_index") == i and r.get("course_code") != "CREDIT_LIMIT"]
            valid_course_codes = {r.get("course_code") for r in results_for_semester if r.get("is_valid", True)}
            
            # Add valid courses to the list
            valid_courses.extend([c for c in semesters[i].get("courses", []) 
                                if c.get("code") in valid_course_codes])
        
        cumulative_gpa, _ = self.calculate_gpa(valid_courses)
        return cumulative_gpa
    
    def calculate_gpa(self, courses):
        """
        Calculate GPA using weighted average.
        
        Args:
            courses: List of course dictionaries
        
        Returns:
            Tuple of (GPA, total_credits_counted)
        """
        grade_points = {
            "A": 4.0,
            "B+": 3.5,
            "B": 3.0,
            "C+": 2.5,
            "C": 2.0,
            "D+": 1.5,
            "D": 1.0,
            "F": 0.0
        }
        
        total_points = 0.0
        total_credits = 0
        
        for course in courses:
            grade = course.get("grade", "")
            credits = course.get("credits", 0)
            
            # Skip grades that don't contribute to GPA (W, P, N, etc.)
            if grade not in grade_points:
                continue
            
            # Calculate points for this course
            points = grade_points[grade] * credits
            total_points += points
            total_credits += credits
        
        # Calculate GPA
        if total_credits > 0:
            gpa = total_points / total_credits
            return round(gpa, 2), total_credits
        else:
            return 0.0, 0
    
    def generate_summary_report(self, student_info: Dict, semesters: List[Dict], validation_results: List[Dict]) -> str:
        """
        Generate a comprehensive summary report of validation results.
        """
        report_lines = []
        
        # Report header
        report_lines.append("="*80)
        report_lines.append(f"COURSE REGISTRATION VALIDATION REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("="*80)
        report_lines.append("")
        
        # Student information section
        report_lines.append("STUDENT INFORMATION")
        report_lines.append("-"*80)
        report_lines.append(f"Student ID:       {student_info.get('id', 'Unknown')}")
        report_lines.append(f"Name:             {student_info.get('name', 'Unknown')}")
        report_lines.append(f"Field of Study:   {student_info.get('field_of_study', 'Unknown')}")
        report_lines.append(f"Date of Admission: {student_info.get('date_admission', 'Unknown')}")
        
        # Academic Status
        if semesters:
            last_semester = semesters[-1]
            current_gpa = last_semester.get("cum_gpa", "N/A")
            report_lines.append(f"Current GPA:      {current_gpa}")
            
            # Determine academic status based on GPA
            if isinstance(current_gpa, (int, float)) or (isinstance(current_gpa, str) and current_gpa != "N/A"):
                current_gpa = float(current_gpa) if isinstance(current_gpa, str) else current_gpa
                
                if current_gpa < 1.50:
                    report_lines.append(f"Academic Status:  CRITICAL (GPA < 1.50)")
                elif current_gpa < 1.75:
                    report_lines.append(f"Academic Status:  WARNING (GPA < 1.75)")
                elif current_gpa < 2.00:
                    report_lines.append(f"Academic Status:  PROBATION (GPA < 2.00)")
                else:
                    report_lines.append(f"Academic Status:  NORMAL")
        
        report_lines.append("")
        
        # Validation Summary
        invalid_count = len([r for r in validation_results if not r.get("is_valid", True)])
        report_lines.append("VALIDATION SUMMARY")
        report_lines.append("-"*80)
        report_lines.append(f"Semesters Analyzed:    {len(semesters)}")
        report_lines.append(f"Registrations Checked: {len(validation_results)}")
        report_lines.append(f"Invalid Registrations: {invalid_count}")
        report_lines.append("")
        
        # Semester Details
        report_lines.append("SEMESTER DETAILS")
        report_lines.append("-"*80)
        
        for i, semester in enumerate(semesters):
            semester_name = semester.get("semester", f"Semester {i+1}")
            report_lines.append(f"\n{semester_name}")
            report_lines.append("-" * len(semester_name))
            
            # Calculate total registered credits (including invalid)
            total_registered_credits = sum(c.get("credits", 0) for c in semester.get("courses", [])
                                         if c.get("grade") != "W")  # Exclude withdrawn courses
            
            # Calculate recalculated semester GPAs
            semester_gpa, _ = self.calculate_gpa(semester.get("courses", []))
            cumulative_gpa = self.calculate_cumulative_gpa(semesters, i)
            
            # Filter for valid courses only
            results_for_semester = [r for r in validation_results 
                                   if r.get("semester_index") == i and r.get("course_code") != "CREDIT_LIMIT"]
            valid_course_codes = {r.get("course_code") for r in results_for_semester if r.get("is_valid", True)}
            valid_courses = [c for c in semester.get("courses", []) if c.get("code") in valid_course_codes]
            valid_semester_gpa, _ = self.calculate_gpa(valid_courses)
            valid_cumulative_gpa = self.calculate_valid_cumulative_gpa(semesters, validation_results, i)
            
            # Credit information
            report_lines.append(f"Total Credits: {total_registered_credits}")
            
            # GPA information (recalculated)
            report_lines.append(f"Overall - Semester GPA: {semester_gpa}, Cumulative GPA: {cumulative_gpa}")
            
            # Only show valid GPA if there are any invalid courses
            if len(valid_courses) < len(semester.get("courses", [])):
                report_lines.append(f"Valid only - Semester GPA: {valid_semester_gpa}, Cumulative GPA: {valid_cumulative_gpa}")
            
            # Credit limit validation - only display notice if it's not valid
            credit_valid, credit_reason = self.validate_credit_limit(semester)
            if not credit_valid:
                report_lines.append(f"{credit_reason}")
            
            # Course table header
            report_lines.append("\nCourses:")
            report_lines.append(f"{'Code':<10} {'Name':<40} {'Grade':<7} {'Credits':<8} {'Status':<10}")
            report_lines.append("-" * 80)
            
            # List all courses for this semester
            for course in semester.get("courses", []):
                # Find validation result for this course
                result = next((r for r in validation_results 
                              if r.get("course_code") == course.get("code") and 
                                 r.get("semester") == semester.get("semester")), None)
                
                status = "INVALID" if result and not result.get("is_valid", True) else "Valid"
                
                # Format course name to fit in the column
                course_name = course.get("name", "Unknown")
                if len(course_name) > 38:
                    course_name = course_name[:35] + "..."
                
                report_lines.append(f"{course.get('code', ''):<10} {course_name:<40} {course.get('grade', ''):<7} {course.get('credits', ''):<8} {status:<10}")
                
                # If invalid, show reason
                if status == "INVALID":
                    reason = result.get("reason", "Unknown")
                    report_lines.append(f"  → Issue: {reason}")
        
        # Invalid Registrations Details
        invalid_results = [r for r in validation_results if not r.get("is_valid", True)]
        
        if invalid_results:
            report_lines.append("\n\nINVALID REGISTRATIONS DETAILS")
            report_lines.append("-"*80)
            
            # Group by semester
            by_semester = {}
            for result in invalid_results:
                semester = result.get("semester", "Unknown")
                if semester not in by_semester:
                    by_semester[semester] = []
                by_semester[semester].append(result)
            
            # Report details for each semester
            for semester, results in sorted(by_semester.items()):
                report_lines.append(f"\nSemester: {semester}")
                
                for result in results:
                    if result.get("course_code") == "CREDIT_LIMIT":
                        report_lines.append(f"  • {result.get('reason', 'Unknown')}")
                    else:
                        report_lines.append(f"  • Course: {result.get('course_code', 'Unknown')} - {result.get('course_name', 'Unknown')}")
                        report_lines.append(f"    Type: {result.get('type', 'prerequisite').capitalize()}")
                        report_lines.append(f"    Reason: {result.get('reason', 'Unknown')}")
        
        # Courses not in course data
        courses_not_in_data = []
        for semester_index, semester in enumerate(semesters):
            for course in semester.get("courses", []):
                course_code = course.get("code", "")
                if course_code and course_code not in self.all_courses:
                    semester_name = semester.get("semester", f"Semester {semester_index+1}")
                    courses_not_in_data.append({
                        "code": course_code,
                        "name": course.get("name", "Unknown"),
                        "semester": semester_name
                    })
        
        if courses_not_in_data:
            report_lines.append("\n\nCOURSES NOT IN COURSE DATA")
            report_lines.append("-"*80)
            report_lines.append("The following courses were not found in the course data file and could not be validated.")
            report_lines.append("Please check prerequisites manually for these courses:")
            report_lines.append("")
            
            report_lines.append(f"{'Code':<10} {'Name':<40} {'Semester':<20}")
            report_lines.append("-" * 70)
            
            for course in courses_not_in_data:
                # Format course name to fit in the column
                course_name = course.get("name", "Unknown")
                if len(course_name) > 38:
                    course_name = course_name[:35] + "..."
                    
                report_lines.append(f"{course.get('code', ''):<10} {course_name:<40} {course.get('semester', ''):<20}")
        
        return "\n".join(report_lines)
