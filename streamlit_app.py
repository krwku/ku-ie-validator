import streamlit as st
import json
import sys
from pathlib import Path
import tempfile
import os
import traceback

# Add modules to path
sys.path.append(str(Path(__file__).parent))

# Import our modules
from utils.pdf_processor import extract_text_from_pdf_bytes
from utils.course_data_loader import load_comprehensive_course_data
from utils.pdf_extractor import PDFExtractor
from utils.validation_adapter import ValidationAdapter
from validator import CourseRegistrationValidator

# Import the fixed generators
from utils.excel_generator import create_smart_registration_excel, classify_course, load_course_categories
from utils.semester_flow_generator import create_semester_flow_html

def safe_course_classification():
    """Safely load course categories with error handling."""
    try:
        return load_course_categories()
    except Exception as e:
        st.error(f"Error loading course categories: {e}")
        return {
            "ie_core": {},
            "technical_electives": {},
            "gen_ed": {
                "wellness": {},
                "entrepreneurship": {},
                "language_communication": {},
                "thai_citizen_global": {},
                "aesthetics": {}
            },
            "all_courses": {}
        }

def analyze_unidentified_courses(semesters, course_categories):
    """Analyze transcript for unidentified courses."""
    unidentified_courses = []
    
    try:
        for semester in semesters:
            for course in semester.get("courses", []):
                course_code = course.get("code", "")
                course_name = course.get("name", "")
                
                if course_code:
                    category, subcategory, is_identified = classify_course(
                        course_code, 
                        course_name,
                        course_categories
                    )
                    
                    if not is_identified:
                        unidentified_courses.append({
                            "code": course_code,
                            "name": course_name,
                            "semester": semester.get("semester", ""),
                            "credits": course.get("credits", 0),
                            "grade": course.get("grade", "")
                        })
    except Exception as e:
        st.error(f"Error analyzing courses: {e}")
    
    return unidentified_courses

def calculate_credit_summary(semesters, course_categories):
    """Calculate credit summary by category."""
    try:
        summary = {
            "ie_core": 0,
            "wellness": 0,
            "entrepreneurship": 0,
            "language_communication": 0,
            "thai_citizen_global": 0,
            "aesthetics": 0,
            "technical_electives": 0,
            "free_electives": 0,
            "unidentified": 0
        }
        
        for semester in semesters:
            for course in semester.get("courses", []):
                course_code = course.get("code", "")
                course_name = course.get("name", "")
                grade = course.get("grade", "")
                credits = course.get("credits", 0)
                
                # Only count completed courses
                if grade in ["A", "B+", "B", "C+", "C", "D+", "D", "P"]:
                    category, subcategory, is_identified = classify_course(
                        course_code, course_name, course_categories
                    )
                    
                    if category == "ie_core":
                        summary["ie_core"] += credits
                    elif category == "gen_ed":
                        summary[subcategory] += credits
                    elif category == "technical_electives":
                        summary["technical_electives"] += credits
                    elif category == "unidentified":
                        summary["unidentified"] += credits
                    else:
                        summary["free_electives"] += credits
        
        return summary
    except Exception as e:
        st.error(f"Error calculating credit summary: {e}")
        return {}

