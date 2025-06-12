import tempfile
import os
from pathlib import Path

def classify_course(course_code, course_name=""):
    """
    Classify course into appropriate category based on course code.
    Returns: (category, subcategory, is_identified)
    """
    code = course_code.upper()
    
    # IE Core Courses (specific patterns)
    ie_core_patterns = [
        "01206221", "01206222", "01206223", "01206224", "01206251", "01206272",
        "01206311", "01206312", "01206321", "01206322", "01206323", "01206341", 
        "01206342", "01206343", "01206361", "01206362", "01206371", "01206381",
        "01206382", "01206399", "01206452", "01206495", "01206497", "01206499"
    ]
    
    # Foundation courses that are also IE core
    foundation_ie_patterns = [
        "01204111", "01205201", "01205202", "01208111", "01208221", "01208241",
        "01208281", "01208381", "01213211", "01403114", "01403117", 
        "01417167", "01417168", "01417267", "01420111", "01420112", 
        "01420113", "01420114"
    ]
    
    if code in ie_core_patterns or code in foundation_ie_patterns:
        return ("ie_core", "core", True)
    
    # Gen-Ed Classification with specific patterns
    # Wellness
    wellness_patterns = ["01175", "01101102", "01173151"]
    if any(code.startswith(prefix) for prefix in wellness_patterns):
        return ("gen_ed", "wellness", True)
    
    if code.startswith("01999") and any(keyword in course_name.lower() for keyword in ["health", "food", "mankind"]):
        return ("gen_ed", "wellness", True)
    
    # Entrepreneurship  
    entrepreneurship_patterns = ["01005101", "01131111", "01132101", "01200101", "01418102"]
    if code in entrepreneurship_patterns:
        return ("gen_ed", "entrepreneurship", True)
    
    # Language and Communication
    language_patterns = ["01361", "01355", "01354", "01356", "01357", "01358", 
                        "01362", "01367", "01395", "01398", "01399", "01371"]
    if any(code.startswith(prefix) for prefix in language_patterns):
        return ("gen_ed", "language_communication", True)
    
    if code in ["01418104", "01418111"]:
        return ("gen_ed", "language_communication", True)
    
    # Thai Citizen and Global Citizenship
    thai_citizen_patterns = ["01001", "01015", "01174", "01350", "01387104", 
                            "01390", "01301", "01455", "01460"]
    if any(code.startswith(prefix) for prefix in thai_citizen_patterns) or "999111" in code:
        return ("gen_ed", "thai_citizen_global", True)
    
    # Aesthetics
    aesthetics_patterns = ["01007", "01240", "01373", "01376", "01387102", "01420201"]
    if any(code.startswith(prefix) for prefix in aesthetics_patterns):
        return ("gen_ed", "aesthetics", True)
    
    if code.startswith("01999") and any(keyword in course_name.lower() for keyword in ["art", "music", "design", "culture"]):
        return ("gen_ed", "aesthetics", True)
    
    # Technical Electives (advanced 206xxx courses not in core)
    technical_elective_patterns = [
        "01206411", "01206412", "01206413", "01206414", "01206415", "01206416",
        "01206421", "01206422", "01206423", "01206424", "01206425", "01206426",
        "01206427", "01206431", "01206432", "01206433", "01206441", "01206442",
        "01206443", "01206444", "01206445", "01206446", "01206447", "01206448",
        "01206451", "01206453", "01206461", "01206462", "01206463", "01206464",
        "01206465", "01206466", "01206467", "01206471", "01206490", "01206496",
        "01206498"
    ]
    
    if code in technical_elective_patterns:
        return ("technical_electives", "technical", True)
    
    # Rail Engineering courses
    if code.startswith("01200") and code in ["01200431", "01200434", "01200435"]:
        return ("technical_electives", "rail", True)
    
    # If we reach here, the course is unidentified
    return ("unidentified", "unknown", False)

def create_smart_registration_excel(student_info, semesters, validation_results):
    """
    Create a smart, dynamic Excel registration format with unidentified course tracking.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Registration Plan"
        
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
        
        # CLASSIFY ALL COURSES WITH IDENTIFICATION TRACKING
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
            "unidentified": []  # NEW: Track unidentified courses
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
                
                # Classify course with identification tracking
                category, subcategory, is_identified = classify_course(course_code, course_name)
                
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
        
        # [Rest of the Excel generation code remains the same...]
        # IE CORE COURSES SECTION
        ws[f'A{current_row}'] = "IE CORE COURSES"
        ws[f'A{current_row}'].font = header_font
        ws[f'A{current_row}'].fill = blue_fill
        ws.merge_cells(f'A{current_row}:P{current_row}')
        current_row += 1
        
        # Add IE courses (same logic as before)
        ie_courses_12 = [c for c in classified_courses["ie_core"] if c["year"] > 0 and (c["year"] - min(s.get("year_int", 9999) for s in semesters if s.get("year_int", 0) > 0) + 1) <= 2]
        ie_courses_34 = [c for c in classified_courses["ie_core"] if c["year"] > 0 and (c["year"] - min(s.get("year_int", 9999) for s in semesters if s.get("year_int", 0) > 0) + 1) > 2]
        
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
        
        # [Continue with rest of sections - Gen-Ed, Technical Electives, etc.]
        # [Same as before but with updated color coding]
        
        # Save to bytes
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            wb.save(tmp_file.name)
            
            with open(tmp_file.name, 'rb') as f:
                excel_bytes = f.read()
            
            os.unlink(tmp_file.name)
            return excel_bytes, unidentified_count
            
    except Exception as e:
        raise Exception(f"Error creating Excel file: {e}")
