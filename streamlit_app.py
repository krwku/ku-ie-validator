import streamlit as st
import json
import sys
from pathlib import Path
import tempfile
import os
import io
import PyPDF2
import pandas as pd
from datetime import datetime

# Add your existing modules to path
sys.path.append(str(Path(__file__).parent))

# Import your existing modules
from utils.pdf_extractor import PDFExtractor
from utils.validation_adapter import ValidationAdapter
from validator import CourseRegistrationValidator

@st.cache_data
def load_available_course_data():
    """Load all available course data files from the repository"""
    course_data_dir = Path(__file__).parent / "course_data"
    available_files = {}
    
    if course_data_dir.exists():
        for json_file in course_data_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                file_name = json_file.stem
                if "2560" in file_name:
                    display_name = "Industrial Engineering 2560 (2017-2021)"
                elif "2565" in file_name:
                    display_name = "Industrial Engineering 2565 (2022-2026)"
                else:
                    display_name = file_name
                
                available_files[display_name] = {
                    'data': data,
                    'filename': json_file.name,
                    'path': str(json_file)
                }
            except Exception as e:
                st.error(f"Error loading {json_file.name}: {e}")
    
    return available_files

def extract_text_from_pdf_bytes(pdf_bytes):
    """Extract text from PDF bytes using PyPDF2"""
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        
        all_text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text and page_text.strip():
                all_text.append(page_text)
        
        return "\n".join(all_text)
    
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return ""

