#!/usr/bin/env python3
"""
PDF extraction functionality for reading transcript PDFs.
"""
import re
import logging
import PyPDF2
from datetime import datetime

logger = logging.getLogger("pdf_extractor")

class PDFExtractor:
    """Class for extracting and processing text from PDF transcripts."""
    
    def __init__(self):
        """Initialize the PDF extractor."""
        pass
    
    def extract_text_from_pdf(self, pdf_path):
        """
        Extract text content from PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        try:
            all_text = []
            
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                for page in reader.pages:
                    # Extract text from the page
                    page_text = page.extract_text()
                    
                    # Skip pages with no text content
                    if not page_text or page_text.strip() == "":
                        continue
                    
                    all_text.append(page_text)
            
            # Join all text
            return "\n".join(all_text)
        
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def extract_student_info(self, text):
            """
            Extract student information from the extracted text.
            
            Args:
                text: Extracted text from PDF
                
            Returns:
                Dictionary containing student information
            """
            # Extract student ID
            student_id = "Unknown"
            id_match = re.search(r'Student No\s*(\d+)', text)
            if id_match:
                student_id = id_match.group(1).strip()
            
            # Extract name - stop at "Field of Study" 
            student_name = "Unknown"
            name_match = re.search(r'Name\s+(.*?)(?=Field of Study|Date of Admission|\n|$)', text)
            if name_match:
                student_name = name_match.group(1).strip()
            
            # Extract field of study
            field_of_study = "Unknown"
            field_match = re.search(r'Field of Study\s+(.*?)(?=Date of Admission|\n|$)', text)
            if field_match:
                field_of_study = field_match.group(1).strip()
            
            # Extract date of admission
            date_admission = "Unknown"
            date_match = re.search(r'Date of Admission\s+(.*?)(?:\n|$)', text)
            if date_match:
                date_admission = date_match.group(1).strip()
            
            return {
                "id": student_id,
                "name": student_name,
                "field_of_study": field_of_study,
                "date_admission": date_admission
            }
    
    def extract_semesters(self, text):
        """
        Extract semester data from the extracted text (improved version).
        """
        # More flexible patterns
        semester_patterns = [
            r'(First|Second)\s*Semester\s*(\d{4})',     # Handles missing spaces
            r'Summer\s*Session\s*(\d{4})',              # Summer with flexible spacing
            r'(First|Second|Summer)\s*(\d{4})'          # Alternative format
        ]
        
        # Improved course pattern - more flexible with spacing
        course_patterns = [
            # Try original pattern first
            r'(\d{8})\s+([\w\s&\'\-\+\.\,\/\(\)]+?)\s+([A-Z\+\-]+)\s+(\d+)',
            # Pattern with flexible spacing
            r'(\d{8})\s*([\w\s&\'\-\+\.\,\/\(\)]+?)\s*([A-Z\+\-]+)\s*(\d+)',
            # Pattern for concatenated text
            r'(\d{8})([A-Za-z][^0-9]*?)([A-Z\+\-]+)(\d+)'
        ]
        
        gpa_pattern = r'sem\.\s*G\.P\.A\.\s*=\s*(\d+\.\d+).*?cum\.\s*G\.P\.A\.\s*=\s*(\d+\.\d+)'
        
        # Preprocessing - fix common spacing issues
        text = re.sub(r'(First|Second)Semester', r'\1 Semester', text)
        text = re.sub(r'SummerSession', r'Summer Session', text)
        text = re.sub(r'(\d{8})([A-Za-z])', r'\1 \2', text)  # Add space after course code
        
        # Debug: Log first 500 chars of processed text
        logger.debug(f"Processing text (first 500 chars): {text[:500]}")
        
        semesters = []
        current_semester = None
        
        lines = text.split('\n')
        logger.debug(f"Total lines to process: {len(lines)}")
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines and URLs
            if not line or "http" in line.lower() or ".php" in line.lower():
                continue
            
            # Try semester patterns
            semester_found = False
            for pattern_num, pattern in enumerate(semester_patterns):
                semester_match = re.search(pattern, line, re.IGNORECASE)
                if semester_match:
                    logger.debug(f"Found semester on line {line_num}: {line}")
                    
                    if current_semester:
                        semesters.append(current_semester)
                    
                    # Extract semester type and year
                    groups = semester_match.groups()
                    if len(groups) == 2:
                        if "Summer" in semester_match.group(0):
                            semester_type = "Summer"
                            year = groups[1] if groups[1] else groups[0]
                        else:
                            semester_type = groups[0]
                            year = groups[1]
                    else:
                        # Handle single group matches
                        if "Summer" in line:
                            semester_type = "Summer"
                            year = groups[0]
                        else:
                            # Extract from the full match
                            full_match = semester_match.group(0)
                            year_match = re.search(r'\d{4}', full_match)
                            year = year_match.group(0) if year_match else "Unknown"
                            semester_type = "First" if "First" in full_match else ("Second" if "Second" in full_match else "Unknown")
                    
                    current_semester = {
                        "semester": f"{semester_type} {year}",
                        "semester_type": semester_type,
                        "year": year,
                        "year_int": int(year) if year.isdigit() else 0,
                        "courses": [],
                        "sem_gpa": None,
                        "cum_gpa": None,
                        "total_credits": 0,
                        "semester_order": 0 if semester_type == "Summer" else (1 if semester_type == "First" else 2)
                    }
                    
                    logger.debug(f"Created semester: {current_semester['semester']}")
                    semester_found = True
                    break
            
            if semester_found:
                continue
            
            # Try GPA pattern
            gpa_match = re.search(gpa_pattern, line, re.IGNORECASE)
            if gpa_match and current_semester:
                try:
                    current_semester["sem_gpa"] = float(gpa_match.group(1))
                    current_semester["cum_gpa"] = float(gpa_match.group(2))
                    logger.debug(f"Found GPA: sem={gpa_match.group(1)}, cum={gpa_match.group(2)}")
                except (ValueError, IndexError):
                    pass
                continue
            
            # Try course patterns
            if current_semester:
                course_found = False
                for pattern_num, pattern in enumerate(course_patterns):
                    course_match = re.search(pattern, line)
                    if course_match:
                        try:
                            groups = course_match.groups()
                            course_code = groups[0]
                            course_name = groups[1].strip()
                            grade = groups[2].strip() if len(groups) > 2 and groups[2] else ""
                            credits_str = groups[3] if len(groups) > 3 else "0"
                            
                            # Clean up course name
                            course_name = re.sub(r'\s+', ' ', course_name)
                            
                            # Parse credits
                            credits = int(credits_str) if credits_str.isdigit() else 0
                            
                            course_data = {
                                "code": course_code,
                                "name": course_name,
                                "grade": grade,
                                "credits": credits
                            }
                            
                            current_semester["courses"].append(course_data)
                            
                            # Count credits for non-withdrawn courses
                            if grade not in ['W', 'N']:
                                current_semester["total_credits"] += credits
                            
                            logger.debug(f"Found course: {course_code} - {course_name} - {grade} - {credits}")
                            course_found = True
                            break
                            
                        except Exception as e:
                            logger.debug(f"Error parsing course from line '{line}': {e}")
                            continue
                
                if not course_found:
                    # Try to find course codes even if full pattern doesn't match
                    code_match = re.search(r'(\d{8})', line)
                    if code_match:
                        logger.debug(f"Found course code but couldn't parse full line: {line}")
        
        # Add the last semester
        if current_semester:
            semesters.append(current_semester)
            logger.debug(f"Added final semester: {current_semester['semester']}")
        
        logger.debug(f"Total semesters extracted: {len(semesters)}")
        for sem in semesters:
            logger.debug(f"Semester {sem['semester']}: {len(sem['courses'])} courses")
        
        return semesters
    
    def process_pdf(self, pdf_path, text=None):
        """
        Process a PDF transcript and extract all data.
        
        Args:
            pdf_path: Path to the PDF file
            text: Optional pre-extracted text (used instead of extracting from PDF)
            
        Returns:
            Tuple of (student_info, semesters, extracted_text)
        """
        # Use provided text or extract from PDF
        if text is not None:
            extracted_text = text
        else:
            extracted_text = self.extract_text_from_pdf(pdf_path)
        
        if not extracted_text:
            logger.error("No text extracted from PDF")
            return {}, [], ""
        
        # Extract student info
        student_info = self.extract_student_info(extracted_text)
        
        # Extract semesters
        semesters = self.extract_semesters(extracted_text)
        
        return student_info, semesters, extracted_text
