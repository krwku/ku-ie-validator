import streamlit as st
import json
import sys
from pathlib import Path
import tempfile
import os

# Add modules to path
sys.path.append(str(Path(__file__).parent))

# Import our clean modules
from utils.pdf_processor import extract_text_from_pdf_bytes
from utils.excel_generator import create_smart_registration_excel
from utils.course_data_loader import load_comprehensive_course_data
from utils.pdf_extractor import PDFExtractor
from utils.validation_adapter import ValidationAdapter
from validator import CourseRegistrationValidator

def main():
    st.set_page_config(
        page_title="KU IE Course Validator", 
        page_icon="🎓",
        layout="wide"
    )
    
    st.title("🎓 KU Industrial Engineering Course Validator")
    st.markdown("*Smart Registration Planning with Dynamic Course Classification*")
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
    
    # Load course data
    available_course_data = load_comprehensive_course_data()
    
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
            help="Upload student transcript PDF"
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
            with st.spinner("🔄 Processing PDF and creating smart course classification..."):
                
                pdf_bytes = pdf_file.getvalue()
                
                try:
                    # Extract text from PDF using our fixed function
                    extracted_text = extract_text_from_pdf_bytes(pdf_bytes)
                    
                    if not extracted_text:
                        st.error("❌ No text extracted from PDF")
                        st.stop()
                    
                    # Process the extracted text
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
            st.header("📥 Download Smart Registration Reports")
            
            col_dl1, col_dl2, col_dl3 = st.columns(3)
            
            with col_dl1:
                # Generate Smart Excel format
                try:
                    excel_bytes = create_smart_registration_excel(
                        st.session_state.student_info,
                        st.session_state.semesters,
                        st.session_state.validation_results
                    )
                    
                    if excel_bytes:
                        st.download_button(
                            label="📋 Download Smart Registration Plan (.xlsx)",
                            data=excel_bytes,
                            file_name=f"KU_IE_smart_plan_{st.session_state.student_info.get('id', 'unknown')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            help="Intelligent course classification with dynamic layout",
                            use_container_width=True
                        )
                    else:
                        st.error("❌ Failed to generate Excel file")
                        
                except Exception as e:
                    st.error(f"❌ Excel generation error: {e}")
            
            with col_dl2:
                # Text report
                try:
                    validator = CourseRegistrationValidator(
                        str(Path(__file__).parent / "course_data" / st.session_state.selected_course_data['filename'])
                    )
                    report_text = validator.generate_summary_report(
                        st.session_state.student_info, 
                        st.session_state.semesters, 
                        st.session_state.validation_results
                    )
                    
                    st.download_button(
                        label="📄 Download Validation Report",
                        data=report_text,
                        file_name=f"validation_report_{st.session_state.student_info.get('id', 'unknown')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"❌ Report generation error: {e}")
            
            with col_dl3:
                # JSON data
                export_data = {
                    "student_info": st.session_state.student_info,
                    "semesters": st.session_state.semesters,
                    "validation_results": st.session_state.validation_results
                }
                
                st.download_button(
                    label="💾 Download Raw Data",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"transcript_data_{st.session_state.student_info.get('id', 'unknown')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
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
        st.info("📋 **Ready for smart course validation and planning!**")
        
        col_info1, col_info2 = st.columns([1, 1])
        
        with col_info1:
            st.markdown("### 🎯 How to use:")
            st.markdown("""
            1. **Select course catalog** (IE 2560 or 2565)
            2. **Upload PDF transcript** in the sidebar
            3. **Wait for smart processing** ⚡
            4. **Download intelligent registration plan** 📋
            """)
        
        with col_info2:
            st.markdown("### 🧠 Smart Features:")
            st.markdown("• **Automatic course classification** - IE Core, Gen-Ed, Electives")
            st.markdown("• **Dynamic layout** - Adjusts to your actual courses")
            st.markdown("• **Clear formatting** - Separate columns for code/name")
            st.markdown("• **Color-coded validation** - Green/Red status")
            st.markdown("• **Credit summary** - Automatic calculations by category")
    
    # Status bar at bottom with your motto
    st.divider()
    col_status1, col_status2 = st.columns([3, 1])
    with col_status2:
        st.markdown("*Created for Raphin P.*", 
                   help="This application was specially created for Raphin P.")

if __name__ == "__main__":
    main()