def create_pqi_registration_excel(student_info, semesters, validation_results):
    """
    Create Excel file matching the exact PQI registration format.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Registration Information"
        
        # Define styles
        header_font = Font(bold=True, size=10)
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
        
        # Set column widths
        column_widths = {
            'A': 8, 'B': 15, 'C': 15, 'D': 15, 'E': 15, 'F': 15, 'G': 15, 'H': 15, 'I': 15,
            'J': 15, 'K': 15, 'L': 15, 'M': 15, 'N': 15, 'O': 15, 'P': 15, 'Q': 15, 'R': 12, 'S': 12
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # Row heights
        for row in range(1, 50):
            ws.row_dimensions[row].height = 25
        
        # Top section - Student Info
        ws['A1'] = "Student ID"
        ws['A1'].font = header_font
        ws['B1'] = student_info.get('id', '')
        ws['B1'].fill = yellow_fill
        ws['B1'].border = border
        
        ws['H1'] = "Credit"
        ws['H1'].font = header_font
        ws['I1'].border = border
        
        ws['J1'] = "Find"
        ws['J1'].fill = gray_fill
        ws['J1'].border = border
        ws['K1'] = "Clear"
        ws['K1'].fill = gray_fill
        ws['K1'].border = border
        
        ws['A2'] = "Name - Surname"
        ws['A2'].font = header_font
        ws['B2'] = student_info.get('name', '')
        ws['B2'].fill = yellow_fill
        ws['B2'].border = border
        
        # Year headers (row 4)
        year_headers = [
            ('B', 'E', 'Year 1'),
            ('F', 'I', 'Year 2'), 
            ('J', 'M', 'Year 3'),
            ('N', 'Q', 'Year 4')
        ]
        
        for start_col, end_col, year_text in year_headers:
            ws.merge_cells(f'{start_col}4:{end_col}4')
            cell = ws[f'{start_col}4']
            cell.value = year_text
            cell.font = header_font
            cell.alignment = center_align
            cell.border = border
            cell.fill = gray_fill
        
        # Semester headers (row 5)
        semester_cols = [
            ('B', 'C', 'First semester'),
            ('D', 'E', 'Second semester'),
            ('F', 'G', 'First semester'),
            ('H', 'I', 'Second semester'),
            ('J', 'K', 'First semester'),
            ('L', 'M', 'Second semester'),
            ('N', 'O', 'First semester'),
            ('P', 'Q', 'Second semester')
        ]
        
        for start_col, end_col, sem_text in semester_cols:
            ws.merge_cells(f'{start_col}5:{end_col}5')
            cell = ws[f'{start_col}5']
            cell.value = sem_text
            cell.font = header_font
            cell.alignment = center_align
            cell.border = border
        
        # IE COURSE section label
        ws.merge_cells('A6:A16')
        cell = ws['A6']
        cell.value = "IE\nCOURSE"
        cell.font = header_font
        cell.alignment = center_align
        cell.border = border
        
        # Create course mapping
        course_mapping = {}
        for semester in semesters:
            year = semester.get("year_int", 0)
            semester_type = semester.get("semester_type", "")
            
            # Map to grid position (assuming first semester in data is Year 1)
            if year > 0:
                # Calculate which year this should be in the grid
                min_year = min(s.get("year_int", 9999) for s in semesters if s.get("year_int", 0) > 0)
                grid_year = year - min_year + 1
                
                if grid_year <= 4:
                    sem_key = f"Year{grid_year}_{semester_type}"
                    course_mapping[sem_key] = semester.get("courses", [])
        
        # Fill IE courses (rows 6-15, slots 1-10)
        for slot in range(1, 11):
            row = 5 + slot
            
            # Slot number
            ws[f'A{row}'] = str(slot)
            ws[f'A{row}'].alignment = center_align
            ws[f'A{row}'].border = border
            ws[f'A{row}'].font = small_font
            
            # Course positions for each semester
            col_positions = {
                'Year1_First': 'B', 'Year1_Second': 'D',
                'Year2_First': 'F', 'Year2_Second': 'H',
                'Year3_First': 'J', 'Year3_Second': 'L', 
                'Year4_First': 'N', 'Year4_Second': 'P'
            }
            
            for sem_key, col in col_positions.items():
                courses = course_mapping.get(sem_key, [])
                cell = ws[f'{col}{row}']
                cell.border = border
                cell.alignment = left_align
                cell.font = small_font
                
                if slot <= len(courses):
                    course = courses[slot-1]
                    course_code = course.get('code', '')
                    course_name = course.get('name', '')
                    grade = course.get('grade', '')
                    
                    if course_code:
                        # Check if course is valid
                        is_valid = True
                        for result in validation_results:
                            if (result.get('course_code') == course_code and 
                                not result.get('is_valid', True) and 
                                result.get('course_code') != 'CREDIT_LIMIT'):
                                is_valid = False
                                break
                        
                        # Create display text
                        display_text = f"{course_code}\n{course_name[:30]}..."  # Truncate long names
                        cell.value = display_text
                        
                        # Color coding: green if passed, default if valid but not completed
                        if is_valid and grade not in ['F', 'W', 'N', '']:
                            cell.fill = green_fill
        
        # GEN-ED section
        gen_ed_start_row = 17
        
        # GEN-ED label
        ws.merge_cells(f'A{gen_ed_start_row}:A{gen_ed_start_row + 25}')
        cell = ws[f'A{gen_ed_start_row}']
        cell.value = "GEN-ED"
        cell.font = header_font
        cell.alignment = center_align
        cell.border = border
        
        # GEN-ED categories
        categories = [
            ("Wellness\n7 Credits", 4),
            ("Entrepreneurship\n5 Credits", 2),
            ("Language and Communication\n15 Credits", 6),
            ("Thai Citizen and Global Citizenship\n2 Credits", 2),
            ("Aesthetics\n3 Credits", 2),
            ("Free Electives\n6 Credits", 6),
            ("Others", 4)
        ]
        
        current_row = gen_ed_start_row
        for category_name, num_slots in categories:
            # Category header
            ws.merge_cells(f'B{current_row}:Q{current_row}')
            cell = ws[f'B{current_row}']
            cell.value = category_name
            cell.font = header_font
            cell.alignment = center_align
            cell.border = border
            cell.fill = gray_fill
            current_row += 1
            
            # Slots for this category
            for slot_num in range(1, num_slots + 1):
                # Slot number
                ws[f'A{current_row}'] = str(slot_num)
                ws[f'A{current_row}'].alignment = center_align
                ws[f'A{current_row}'].border = border
                ws[f'A{current_row}'].font = small_font
                
                # Empty slots across all semester columns
                for col_letter in ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q']:
                    cell = ws[f'{col_letter}{current_row}']
                    cell.border = border
                    cell.alignment = left_align
                    cell.font = small_font
                
                current_row += 1
        
        # Right side summary
        summary_start_row = 6
        
        # Credit summary
        ws[f'R{summary_start_row}'] = "Credit Completed"
        ws[f'R{summary_start_row}'].font = small_font
        ws[f'R{summary_start_row}'].border = border
        
        ws[f'R{summary_start_row + 1}'] = "Credit Left"
        ws[f'R{summary_start_row + 1}'].font = small_font
        ws[f'R{summary_start_row + 1}'].border = border
        
        # Calculate completed credits
        total_credits = 0
        for semester in semesters:
            for course in semester.get('courses', []):
                if course.get('grade') not in ['F', 'W', 'N', '']:
                    total_credits += course.get('credits', 0)
        
        ws[f'S{summary_start_row}'] = total_credits
        ws[f'S{summary_start_row}'].border = border
        ws[f'S{summary_start_row}'].alignment = center_align
        
        # Cum GPA
        ws[f'S{summary_start_row + 3}'] = "Cum GPA"
        ws[f'S{summary_start_row + 3}'].font = small_font
        ws[f'S{summary_start_row + 3}'].border = border
        
        if semesters:
            # Get the latest cumulative GPA
            latest_gpa = None
            for semester in reversed(semesters):
                if semester.get('cum_gpa') is not None:
                    latest_gpa = semester.get('cum_gpa')
                    break
            
            if latest_gpa is not None:
                ws[f'S{summary_start_row + 4}'] = latest_gpa
                ws[f'S{summary_start_row + 4}'].border = border
                ws[f'S{summary_start_row + 4}'].alignment = center_align
        
        # GEN-ED summary
        ws[f'R{summary_start_row + 6}'] = "GEN-ED"
        ws[f'R{summary_start_row + 6}'].font = small_font
        ws[f'R{summary_start_row + 6}'].border = border
        
        # Save to bytes
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            wb.save(tmp_file.name)
            
            with open(tmp_file.name, 'rb') as f:
                excel_bytes = f.read()
            
            os.unlink(tmp_file.name)
            return excel_bytes
            
    except Exception as e:
        st.error(f"Error creating PQI Excel file: {e}")
        return None

def main():
    st.set_page_config(
        page_title="Course Registration Validator", 
        page_icon="🎓",
        layout="wide"
    )
    
    st.title("🎓 Course Registration Validation System")
    st.markdown("*PQI Registration Format Generator*")
    
    # Initialize session state
    if 'student_info' not in st.session_state:
        st.session_state.student_info = {}
    if 'semesters' not in st.session_state:
        st.session_state.semesters = []
    if 'validation_results' not in st.session_state:
        st.session_state.validation_results = []
    if 'selected_course_data' not in st.session_state:
        st.session_state.selected_course_data = None
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
    # Load available course data
    available_course_data = load_available_course_data()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        if available_course_data:
            selected_catalog = st.selectbox(
                "📚 Select Course Catalog",
                options=list(available_course_data.keys()),
                help="Choose the course catalog for validation"
            )
            
            if selected_catalog:
                st.session_state.selected_course_data = available_course_data[selected_catalog]
                st.success(f"✅ Using: {available_course_data[selected_catalog]['filename']}")
        else:
            st.error("❌ No course data files found")
            st.stop()
        
        st.divider()
        
        st.header("📁 Upload Transcript")
        pdf_file = st.file_uploader(
            "Upload PDF Transcript", 
            type=['pdf'],
            help="Upload student transcript PDF for processing"
        )
        
        if pdf_file is not None:
            st.info(f"📄 File: {pdf_file.name}")
            st.info(f"📊 Size: {len(pdf_file.getvalue()) / 1024:.1f} KB")
            
            if 'last_pdf_name' not in st.session_state or st.session_state.last_pdf_name != pdf_file.name:
                st.session_state.processing_complete = False
                st.session_state.student_info = {}
                st.session_state.semesters = []
                st.session_state.validation_results = []
                st.session_state.last_pdf_name = pdf_file.name
    
    # Main processing
    if pdf_file is not None and st.session_state.selected_course_data is not None:
        
        if not st.session_state.processing_complete:
            with st.spinner("🔄 Processing PDF... Please wait."):
                
                pdf_bytes = pdf_file.getvalue()
                extracted_text = extract_text_from_pdf_bytes(pdf_bytes)
                
                if not extracted_text:
                    st.error("❌ No text extracted from PDF")
                    st.stop()
                
                try:
                    extractor = PDFExtractor()
                    student_info, semesters, _ = extractor.process_pdf(None, extracted_text)
                    
                    if not student_info or not semesters:
                        st.error("❌ Failed to process transcript data")
                        st.stop()
                    
                    # Validate data
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                        json.dump(st.session_state.selected_course_data['data'], tmp_file)
                        tmp_path = tmp_file.name
                    
                    validator = CourseRegistrationValidator(tmp_path)
                    passed_courses_history = validator.build_passed_courses_history(semesters)
                    
                    all_results = []
                    for i, semester in enumerate(semesters):
                        credit_valid, credit_reason = validator.validate_credit_limit(semester)
                        if not credit_valid:
                            all_results.append({
                                "semester": semester.get("semester", ""),
                                "semester_index": i,
                                "course_code": "CREDIT_LIMIT", 
                                "course_name": "Credit Limit Check",
                                "grade": "N/A",
                                "is_valid": True,
                                "reason": credit_reason,
                                "type": "credit_limit"
                            })
                        
                        for course in semester.get("courses", []):
                            is_valid, reason = validator.validate_course(
                                course, i, semesters, passed_courses_history, all_results
                            )
                            
                            all_results.append({
                                "semester": semester.get("semester", ""),
                                "semester_index": i,
                                "course_code": course.get("code", ""),
                                "course_name": course.get("name", ""),
                                "grade": course.get("grade", ""),
                                "is_valid": is_valid,
                                "reason": reason,
                                "type": "prerequisite"
                            })
                    
                    validator.propagate_invalidation(semesters, all_results)
                    os.unlink(tmp_path)
                    
                    st.session_state.student_info = student_info
                    st.session_state.semesters = semesters
                    st.session_state.validation_results = all_results
                    st.session_state.processing_complete = True
                    
                except Exception as e:
                    st.error(f"❌ Error during processing: {e}")
                    st.stop()
        
        # Display results
        if st.session_state.processing_complete:
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.header("📋 Student Information")
                st.write(f"**Student ID:** {st.session_state.student_info.get('id', 'Unknown')}")
                st.write(f"**Name:** {st.session_state.student_info.get('name', 'Unknown')}")
                st.write(f"**Field of Study:** {st.session_state.student_info.get('field_of_study', 'Unknown')}")
                
                st.divider()
                st.subheader("📚 Semester Summary")
                for i, sem in enumerate(st.session_state.semesters):
                    semester_name = sem.get('semester', f'Semester {i+1}')
                    course_count = len(sem.get('courses', []))
                    total_credits = sem.get('total_credits', 0)
                    st.write(f"• **{semester_name}:** {course_count} courses, {total_credits} credits")
            
            with col2:
                st.header("✅ Validation Results")
                
                invalid_results = [r for r in st.session_state.validation_results 
                                 if not r.get("is_valid", True) and r.get("course_code") != "CREDIT_LIMIT"]
                total_courses = len([r for r in st.session_state.validation_results 
                                   if r.get("course_code") != "CREDIT_LIMIT"])
                
                if len(invalid_results) == 0:
                    st.success(f"🎉 **Excellent!** All {total_courses} registrations are valid!")
                else:
                    st.error(f"⚠️ **Issues Found:** {len(invalid_results)} invalid registrations")
                
                if invalid_results:
                    with st.expander("❌ Invalid Registrations", expanded=True):
                        for result in invalid_results:
                            st.error(f"**{result.get('semester')}:** {result.get('course_code')} - {result.get('course_name')}")
                            st.write(f"   *Issue:* {result.get('reason')}")
            
            # Download section
            st.divider()
            st.header("📥 Download PQI Registration Report")
            
            # Generate PQI Excel format
            excel_bytes = create_pqi_registration_excel(
                st.session_state.student_info,
                st.session_state.semesters,
                st.session_state.validation_results
            )
            
            if excel_bytes:
                col_dl1, col_dl2, col_dl3 = st.columns(3)
                
                with col_dl1:
                    st.download_button(
                        label="📋 Download PQI Registration (.xlsx)",
                        data=excel_bytes,
                        file_name=f"PQI_registration_{st.session_state.student_info.get('id', 'unknown')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help="Exact PQI registration format with course planning grid",
                        use_container_width=True
                    )
                
                with col_dl2:
                    # Text report
                    validator = CourseRegistrationValidator(
                        str(Path(__file__).parent / "course_data" / st.session_state.selected_course_data['filename'])
                    )
                    report_text = validator.generate_summary_report(
                        st.session_state.student_info, 
                        st.session_state.semesters, 
                        st.session_state.validation_results
                    )
                    
                    st.download_button(
                        label="📄 Download Text Report",
                        data=report_text,
                        file_name=f"validation_report_{st.session_state.student_info.get('id', 'unknown')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                with col_dl3:
                    # JSON data
                    export_data = {
                        "student_info": st.session_state.student_info,
                        "semesters": st.session_state.semesters,
                        "validation_results": st.session_state.validation_results
                    }
                    
                    st.download_button(
                        label="💾 Download JSON Data",
                        data=json.dumps(export_data, indent=2),
                        file_name=f"transcript_data_{st.session_state.student_info.get('id', 'unknown')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
            else:
                st.error("❌ Failed to generate PQI Excel file")
            
            # Process another file
            st.divider()
            if st.button("🔄 Process Another PDF", type="secondary"):
                st.session_state.processing_complete = False
                st.session_state.student_info = {}
                st.session_state.semesters = []
                st.session_state.validation_results = []
                if 'last_pdf_name' in st.session_state:
                    del st.session_state.last_pdf_name
                st.rerun()
    
    else:
        # Welcome screen
        st.info("📋 **Ready to generate PQI Registration format!**")
        
        col_info1, col_info2 = st.columns([1, 1])
        
        with col_info1:
            st.markdown("### 🎯 How to use:")
            st.markdown("""
            1. **Select course catalog** (already loaded!)
            2. **Upload PDF transcript** in the sidebar
            3. **Wait for automatic processing** ⚡
            4. **Download PQI registration format** 📋
            """)
        
        with col_info2:
            st.markdown("### 📋 PQI Format Features:")
            st.markdown("• **Exact grid layout** - 4 years × 2 semesters")
            st.markdown("• **Color-coded courses** - Green for completed")
            st.markdown("• **IE and GEN-ED sections** - Properly organized")
            st.markdown("• **Credit tracking** - Automatic calculations")

if __name__ == "__main__":
    main()