def main():
    st.set_page_config(
        page_title="KU IE Course Validator", 
        page_icon="🎓",
        layout="wide"
    )
    
    st.title("🎓 KU Industrial Engineering Course Validator")
    st.markdown("*Smart Registration Planning with Advanced Course Detection*")
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
    if 'unidentified_count' not in st.session_state:
        st.session_state.unidentified_count = 0
    if 'course_categories' not in st.session_state:
        st.session_state.course_categories = None
    
    # Load course data
    try:
        available_course_data = load_comprehensive_course_data()
    except Exception as e:
        st.error(f"Error loading course data: {e}")
        available_course_data = {}
    
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
                
                # Load course categories for classification
                if st.session_state.course_categories is None:
                    with st.spinner("Loading course classification system..."):
                        st.session_state.course_categories = safe_course_classification()
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
            
            # Reset processing when new file is uploaded
            if 'last_pdf_name' not in st.session_state or st.session_state.last_pdf_name != pdf_file.name:
                st.session_state.processing_complete = False
                st.session_state.student_info = {}
                st.session_state.semesters = []
                st.session_state.validation_results = []
                st.session_state.unidentified_count = 0
                st.session_state.last_pdf_name = pdf_file.name
    
    # Main processing
    if pdf_file is not None and st.session_state.selected_course_data is not None:
        
        if not st.session_state.processing_complete:
            with st.spinner("🔄 Processing PDF and creating advanced course analysis..."):
                
                try:
                    pdf_bytes = pdf_file.getvalue()
                    
                    # Extract text from PDF
                    extracted_text = extract_text_from_pdf_bytes(pdf_bytes)
                    
                    if not extracted_text:
                        st.error("❌ No text extracted from PDF. Please ensure the PDF contains readable text.")
                        st.stop()
                    
                    # Process the extracted text
                    extractor = PDFExtractor()
                    student_info, semesters, _ = extractor.process_pdf(None, extracted_text)
                    
                    if not student_info or not semesters:
                        st.error("❌ Failed to process transcript data. Please check if the PDF format is supported.")
                        st.stop()
                    
                    # Validate data
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                        json.dump(st.session_state.selected_course_data['data'], tmp_file)
                        tmp_path = tmp_file.name
                    
                    try:
                        validator = CourseRegistrationValidator(tmp_path)
                        passed_courses_history = validator.build_passed_courses_history(semesters)
                        
                        all_results = []
                        
                        # Validate each semester
                        for i, semester in enumerate(semesters):
                            # Check credit limit
                            credit_valid, credit_reason = validator.validate_credit_limit(semester)
                            if not credit_valid:
                                all_results.append({
                                    "semester": semester.get("semester", ""),
                                    "semester_index": i,
                                    "course_code": "CREDIT_LIMIT", 
                                    "course_name": "Credit Limit Check",
                                    "grade": "N/A",
                                    "is_valid": True,  # Credit limits are warnings, not errors
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
                    
                    finally:
                        # Clean up temp file
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                    
                    # Store results
                    st.session_state.student_info = student_info
                    st.session_state.semesters = semesters
                    st.session_state.validation_results = all_results
                    st.session_state.processing_complete = True
                    
                    # Analyze unidentified courses
                    if st.session_state.course_categories:
                        unidentified_courses = analyze_unidentified_courses(
                            semesters, st.session_state.course_categories
                        )
                        st.session_state.unidentified_count = len(unidentified_courses)
                    
                except Exception as e:
                    st.error(f"❌ Error during processing: {e}")
                    with st.expander("Debug Information"):
                        st.code(traceback.format_exc())
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
            
            # Check for unidentified courses
            if st.session_state.course_categories:
                unidentified_courses = analyze_unidentified_courses(
                    st.session_state.semesters, 
                    st.session_state.course_categories
                )
                st.session_state.unidentified_count = len(unidentified_courses)
                
                if unidentified_courses:
                    st.warning(f"⚠️ **Database Update Needed:** {len(unidentified_courses)} unidentified courses found")
                    with st.expander("🔍 Unidentified Courses - Require Classification", expanded=True):
                        for course in unidentified_courses:
                            st.write(f"• **{course['code']}** - {course['name']} ({course['semester']}) - {course['credits']} credits")
                        st.info("💡 These courses need to be added to the course classification system for accurate analysis.")
                
                # Show credit summary
                credit_summary = calculate_credit_summary(
                    st.session_state.semesters, 
                    st.session_state.course_categories
                )
                
                if credit_summary:
                    st.divider()
                    st.subheader("📊 Credit Summary by Category")
                    
                    col_cr1, col_cr2, col_cr3 = st.columns(3)
                    
                    with col_cr1:
                        st.metric("IE Core", f"{credit_summary.get('ie_core', 0)}", help="Required: ~110 credits")
                        st.metric("Wellness", f"{credit_summary.get('wellness', 0)}", help="Required: 7 credits")
                        st.metric("Entrepreneurship", f"{credit_summary.get('entrepreneurship', 0)}", help="Required: 3 credits")
                    
                    with col_cr2:
                        st.metric("Language & Communication", f"{credit_summary.get('language_communication', 0)}", help="Required: 15 credits")
                        st.metric("Thai Citizen & Global", f"{credit_summary.get('thai_citizen_global', 0)}", help="Required: 2 credits")
                        st.metric("Aesthetics", f"{credit_summary.get('aesthetics', 0)}", help="Required: 3 credits")
                    
                    with col_cr3:
                        st.metric("Technical Electives", f"{credit_summary.get('technical_electives', 0)}", help="Variable requirement")
                        st.metric("Free Electives", f"{credit_summary.get('free_electives', 0)}", help="Variable requirement")
                        st.metric("Unidentified", f"{credit_summary.get('unidentified', 0)}", help="Need classification", delta_color="off")
            
            # Visualization Options - FIXED SECTION
            st.divider()
            st.header("📊 Advanced Visualizations & Downloads")
            
            # Generate flow chart - AUTO-OPEN IN NEW WINDOW
            try:
                with st.spinner("Generating interactive curriculum flow chart..."):
                    flow_html, flow_unidentified = create_semester_flow_html(
                        st.session_state.student_info,
                        st.session_state.semesters,
                        st.session_state.validation_results
                    )
                
                st.subheader("🗂️ Interactive Curriculum Flow Chart")
                st.markdown("*Visual curriculum progression with prerequisite relationships*")
                
                if flow_html and len(flow_html.strip()) > 0:
                    # Automatically open flow chart in new window
                    js_code = f"""
                    <script>
                    const flowHTML = `{flow_html.replace('`', '\\`')}`;
                    const newWindow = window.open('', '_blank');
                    if (newWindow) {{
                        newWindow.document.write(flowHTML);
                        newWindow.document.close();
                    }}
                    </script>
                    """
                    st.components.v1.html(js_code, height=0)
                    
                    # Show success message and provide re-open option
                    col_flow1, col_flow2 = st.columns([2, 1])
                    
                    with col_flow1:
                        st.success("✅ Flow chart automatically opened in new window!")
                        if flow_unidentified > 0:
                            st.warning(f"⚠️ {flow_unidentified} unidentified courses in flow chart")
                    
                    with col_flow2:
                        # Re-open button for popup blocker cases
                        if st.button("🔄 Re-open Flow Chart", help="Click if popup was blocked"):
                            js_reopen = f"""
                            <script>
                            const flowHTML = `{flow_html.replace('`', '\\`')}`;
                            const newWindow = window.open('', '_blank');
                            newWindow.document.write(flowHTML);
                            newWindow.document.close();
                            </script>
                            """
                            st.components.v1.html(js_reopen, height=0)
                            st.success("✅ Flow chart re-opened!")
                    
                    st.info("💡 **Note:** If the window didn't open automatically, use the 'Re-open' button (popup might be blocked by browser).")
                    
                else:
                    st.error("❌ No HTML content generated for flow chart")
                
            except Exception as e:
                st.error(f"Error generating flow chart: {e}")
                with st.expander("Debug Information"):
                    st.code(traceback.format_exc())
            
            # Download section
            st.divider()
            st.header("📥 Download Reports")
            
            col_dl1, col_dl2, col_dl3, col_dl4 = st.columns(4)
            
            with col_dl1:
                # Generate Smart Excel format
                try:
                    with st.spinner("Creating smart Excel analysis..."):
                        excel_bytes, excel_unidentified = create_smart_registration_excel(
                            st.session_state.student_info,
                            st.session_state.semesters,
                            st.session_state.validation_results
                        )
                    
                    if excel_bytes:
                        st.download_button(
                            label="📋 Smart Excel Analysis",
                            data=excel_bytes,
                            file_name=f"KU_IE_smart_analysis_{st.session_state.student_info.get('id', 'unknown')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            help="Comprehensive course analysis with alerts and recommendations",
                            use_container_width=True
                        )
                        
                        if excel_unidentified > 0:
                            st.warning(f"⚠️ {excel_unidentified} unidentified")
                    else:
                        st.error("❌ Excel generation failed")
                        
                except Exception as e:
                    st.error(f"❌ Excel error: {str(e)[:50]}...")
                    with st.expander("Debug"):
                        st.code(str(e))
            
            with col_dl2:
                # HTML Flow Chart download
                try:
                    if 'flow_html' in locals():
                        st.download_button(
                            label="🗂️ Flow Chart (HTML)",
                            data=flow_html.encode('utf-8'),
                            file_name=f"curriculum_flow_{st.session_state.student_info.get('id', 'unknown')}.html",
                            mime="text/html",
                            help="Interactive semester-based curriculum flow chart",
                            use_container_width=True
                        )
                        
                        if 'flow_unidentified' in locals() and flow_unidentified > 0:
                            st.warning(f"⚠️ {flow_unidentified} unidentified")
                    else:
                        # Generate flow chart for download if not already generated
                        flow_html, flow_unidentified = create_semester_flow_html(
                            st.session_state.student_info,
                            st.session_state.semesters,
                            st.session_state.validation_results
                        )
                        
                        st.download_button(
                            label="🗂️ Flow Chart (HTML)",
                            data=flow_html.encode('utf-8'),
                            file_name=f"curriculum_flow_{st.session_state.student_info.get('id', 'unknown')}.html",
                            mime="text/html",
                            help="Interactive semester-based curriculum flow chart",
                            use_container_width=True
                        )
                        
                        if flow_unidentified > 0:
                            st.warning(f"⚠️ {flow_unidentified} unidentified")
                        
                except Exception as e:
                    st.error(f"❌ Flow chart error: {str(e)[:50]}...")
            
            with col_dl3:
                # Text report
                try:
                    course_data_path = str(Path(__file__).parent / "course_data" / st.session_state.selected_course_data['filename'])
                    validator = CourseRegistrationValidator(course_data_path)
                    report_text = validator.generate_summary_report(
                        st.session_state.student_info, 
                        st.session_state.semesters, 
                        st.session_state.validation_results
                    )
                    
                    st.download_button(
                        label="📄 Validation Report",
                        data=report_text,
                        file_name=f"validation_report_{st.session_state.student_info.get('id', 'unknown')}.txt",
                        mime="text/plain",
                        help="Detailed prerequisite validation report",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"❌ Report error: {str(e)[:50]}...")
            
            with col_dl4:
                # JSON data
                try:
                    export_data = {
                        "student_info": st.session_state.student_info,
                        "semesters": st.session_state.semesters,
                        "validation_results": st.session_state.validation_results,
                        "unidentified_count": st.session_state.unidentified_count,
                        "metadata": {
                            "course_catalog": st.session_state.selected_course_data.get('filename', ''),
                            "generated_timestamp": str(st.session_state.get('processing_timestamp', 'unknown'))
                        }
                    }
                    
                    st.download_button(
                        label="💾 Raw Data (JSON)",
                        data=json.dumps(export_data, indent=2),
                        file_name=f"transcript_data_{st.session_state.student_info.get('id', 'unknown')}.json",
                        mime="application/json",
                        help="Raw extracted and validated data",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"❌ JSON error: {str(e)[:50]}...")
            
            # Process another file
            st.divider()
            if st.button("🔄 Process Another PDF", type="secondary"):
                # Reset all session state
                for key in ['processing_complete', 'student_info', 'semesters', 'validation_results', 
                           'unidentified_count', 'last_pdf_name']:
                    if key in st.session_state:
                        if key in ['student_info', 'semesters', 'validation_results']:
                            st.session_state[key] = [] if key != 'student_info' else {}
                        else:
                            del st.session_state[key]
                st.rerun()
    
    else:
        # Welcome screen
        st.info("📋 **Ready for advanced course validation and visualization!**")
        
        col_info1, col_info2 = st.columns([1, 1])
        
        with col_info1:
            st.markdown("### 🎯 How to use:")
            st.markdown("""
            1. **Select course catalog** (IE 2560 or 2565)
            2. **Upload PDF transcript** in the sidebar
            3. **Wait for processing** ⚡
            4. **View interactive visualizations** 🗂️
            5. **Download various report formats** 📋
            """)
        
        with col_info2:
            st.markdown("### 🚀 Key Features:")
            st.markdown("• **Smart course detection** - Automatically categorizes courses")
            st.markdown("• **Unidentified course alerts** - Highlights courses needing classification")
            st.markdown("• **Interactive flow chart** - Visual semester progression")
            st.markdown("• **Comprehensive Excel analysis** - Detailed credit breakdowns")
            st.markdown("• **Prerequisite validation** - Checks course requirements")
            st.markdown("• **Progress tracking** - Credit completion by category")
    
    # Status bar at bottom
    st.divider()
    col_status1, col_status2, col_status3 = st.columns([2, 2, 1])
    
    with col_status1:
        if st.session_state.unidentified_count > 0:
            st.warning(f"⚠️ Database maintenance needed: {st.session_state.unidentified_count} unidentified courses")
        elif st.session_state.processing_complete:
            st.success("✅ All courses successfully classified")
    
    with col_status2:
        if st.session_state.processing_complete:
            invalid_count = len([r for r in st.session_state.validation_results 
                               if not r.get("is_valid", True) and r.get("course_code") != "CREDIT_LIMIT"])
            if invalid_count > 0:
                st.error(f"❌ {invalid_count} validation issues found")
            else:
                st.success("✅ All validations passed")
    
    with col_status3:
        st.markdown("*Created for Raphin P.*", 
                   help="Advanced course validation with smart detection")

if __name__ == "__main__":
    main()
