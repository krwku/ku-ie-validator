import tempfile
import os
import json
from pathlib import Path

def load_course_categories():
    """
    Load course categories from separate JSON files.
    Returns: dict with categorized courses
    """
    course_data_dir = Path(__file__).parent.parent / "course_data"
    
    categories = {
        "ie_core": set(),
        "technical_electives": set(),
        "gen_ed": {
            "wellness": set(),
            "entrepreneurship": set(),
            "language_communication": set(),
            "thai_citizen_global": set(),
            "aesthetics": set()
        }
    }
    
    # Load IE Core courses
    ie_core_file = course_data_dir / "ie_core_courses.json"
    if ie_core_file.exists():
        with open(ie_core_file, 'r', encoding='utf-8') as f:
            ie_data = json.load(f)
            # Add from both sections
            for course in ie_data.get("industrial_engineering_courses", []):
                categories["ie_core"].add(course["code"])
            for course in ie_data.get("other_related_courses", []):
                categories["ie_core"].add(course["code"])
    
    # Load Technical Electives
    tech_file = course_data_dir / "technical_electives.json"
    if tech_file.exists():
        with open(tech_file, 'r', encoding='utf-8') as f:
            tech_data = json.load(f)
            for course in tech_data.get("technical_electives", []):
                categories["technical_electives"].add(course["code"])
    
    # Load Gen-Ed courses
    gen_ed_file = course_data_dir / "gen_ed_courses.json"
    if gen_ed_file.exists():
        with open(gen_ed_file, 'r', encoding='utf-8') as f:
            gen_ed_data = json.load(f)
            gen_ed_courses = gen_ed_data.get("gen_ed_courses", {})
            
            for course in gen_ed_courses.get("wellness", []):
                categories["gen_ed"]["wellness"].add(course["code"])
            for course in gen_ed_courses.get("entrepreneurship", []):
                categories["gen_ed"]["entrepreneurship"].add(course["code"])
            for course in gen_ed_courses.get("language_communication", []):
                categories["gen_ed"]["language_communication"].add(course["code"])
            for course in gen_ed_courses.get("thai_citizen_global", []):
                categories["gen_ed"]["thai_citizen_global"].add(course["code"])
            for course in gen_ed_courses.get("aesthetics", []):
                categories["gen_ed"]["aesthetics"].add(course["code"])
    
    return categories

def classify_course(course_code, course_name="", course_categories=None):
    """
    Classify course into appropriate category using loaded JSON files.
    Returns: (category, subcategory, is_identified)
    """
    if course_categories is None:
        course_categories = load_course_categories()
    
    code = course_code.upper()
    
    # Check IE Core courses
    if code in course_categories["ie_core"]:
        return ("ie_core", "core", True)
    
    # Check Technical Electives
    if code in course_categories["technical_electives"]:
        return ("technical_electives", "technical", True)
    
    # Check Gen-Ed courses
    for subcategory, courses in course_categories["gen_ed"].items():
        if code in courses:
            return ("gen_ed", subcategory, True)
    
    # If we reach here, the course is unidentified
    return ("unidentified", "unknown", False)

