import streamlit as st
import json
import sys
from pathlib import Path
import tempfile
import os
import io
import PyPDF2

# Add your existing modules to path
sys.path.append(str(Path(__file__).parent))

# Import ONLY the non-GUI parts of your code
from utils.pdf_extractor import PDFExtractor
from utils.validation_adapter import ValidationAdapter
from utils.file_operations import save_validation_report_excel  # Add this import
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
                
                # Create a friendly name for the dropdown
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
        # Create a BytesIO object from the uploaded file
        pdf_file = io.BytesIO(pdf_bytes)
        
        # Create PDF reader
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

def create_excel_report(student_info, semesters, validation_results):
    """Create Excel report and return as bytes"""
    try:
        # Create temporary file for Excel report
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        # Use your existing Excel export function
        success = save_validation_report_excel(student_info, semesters, validation_results, tmp_path)
        
        if success:
            # Read the Excel file as bytes
            with open(tmp_path, 'rb') as f:
                excel_bytes = f.read()
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            return excel_bytes
        else:
            return None
            
    except Exception as e:
        st.error(f"Error creating Excel report: {e}")
        return None

def main():
    st.set_page_config(
        page_title="Course Registration Validator", 
        page_icon="🎓",
        layout="wide"
    )
    
    st.title("🎓 Course Registration Validation System")
    st.markdown("*Created for Raphin P.*")
    
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
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Course data selection (no upload needed!)
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
            st.error("❌ No course data files found in repository")
            st.stop()
        
        st.divider()
        
        # PDF upload
        st.header("📁 Upload Transcript")
        pdf_file = st.file_uploader(
            "Upload PDF Transcript", 
            type=['pdf'],
            help="Upload student transcript PDF for automatic processing and validation"
        )
        
        # Show PDF info if uploaded
        if pdf_file is not None:
            st.info(f"📄 File: {pdf_file.name}")
            st.info(f"📊 Size: {len(pdf_file.getvalue()) / 1024:.1f} KB")
            
            # Reset processing state when new file is uploaded
            if 'last_pdf_name' not in st.session_state or st.session_state.last_pdf_name != pdf_file.name:
                st.session_state.processing_complete = False
                st.session_state.student_info = {}
                st.session_state.semesters = []
                st.session_state.validation_results = []
                st.session_state.last_pdf_name = pdf_file.name
    
    # Main content area
    if pdf_file is not None and st.session_state.selected_course_data is not None:
        
        # Auto-process when file is uploaded (only once)
        if not st.session_state.processing_complete:
            with st.spinner("🔄 Processing PDF automatically... Please wait."):
                
                # Step 1: Extract text
                pdf_bytes = pdf_file.getvalue()
                extracted_text = extract_text_from_pdf_bytes(pdf_bytes)
                
                if not extracted_text:
                    st.error("❌ No text extracted from PDF. This might be a scanned/image PDF.")
                    st.stop()
                
                # Step 2: Process text
                try:
                    extractor = PDFExtractor()
                    student_info, semesters, _ = extractor.process_pdf(None, extracted_text)
                    
                    if not student_info or not semesters:
                        st.error("❌ Failed to process extracted text into transcript data")
                        with st.expander("🔍 Debug: Show Extracted Text"):
                            st.text_area("Raw Text", extracted_text, height=200)
                        st.stop()
                    
                    # Step 3: Validate automatically
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                        json.dump(st.session_state.selected_course_data['data'], tmp_file)
                        tmp_path = tmp_file.name
                    
                    validator = CourseRegistrationValidator(tmp_path)
                    passed_courses_history = validator.build_passed_courses_history(semesters)
                    
                    all_results = []
                    for i, semester in enumerate(semesters):
                        # Check credit limits
                        credit_valid, credit_reason = validator.validate_credit_limit(semester)
                        if not credit_valid:
                            all_results.append({
                                "semester": semester.get("semester", ""),
                                "semester_index": i,
                                "course_code": "CREDIT_LIMIT",
                                "course_name": "Credit Limit Check",
                                "grade": "N/A",
                                "is_valid": True,  # Just a warning
                                "reason": credit_reason,
                                "type": "credit_limit"
                            })
                        
                        # Validate each course
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
                    
                    # Propagate invalidation
                    validator.propagate_invalidation(semesters, all_results)
                    
                    # Clean up temp file
                    os.unlink(tmp_path)
                    
                    # Store results in session state
                    st.session_state.student_info = student_info
                    st.session_state.semesters = semesters
                    st.session_state.validation_results = all_results
                    st.session_state.processing_complete = True
                    
                except Exception as e:
                    st.error(f"❌ Error during processing: {e}")
                    with st.expander("🔍 Debug Information"):
                        st.exception(e)
                    st.stop()
        
        # Display results after processing is complete
        if st.session_state.processing_complete:
            
            # Two-column layout for results
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.header("📋 Student Information")
                
                # Student info in a nice format
                info_container = st.container()
                with info_container:
                    st.write(f"**Student ID:** {st.session_state.student_info.get('id', 'Unknown')}")
                    st.write(f"**Name:** {st.session_state.student_info.get('name', 'Unknown')}")
                    st.write(f"**Field of Study:** {st.session_state.student_info.get('field_of_study', 'Unknown')}")
                    st.write(f"**Date of Admission:** {st.session_state.student_info.get('date_admission', 'Unknown')}")
                
                st.divider()
                
                # Semester summary
                st.subheader("📚 Semester Summary")
                st.write(f"**Total Semesters:** {len(st.session_state.semesters)}")
                
                for i, sem in enumerate(st.session_state.semesters):
                    semester_name = sem.get('semester', f'Semester {i+1}')
                    course_count = len(sem.get('courses', []))
                    total_credits = sem.get('total_credits', 0)
                    st.write(f"• **{semester_name}:** {course_count} courses, {total_credits} credits")
            
            with col2:
                st.header("✅ Validation Results")
                
                # Calculate summary
                invalid_results = [r for r in st.session_state.validation_results if not r.get("is_valid", True) and r.get("course_code") != "CREDIT_LIMIT"]
                credit_warnings = [r for r in st.session_state.validation_results if r.get("course_code") == "CREDIT_LIMIT"]
                total_courses = len([r for r in st.session_state.validation_results if r.get("course_code") != "CREDIT_LIMIT"])
                
                # Summary metrics
                if len(invalid_results) == 0:
                    st.success(f"🎉 **Excellent!** All {total_courses} course registrations are valid!")
                else:
                    st.error(f"⚠️ **Issues Found:** {len(invalid_results)} invalid registrations out of {total_courses} total")
                
                # Show credit warnings if any
                if credit_warnings:
                    with st.expander("⚠️ Credit Load Warnings"):
                        for warning in credit_warnings:
                            st.warning(f"📊 {warning.get('semester')}: {warning.get('reason')}")
                
                # Show invalid courses if any
                if invalid_results:
                    with st.expander("❌ Invalid Course Registrations", expanded=True):
                        for result in invalid_results:
                            st.error(f"**{result.get('semester')}:** {result.get('course_code')} - {result.get('course_name')}")
                            st.write(f"   *Issue:* {result.get('reason')}")
            
            # Download section (full width)
            st.divider()
            st.header("📥 Download Reports")
            
            col_download1, col_download2, col_download3 = st.columns(3)
            
            with col_download1:
                # Text report
                validator = CourseRegistrationValidator(str(Path(__file__).parent / "course_data" / st.session_state.selected_course_data['filename']))
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
                    help="Detailed validation report in text format",
                    use_container_width=True
                )
            
            with col_download2:
                # Excel report
                excel_bytes = create_excel_report(
                    st.session_state.student_info,
                    st.session_state.semesters,
                    st.session_state.validation_results
                )
                
                if excel_bytes:
                    st.download_button(
                        label="📊 Download Excel Report",
                        data=excel_bytes,
                        file_name=f"validation_report_{st.session_state.student_info.get('id', 'unknown')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help="Detailed validation report in Excel format with formatting",
                        use_container_width=True
                    )
                else:
                    st.button("📊 Excel Export Error", disabled=True, use_container_width=True)
            
            with col_download3:
                # JSON data export
                export_data = {
                    "student_info": st.session_state.student_info,
                    "semesters": st.session_state.semesters,
                    "validation_results": st.session_state.validation_results,
                    "course_catalog_used": st.session_state.selected_course_data['filename']
                }
                
                st.download_button(
                    label="💾 Download JSON Data",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"transcript_data_{st.session_state.student_info.get('id', 'unknown')}.json",
                    mime="application/json",
                    help="Complete transcript and validation data",
                    use_container_width=True
                )
            
            # Option to process another file
            st.divider()
            if st.button("🔄 Process Another PDF", type="secondary"):
                # Reset state to process another file
                st.session_state.processing_complete = False
                st.session_state.student_info = {}
                st.session_state.semesters = []
                st.session_state.validation_results = []
                if 'last_pdf_name' in st.session_state:
                    del st.session_state.last_pdf_name
                st.rerun()
    
    else:
        # Welcome message and instructions
        st.info("📋 **Ready to validate transcripts!**")
        
        col_info1, col_info2 = st.columns([1, 1])
        
        with col_info1:
            st.markdown("### 🎯 How to use:")
            st.markdown("""
            1. **Select course catalog** (already loaded!)
            2. **Upload PDF transcript** in the sidebar
            3. **Wait for automatic processing** ⚡
            4. **View validation results** 
            5. **Download reports** in your preferred format
            """)
        
        with col_info2:
            st.markdown("### 📚 Available Catalogs:")
            if available_course_data:
                for catalog_name, info in available_course_data.items():
                    st.markdown(f"• {catalog_name}")
            
            st.markdown("### 📄 Supported PDF Format:")
            st.markdown("• Academic transcripts with student info and course grades")
            st.markdown("• Text-based PDFs (not scanned images)")

if __name__ == "__main__":
    main()
