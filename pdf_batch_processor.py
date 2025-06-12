#!/usr/bin/env python3
"""
Standalone PDF Transcript Batch Processor
Processes all PDF transcript files and creates columns based on course codes found, sorted numerically.
"""

import os
import sys
import re
import csv
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Set

try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not installed. Installing...")
    os.system("pip install PyPDF2")
    import PyPDF2

# Set up basic logging
logging.basicConfig(level=logging.WARNING)

class PDFTranscriptExtractor:
    """Extract transcript data from PDF files."""
    
    def __init__(self):
        self.all_course_codes = set()
        self.all_results = []
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        try:
            all_text = []
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        all_text.append(page_text)
            return "\n".join(all_text)
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def extract_student_info(self, text: str) -> Dict[str, str]:
        """Extract student information from text."""
        student_id = "Unknown"
        student_name = "Unknown"
        
        # Extract student ID
        id_patterns = [
            r'Student\s+No\s*[:\.]?\s*(\d+)',
            r'รหัสนักศึกษา\s*[:\.]?\s*(\d+)',
            r'Student\s+ID\s*[:\.]?\s*(\d+)',
            r'ID\s*[:\.]?\s*(\d+)'
        ]
        
        for pattern in id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                student_id = match.group(1).strip()
                break
        
        # Extract student name
        name_patterns = [
            r'Name\s*[:\.]?\s*([^\n\r]+?)(?=Field|Date|Student|$)',
            r'ชื่อ\s*[:\.]?\s*([^\n\r]+?)(?=สาขา|วันที่|$)',
            r'Name\s*[:\.]?\s*(.+?)(?=\n|\r|$)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up the name
                name = re.sub(r'\s+', ' ', name)
                # Remove common unwanted text
                name = re.sub(r'(Field of Study|Date of Admission).*', '', name).strip()
                if name and len(name) > 2:
                    student_name = name
                    break
        
        return {
            "id": student_id,
            "name": student_name
        }
    
    def extract_courses(self, text: str) -> Dict[str, str]:
        """Extract course codes and grades from text - improved precision."""
        courses_grades = {}
        
        # Try to find student-specific transcript section
        # Look for semester headers and course lists
        semester_patterns = [
            r'(First|Second|Summer)\s+(Semester|Session)\s+(\d{4})',
            r'ภาคเรียนที่\s*\d+.*?\d{4}',
            r'Semester\s*\d+.*?\d{4}'
        ]
        
        # Find all semester sections
        semester_sections = []
        for pattern in semester_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start_pos = match.start()
                # Find the end of this semester (next semester or end of text)
                next_semester = None
                for next_match in re.finditer(pattern, text[start_pos + 1:], re.IGNORECASE):
                    next_semester = start_pos + 1 + next_match.start()
                    break
                
                if next_semester:
                    semester_text = text[start_pos:next_semester]
                else:
                    # Take a reasonable chunk after semester header
                    semester_text = text[start_pos:start_pos + 2000]
                
                semester_sections.append(semester_text)
        
        # If no semester sections found, use the whole text but be more careful
        if not semester_sections:
            semester_sections = [text]
        
        # Extract courses from each section
        for section in semester_sections:
            section_courses = self._extract_courses_from_section(section)
            courses_grades.update(section_courses)
        
        return courses_grades
    
    def _extract_courses_from_section(self, text: str) -> Dict[str, str]:
        """Extract courses from a specific text section with better precision."""
        courses_grades = {}
        
        # Valid grades including I
        valid_grades = {'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F', 'W', 'P', 'N', 'I'}
        
        # More precise patterns for course extraction
        # Pattern 1: Course code, course name, grade, credits (most common format)
        pattern1 = r'(01\d{6})\s+([^0-9\n\r]{10,80}?)\s+([ABCDF][\+\-]?|[WPNI])\s+(\d{1,2})\s*(?:\n|\r|$)'
        
        # Pattern 2: Course code followed by grade (more flexible)
        pattern2 = r'(01\d{6})\s+.{5,100}?\s+([ABCDF][\+\-]?|[WPNI])(?:\s+\d{1,2})?\s*(?:\n|\r|$)'
        
        # Pattern 3: Just course code and grade close together
        pattern3 = r'(01\d{6})\s+.*?\s+([ABCDF][\+\-]?|[WPNI])\s*(?:\n|\r)'
        
        patterns = [pattern1, pattern2, pattern3]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                course_code = match.group(1)
                
                # Get grade (different position depending on pattern)
                if pattern == pattern1:
                    grade = match.group(3).upper()
                else:
                    grade = match.group(2).upper()
                
                # Validate grade
                if grade in valid_grades:
                    # Skip if this looks like a course catalog entry (too many repeated grades)
                    context = match.group(0)
                    if not self._looks_like_catalog_entry(context):
                        courses_grades[course_code] = grade
                        
        # Additional pattern for lines that might have different formatting
        # Look for lines with course codes followed by single letter grades
        lines = text.split('\n')
        for line in lines:
            # Skip obviously non-grade lines
            if len(line) < 10 or 'prerequisite' in line.lower() or 'corequisite' in line.lower():
                continue
                
            # Look for course code + grade pattern in the line
            course_match = re.search(r'(01\d{6})', line)
            if course_match:
                course_code = course_match.group(1)
                
                # Look for grades in the same line
                grade_matches = re.findall(r'\b([ABCDF][\+\-]?|[WPNI])\b', line)
                
                # Take the last grade found (most likely to be the actual grade)
                if grade_matches:
                    grade = grade_matches[-1].upper()
                    if grade in valid_grades and course_code not in courses_grades:
                        courses_grades[course_code] = grade
        
        return courses_grades
    
    def _looks_like_catalog_entry(self, text: str) -> bool:
        """Check if text looks like a course catalog entry rather than student grade."""
        # Skip entries that look like course descriptions
        catalog_indicators = [
            'prerequisite', 'corequisite', 'credit', 'laboratory', 
            'lecture', 'introduction to', 'advanced', 'basic',
            'semester hour', 'course description'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in catalog_indicators)
    
    def process_pdf(self, pdf_path: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Process a single PDF file."""
        print(f"Processing: {pdf_path}")
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return {}, {}
        
        # Extract student info
        student_info = self.extract_student_info(text)
        
        # Extract courses and grades
        courses_grades = self.extract_courses(text)
        
        # Add course codes to global set
        self.all_course_codes.update(courses_grades.keys())
        
        return student_info, courses_grades
    
    def get_sorted_course_codes(self) -> List[str]:
        """Get all course codes sorted numerically."""
        return sorted(list(self.all_course_codes))

def main():
    """Main function to process all PDFs in current directory."""
    
    print("PDF Transcript Batch Processor")
    print("=" * 50)
    
    # Find all PDF files in current directory
    current_dir = Path(".")
    pdf_files = list(current_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in current directory.")
        input("Press Enter to exit...")
        return
    
    print(f"Found {len(pdf_files)} PDF files:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")
    print()
    
    # Initialize extractor
    extractor = PDFTranscriptExtractor()
    
    # First pass: Process all PDFs to collect all course codes
    print("Phase 1: Collecting all course codes...")
    all_results = []
    
    for pdf_file in pdf_files:
        try:
            student_info, courses_grades = extractor.process_pdf(str(pdf_file))
            
            if student_info.get("name") != "Unknown":
                all_results.append({
                    "student_info": student_info,
                    "courses_grades": courses_grades,
                    "filename": pdf_file.name
                })
                print(f"✓ {student_info.get('name')} ({student_info.get('id')}) - {len(courses_grades)} courses")
            else:
                print(f"✗ Failed to extract data from: {pdf_file.name}")
                
        except Exception as e:
            print(f"✗ Error processing {pdf_file.name}: {e}")
    
    if not all_results:
        print("\nNo valid data extracted from any PDF files.")
        input("Press Enter to exit...")
        return
    
    # Get sorted course codes
    sorted_course_codes = extractor.get_sorted_course_codes()
    
    print(f"\nPhase 2: Creating output...")
    print(f"✓ Found {len(sorted_course_codes)} unique course codes")
    print(f"✓ Processed {len(all_results)} students")
    
    # Show sample of course codes
    print(f"\nSample course codes found:")
    for i, code in enumerate(sorted_course_codes[:10]):
        print(f"  {code}")
    if len(sorted_course_codes) > 10:
        print(f"  ... and {len(sorted_course_codes) - 10} more")
    
    # Generate CSV output
    output_file = "transcript_batch_results.csv"
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Create header row
            header = ["NAME - SURNAME", "Student ID"] + sorted_course_codes
            writer.writerow(header)
            
            # Write data rows
            for result in all_results:
                student_info = result["student_info"]
                courses_grades = result["courses_grades"]
                
                row = [
                    student_info.get("name", "Unknown"),
                    student_info.get("id", "Unknown")
                ]
                
                # Add grades for each course code in sorted order
                for course_code in sorted_course_codes:
                    grade = courses_grades.get(course_code, "")
                    row.append(grade)
                
                writer.writerow(row)
        
        print(f"\n✓ Results saved to: {output_file}")
        print(f"✓ Format: CSV with {len(header)} columns total")
        print(f"  - Column 1: Student Name")
        print(f"  - Column 2: Student ID") 
        print(f"  - Columns 3-{len(header)}: Course codes (sorted numerically)")
        
        # Create a summary file
        summary_file = "course_codes_found.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"Course Codes Found ({len(sorted_course_codes)} total)\n")
            f.write("=" * 50 + "\n\n")
            for i, code in enumerate(sorted_course_codes, 1):
                f.write(f"{i:3d}. {code}\n")
        
        print(f"✓ Course codes list saved to: {summary_file}")
            
    except Exception as e:
        print(f"✗ Error saving results: {e}")
    
    print(f"\nProcessing complete!")
    print(f"Files created:")
    print(f"  - {output_file} (main results)")
    print(f"  - {summary_file} (course codes list)")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