def create_smart_registration_excel(student_info, semesters, validation_results):
    """
    Create a smart, dynamic Excel registration format with proper course detection.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Registration Plan"
        
        # Load course categories once
        course_categories = load_course_categories()
        
        # Define styles
        header_font = Font(bold=True, size=11)
        subheader_font = Font(bold=True, size=10)
        normal_font = Font(size=9)
        small_font = Font(size=8)
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)
        border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        # Color fills
        green_fill = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
        yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
        gray_fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
        blue_fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
        red_fill = PatternFill(start_color="FFE6E6", end_color="FFE6E6", fill_type="solid")
        orange_fill = PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid")  # For unidentified
        
        # Set column widths
        column_widths = {
            'A': 12, 'B': 35, 'C': 8, 'D': 8, 'E': 15, 'F': 35, 'G': 8, 'H': 8,
            'I': 15, 'J': 35, 'K': 8, 'L': 8, 'M': 15, 'N': 35, 'O': 8, 'P': 8
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # HEADER SECTION
        ws['A1'] = "KU INDUSTRIAL ENGINEERING - COURSE REGISTRATION PLAN"
        ws['A1'].font = Font(bold=True, size=14)
        ws.merge_cells('A1:P1')
        ws['A1'].alignment = center_align
        ws['A1'].fill = blue_fill
        
        # Student Info
        ws['A3'] = "Student ID:"
        ws['B3'] = student_info.get('id', '')
        ws['B3'].fill = yellow_fill
        ws['E3'] = "Name:"
        ws['F3'] = student_info.get('name', '')
        ws['F3'].fill = yellow_fill
        
        # CLASSIFY ALL COURSES WITH PROPER DETECTION
        classified_courses = {
            "ie_core": [],
            "gen_ed": {
                "wellness": [],
                "entrepreneurship": [],
                "language_communication": [],
                "thai_citizen_global": [],
                "aesthetics": []
            },
            "technical_electives": [],
            "free_electives": [],
            "unidentified": []  # Track unidentified courses
        }
        
        unidentified_count = 0
        
        # Process all courses from all semesters
        for sem_idx, semester in enumerate(semesters):
            semester_name = semester.get("semester", f"Semester {sem_idx + 1}")
            year = semester.get("year_int", 0)
            semester_type = semester.get("semester_type", "")
            
            for course in semester.get("courses", []):
                course_code = course.get("code", "")
                course_name = course.get("name", "")
                grade = course.get("grade", "")
                credits = course.get("credits", 0)
                
                # Check if course is valid
                is_valid = True
                issue_reason = ""
                for result in validation_results:
                    if (result.get('course_code') == course_code and 
                        not result.get('is_valid', True) and 
                        result.get('course_code') != 'CREDIT_LIMIT'):
                        is_valid = False
                        issue_reason = result.get('reason', '')
                        break
                
                # Classify course with proper detection
                category, subcategory, is_identified = classify_course(course_code, course_name, course_categories)
                
                if not is_identified:
                    unidentified_count += 1
                
                course_info = {
                    "code": course_code,
                    "name": course_name,
                    "grade": grade,
                    "credits": credits,
                    "semester": semester_name,
                    "is_valid": is_valid,
                    "issue": issue_reason,
                    "year": year,
                    "semester_type": semester_type,
                    "is_identified": is_identified
                }
                
                # Place in appropriate category
                if category == "ie_core":
                    classified_courses["ie_core"].append(course_info)
                elif category == "gen_ed":
                    classified_courses["gen_ed"][subcategory].append(course_info)
                elif category == "technical_electives":
                    classified_courses["technical_electives"].append(course_info)
                elif category == "unidentified":
                    classified_courses["unidentified"].append(course_info)
                else:
                    classified_courses["free_electives"].append(course_info)
        
        # Add warning about unidentified courses
        if unidentified_count > 0:
            ws['A4'] = "⚠️ ATTENTION:"
            ws['A4'].fill = orange_fill
            ws['A4'].font = Font(bold=True)
            ws['B4'] = f"{unidentified_count} unidentified courses found - database update needed"
            ws['B4'].fill = orange_fill
            ws['B4'].font = Font(bold=True)
        
        current_row = 6
        
        # Function to add course rows with identification status
        def add_course_rows(courses, start_row, cols_per_course=4, max_cols=16):
            courses_per_row = max_cols // cols_per_course
            for i, course in enumerate(courses):
                row = start_row + (i // courses_per_row)
                col_set = (i % courses_per_row) * cols_per_course
                
                # Course code
                cell = ws[f'{header_cols[col_set]}{row}']
                cell.value = course["code"]
                cell.border = border
                cell.font = small_font
                
                # Course name
                cell = ws[f'{header_cols[col_set + 1]}{row}']
                cell.value = course["name"]
                cell.border = border
                cell.font = small_font
                cell.alignment = left_align
                
                # Grade
                cell = ws[f'{header_cols[col_set + 2]}{row}']
                cell.value = course["grade"]
                cell.border = border
                cell.font = small_font
                cell.alignment = center_align
                
                # Credits
                cell = ws[f'{header_cols[col_set + 3]}{row}']
                cell.value = course["credits"]
                cell.border = border
                cell.font = small_font
                cell.alignment = center_align
                
                # Color coding with identification status
                if not course["is_identified"]:
                    # Orange for unidentified courses
                    for j in range(4):
                        ws[f'{header_cols[col_set + j]}{row}'].fill = orange_fill
                elif not course["is_valid"]:
                    # Red for invalid courses
                    for j in range(4):
                        ws[f'{header_cols[col_set + j]}{row}'].fill = red_fill
                elif course["grade"] not in ['F', 'W', 'N', '']:
                    # Green for completed courses
                    for j in range(4):
                        ws[f'{header_cols[col_set + j]}{row}'].fill = green_fill
            
            return start_row + ((len(courses) - 1) // courses_per_row) + 1 if courses else start_row
        
        header_cols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
        
        # IE CORE COURSES SECTION
        ws[f'A{current_row}'] = "IE CORE COURSES"
        ws[f'A{current_row}'].font = header_font
        ws[f'A{current_row}'].fill = blue_fill
        ws.merge_cells(f'A{current_row}:P{current_row}')
        current_row += 1
        
        # Column headers
        headers = ["Code", "Course Name", "Grade", "Credits"]
        for i in range(4):  # 4 columns of headers
            for j, header in enumerate(headers):
                col_idx = i * 4 + j
                if col_idx < len(header_cols):
                    cell = ws[f'{header_cols[col_idx]}{current_row}']
                    cell.value = header
                    cell.font = subheader_font
                    cell.alignment = center_align
                    cell.fill = gray_fill
                    cell.border = border
        current_row += 1
        
        # Add IE courses (organize by years 1-2 and 3-4)
        ie_courses_12 = [c for c in classified_courses["ie_core"] if c["year"] > 0 and (c["year"] - min(s.get("year_int", 9999) for s in semesters if s.get("year_int", 0) > 0) + 1) <= 2]
        ie_courses_34 = [c for c in classified_courses["ie_core"] if c["year"] > 0 and (c["year"] - min(s.get("year_int", 9999) for s in semesters if s.get("year_int", 0) > 0) + 1) > 2]
        
        if ie_courses_12:
            ws[f'A{current_row}'] = "Years 1-2"
            ws[f'A{current_row}'].font = subheader_font
            current_row += 1
            current_row = add_course_rows(ie_courses_12, current_row) + 1
        
        if ie_courses_34:
            ws[f'A{current_row}'] = "Years 3-4"
            ws[f'A{current_row}'].font = subheader_font
            current_row += 1
            current_row = add_course_rows(ie_courses_34, current_row) + 1
        
        # UNIDENTIFIED COURSES SECTION (HIGH PRIORITY)
        if classified_courses["unidentified"]:
            current_row += 1
            ws[f'A{current_row}'] = "⚠️ UNIDENTIFIED COURSES - REQUIRES DATABASE UPDATE"
            ws[f'A{current_row}'].font = header_font
            ws[f'A{current_row}'].fill = orange_fill
            ws.merge_cells(f'A{current_row}:P{current_row}')
            current_row += 1
            
            ws[f'A{current_row}'] = "These courses are not in the system database and need classification:"
            ws[f'A{current_row}'].font = subheader_font
            current_row += 1
            
            for course in classified_courses["unidentified"]:
                ws[f'A{current_row}'] = course["code"]
                ws[f'A{current_row}'].border = border
                ws[f'A{current_row}'].font = small_font
                ws[f'A{current_row}'].fill = orange_fill
                
                ws[f'B{current_row}'] = course["name"]
                ws[f'B{current_row}'].border = border
                ws[f'B{current_row}'].font = small_font
                ws[f'B{current_row}'].alignment = left_align
                ws[f'B{current_row}'].fill = orange_fill
                
                ws[f'C{current_row}'] = course["grade"]
                ws[f'C{current_row}'].border = border
                ws[f'C{current_row}'].font = small_font
                ws[f'C{current_row}'].alignment = center_align
                ws[f'C{current_row}'].fill = orange_fill
                
                ws[f'D{current_row}'] = course["credits"]
                ws[f'D{current_row}'].border = border
                ws[f'D{current_row}'].font = small_font
                ws[f'D{current_row}'].alignment = center_align
                ws[f'D{current_row}'].fill = orange_fill
                
                ws[f'E{current_row}'] = course["semester"]
                ws[f'E{current_row}'].border = border
                ws[f'E{current_row}'].font = small_font
                ws[f'E{current_row}'].fill = orange_fill
                
                current_row += 1
            
            current_row += 1
        
        # GEN-ED SECTIONS with proper categorization
        gen_ed_categories = [
            ("wellness", "WELLNESS (7 Credits Required)"),
            ("entrepreneurship", "ENTREPRENEURSHIP (5 Credits Required)"),
            ("language_communication", "LANGUAGE & COMMUNICATION (15 Credits Required)"),
            ("thai_citizen_global", "THAI CITIZEN & GLOBAL CITIZENSHIP (2 Credits Required)"),
            ("aesthetics", "AESTHETICS (3 Credits Required)")
        ]
        
        for category_key, category_name in gen_ed_categories:
            courses = classified_courses["gen_ed"][category_key]
            if courses:  # Only show if there are courses
                # Category header
                ws[f'A{current_row}'] = category_name
                ws[f'A{current_row}'].font = header_font
                ws[f'A{current_row}'].fill = gray_fill
                ws.merge_cells(f'A{current_row}:P{current_row}')
                current_row += 1
                
                # Add courses in this category
                for course in courses:
                    ws[f'A{current_row}'] = course["code"]
                    ws[f'A{current_row}'].border = border
                    ws[f'A{current_row}'].font = small_font
                    
                    ws[f'B{current_row}'] = course["name"]
                    ws[f'B{current_row}'].border = border
                    ws[f'B{current_row}'].font = small_font
                    ws[f'B{current_row}'].alignment = left_align
                    
                    ws[f'C{current_row}'] = course["grade"]
                    ws[f'C{current_row}'].border = border
                    ws[f'C{current_row}'].font = small_font
                    ws[f'C{current_row}'].alignment = center_align
                    
                    ws[f'D{current_row}'] = course["credits"]
                    ws[f'D{current_row}'].border = border
                    ws[f'D{current_row}'].font = small_font
                    ws[f'D{current_row}'].alignment = center_align
                    
                    ws[f'E{current_row}'] = course["semester"]
                    ws[f'E{current_row}'].border = border
                    ws[f'E{current_row}'].font = small_font
                    
                    # Color coding
                    if not course["is_identified"]:
                        for col in ['A', 'B', 'C', 'D', 'E']:
                            ws[f'{col}{current_row}'].fill = orange_fill
                    elif not course["is_valid"]:
                        for col in ['A', 'B', 'C', 'D', 'E']:
                            ws[f'{col}{current_row}'].fill = red_fill
                    elif course["grade"] not in ['F', 'W', 'N', '']:
                        for col in ['A', 'B', 'C', 'D', 'E']:
                            ws[f'{col}{current_row}'].fill = green_fill
                    
                    current_row += 1
                
                current_row += 1
        
        # TECHNICAL ELECTIVES SECTION
        if classified_courses["technical_electives"]:
            ws[f'A{current_row}'] = "TECHNICAL ELECTIVES"
            ws[f'A{current_row}'].font = header_font
            ws[f'A{current_row}'].fill = blue_fill
            ws.merge_cells(f'A{current_row}:P{current_row}')
            current_row += 1
            
            for course in classified_courses["technical_electives"]:
                ws[f'A{current_row}'] = course["code"]
                ws[f'A{current_row}'].border = border
                ws[f'A{current_row}'].font = small_font
                
                ws[f'B{current_row}'] = course["name"]
                ws[f'B{current_row}'].border = border
                ws[f'B{current_row}'].font = small_font
                ws[f'B{current_row}'].alignment = left_align
                
                ws[f'C{current_row}'] = course["grade"]
                ws[f'C{current_row}'].border = border
                ws[f'C{current_row}'].font = small_font
                ws[f'C{current_row}'].alignment = center_align
                
                ws[f'D{current_row}'] = course["credits"]
                ws[f'D{current_row}'].border = border
                ws[f'D{current_row}'].font = small_font
                ws[f'D{current_row}'].alignment = center_align
                
                ws[f'E{current_row}'] = course["semester"]
                ws[f'E{current_row}'].border = border
                ws[f'E{current_row}'].font = small_font
                
                # Color coding
                if not course["is_identified"]:
                    for col in ['A', 'B', 'C', 'D', 'E']:
                        ws[f'{col}{current_row}'].fill = orange_fill
                elif not course["is_valid"]:
                    for col in ['A', 'B', 'C', 'D', 'E']:
                        ws[f'{col}{current_row}'].fill = red_fill
                elif course["grade"] not in ['F', 'W', 'N', '']:
                    for col in ['A', 'B', 'C', 'D', 'E']:
                        ws[f'{col}{current_row}'].fill = green_fill
                
                current_row += 1
            
            current_row += 1
        
        # FREE ELECTIVES SECTION
        if classified_courses["free_electives"]:
            ws[f'A{current_row}'] = "FREE ELECTIVES"
            ws[f'A{current_row}'].font = header_font
            ws[f'A{current_row}'].fill = yellow_fill
            ws.merge_cells(f'A{current_row}:P{current_row}')
            current_row += 1
            
            for course in classified_courses["free_electives"]:
                ws[f'A{current_row}'] = course["code"]
                ws[f'A{current_row}'].border = border
                ws[f'A{current_row}'].font = small_font
                
                ws[f'B{current_row}'] = course["name"]
                ws[f'B{current_row}'].border = border
                ws[f'B{current_row}'].font = small_font
                ws[f'B{current_row}'].alignment = left_align
                
                ws[f'C{current_row}'] = course["grade"]
                ws[f'C{current_row}'].border = border
                ws[f'C{current_row}'].font = small_font
                ws[f'C{current_row}'].alignment = center_align
                
                ws[f'D{current_row}'] = course["credits"]
                ws[f'D{current_row}'].border = border
                ws[f'D{current_row}'].font = small_font
                ws[f'D{current_row}'].alignment = center_align
                
                ws[f'E{current_row}'] = course["semester"]
                ws[f'E{current_row}'].border = border
                ws[f'E{current_row}'].font = small_font
                
                # Color coding
                if not course["is_identified"]:
                    for col in ['A', 'B', 'C', 'D', 'E']:
                        ws[f'{col}{current_row}'].fill = orange_fill
                elif not course["is_valid"]:
                    for col in ['A', 'B', 'C', 'D', 'E']:
                        ws[f'{col}{current_row}'].fill = red_fill
                elif course["grade"] not in ['F', 'W', 'N', '']:
                    for col in ['A', 'B', 'C', 'D', 'E']:
                        ws[f'{col}{current_row}'].fill = green_fill
                
                current_row += 1
        
        # SUMMARY AT THE END
        current_row += 2
        
        ws[f'A{current_row}'] = "CREDIT SUMMARY"
        ws[f'A{current_row}'].font = header_font
        ws[f'A{current_row}'].fill = blue_fill
        ws.merge_cells(f'A{current_row}:E{current_row}')
        current_row += 1
        
        # Calculate credits by category
        ie_credits = sum(c["credits"] for c in classified_courses["ie_core"] if c["grade"] not in ['F', 'W', 'N', ''])
        gen_ed_credits = sum(
            sum(c["credits"] for c in courses if c["grade"] not in ['F', 'W', 'N', ''])
            for courses in classified_courses["gen_ed"].values()
        )
        tech_credits = sum(c["credits"] for c in classified_courses["technical_electives"] if c["grade"] not in ['F', 'W', 'N', ''])
        free_credits = sum(c["credits"] for c in classified_courses["free_electives"] if c["grade"] not in ['F', 'W', 'N', ''])
        unidentified_credits = sum(c["credits"] for c in classified_courses["unidentified"] if c["grade"] not in ['F', 'W', 'N', ''])
        
        summary_data = [
            ("IE Core Courses:", ie_credits),
            ("Gen-Ed Courses:", gen_ed_credits),
            ("Technical Electives:", tech_credits),
            ("Free Electives:", free_credits),
            ("Unidentified Courses:", unidentified_credits),
            ("TOTAL CREDITS:", ie_credits + gen_ed_credits + tech_credits + free_credits + unidentified_credits)
        ]
        
        for i, (label, credits) in enumerate(summary_data):
            row = current_row + i
            ws[f'A{row}'] = label
            ws[f'A{row}'].font = subheader_font
            ws[f'B{row}'] = credits
            ws[f'B{row}'].font = subheader_font
            
            if "Unidentified" in label and credits > 0:
                ws[f'A{row}'].fill = orange_fill
                ws[f'B{row}'].fill = orange_fill
            elif label.startswith("TOTAL"):
                ws[f'A{row}'].fill = blue_fill
                ws[f'B{row}'].fill = blue_fill
            elif credits > 0:
                ws[f'B{row}'].fill = green_fill
            else:
                ws[f'B{row}'].fill = yellow_fill
        
        # Save to bytes
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            wb.save(tmp_file.name)
            
            with open(tmp_file.name, 'rb') as f:
                excel_bytes = f.read()
            
            os.unlink(tmp_file.name)
            return excel_bytes, unidentified_count
            
    except Exception as e:
        raise Exception(f"Error creating Excel file: {e}")
