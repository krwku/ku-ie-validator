import json
from pathlib import Path

def load_course_categories():
    """
    Load course categories from separate JSON files.
    Returns: dict with categorized courses
    """
    course_data_dir = Path(__file__).parent.parent / "course_data"
    
    categories = {
        "ie_core": {},  # Changed to dict to store course info
        "technical_electives": {},
        "gen_ed": {
            "wellness": {},
            "entrepreneurship": {},
            "language_communication": {},
            "thai_citizen_global": {},
            "aesthetics": {}
        },
        "all_courses": {}  # Master list of all courses
    }
    
    # Load IE Core courses from both B-IE files
    for ie_file in ["B-IE-2560.json", "B-IE-2565.json", "ie_core_courses.json"]:
        ie_path = course_data_dir / ie_file
        if ie_path.exists():
            with open(ie_path, 'r', encoding='utf-8') as f:
                ie_data = json.load(f)
                # Add from both sections
                for course in ie_data.get("industrial_engineering_courses", []):
                    categories["ie_core"][course["code"]] = course
                    categories["all_courses"][course["code"]] = course
                for course in ie_data.get("other_related_courses", []):
                    categories["ie_core"][course["code"]] = course  
                    categories["all_courses"][course["code"]] = course
    
    # Load Technical Electives
    tech_file = course_data_dir / "technical_electives.json"
    if tech_file.exists():
        with open(tech_file, 'r', encoding='utf-8') as f:
            tech_data = json.load(f)
            for course in tech_data.get("technical_electives", []):
                categories["technical_electives"][course["code"]] = course
                categories["all_courses"][course["code"]] = course
    
    # Load Gen-Ed courses with proper subcategory mapping
    gen_ed_file = course_data_dir / "gen_ed_courses.json"
    if gen_ed_file.exists():
        with open(gen_ed_file, 'r', encoding='utf-8') as f:
            gen_ed_data = json.load(f)
            gen_ed_courses = gen_ed_data.get("gen_ed_courses", {})
            
            # Map each subcategory properly
            for subcategory in ["wellness", "entrepreneurship", "language_communication", "thai_citizen_global", "aesthetics"]:
                for course in gen_ed_courses.get(subcategory, []):
                    categories["gen_ed"][subcategory][course["code"]] = course
                    categories["all_courses"][course["code"]] = course
    
    return categories

def get_prerequisite_relationships():
    """Load prerequisite relationships from course data files."""
    course_data_dir = Path(__file__).parent.parent / "course_data"
    prerequisites = {}
    
    # Load from B-IE files (most comprehensive)
    for ie_file in ["B-IE-2565.json", "B-IE-2560.json"]:  # Try 2565 first (newer)
        ie_path = course_data_dir / ie_file
        if ie_path.exists():
            try:
                with open(ie_path, 'r', encoding='utf-8') as f:
                    ie_data = json.load(f)
                    
                    # Process both course sections
                    for course in ie_data.get("industrial_engineering_courses", []):
                        code = course.get("code")
                        prereqs = course.get("prerequisites", [])
                        if code and prereqs:
                            prerequisites[code] = prereqs
                    
                break  # Use first available file
            except Exception as e:
                continue
    
    return prerequisites

def classify_course_with_proper_detection(course_code, course_name="", course_categories=None):
    """
    Classify course using the loaded JSON files.
    Returns: (category, subcategory, is_identified, year, semester)
    """
    if course_categories is None:
        course_categories = load_course_categories()
    
    code = course_code.upper()
    
    # Check IE Core courses first
    if code in course_categories["ie_core"]:
        # Determine year/semester for IE core courses based on typical curriculum flow
        year1_first = ["01417167", "01420111", "01420113", "01403117", "01403114", "01208111"]
        year1_second = ["01417168", "01420112", "01420114", "01208281", "01204111"]
        year2_first = ["01417267", "01208221", "01208241", "01213211", "01205201"]
        year2_second = ["01206221", "01206251", "01205202", "01208381"]
        year3_first = ["01206222", "01206223", "01206272", "01206311", "01206321"]
        year3_second = ["01206312", "01206322", "01206323", "01206341", "01206361"]
        year4_first = ["01206342", "01206371", "01206381", "01206452"]
        year4_second = ["01206343", "01206382", "01206495", "01206497", "01206499"]
        
        if code in year1_first:
            return ("ie_core", "foundation", True, 1, "First")
        elif code in year1_second:
            return ("ie_core", "foundation", True, 1, "Second")
        elif code in year2_first:
            return ("ie_core", "foundation", True, 2, "First")
        elif code in year2_second:
            return ("ie_core", "core", True, 2, "Second")
        elif code in year3_first:
            return ("ie_core", "core", True, 3, "First")
        elif code in year3_second:
            return ("ie_core", "core", True, 3, "Second")
        elif code in year4_first:
            return ("ie_core", "core", True, 4, "First")
        elif code in year4_second:
            return ("ie_core", "core", True, 4, "Second")
        else:
            return ("ie_core", "other", True, None, None)
    
    # Check Technical Electives
    if code in course_categories["technical_electives"]:
        return ("technical_electives", "technical", True, None, None)
    
    # Check Gen-Ed courses with proper subcategory detection
    for subcategory, courses in course_categories["gen_ed"].items():
        if code in courses:
            return ("gen_ed", subcategory, True, None, None)
    
    # Unidentified course
    return ("unidentified", "unknown", False, None, None)

def create_semester_flow_html(student_info, semesters, validation_results, course_data=None):
    """
    Create an HTML visualization with proper course detection and prerequisite arrows.
    """
    
    # Load course categories
    course_categories = load_course_categories()
    
    # Organize student courses by completion status
    completed_courses = {}
    current_courses = {}
    
    for semester in semesters:
        for course in semester.get("courses", []):
            code = course.get("code", "")
            grade = course.get("grade", "")
            
            if grade in ["A", "B+", "B", "C+", "C", "D+", "D", "P"]:
                completed_courses[code] = {
                    "grade": grade,
                    "semester": semester.get("semester", ""),
                    "credits": course.get("credits", 0)
                }
            elif grade in ["F", "W", "N", ""]:
                current_courses[code] = {
                    "grade": grade,
                    "semester": semester.get("semester", ""),
                    "credits": course.get("credits", 0)
                }
    
    # Define the fixed curriculum structure
    curriculum_structure = {
        1: {
            "First": [
                {"code": "01417167", "name": "Engineering Mathematics I", "credits": 3},
                {"code": "01420111", "name": "General Physics I", "credits": 3},
                {"code": "01420113", "name": "Laboratory in Physics I", "credits": 1},
                {"code": "01403117", "name": "Fundamentals of General Chemistry", "credits": 3},
                {"code": "01403114", "name": "Laboratory in Fundamentals of General Chemistry", "credits": 1},
                {"code": "01208111", "name": "Engineering Drawing", "credits": 3}
            ],
            "Second": [
                {"code": "01417168", "name": "Engineering Mathematics II", "credits": 3},
                {"code": "01420112", "name": "General Physics II", "credits": 3},
                {"code": "01420114", "name": "Laboratory in Physics II", "credits": 1},
                {"code": "01208281", "name": "Workshop Practice", "credits": 1},
                {"code": "01204111", "name": "Computers and Programming", "credits": 3}
            ]
        },
        2: {
            "First": [
                {"code": "01417267", "name": "Engineering Mathematics III", "credits": 3},
                {"code": "01208221", "name": "Engineering Mechanics I", "credits": 3},
                {"code": "01208241", "name": "Thermodynamics", "credits": 3},
                {"code": "01213211", "name": "Materials Science for Engineers", "credits": 3},
                {"code": "01205201", "name": "Introduction to Electrical Engineering", "credits": 3}
            ],
            "Second": [
                {"code": "01206221", "name": "Applied Probability and Statistics for Engineers", "credits": 3},
                {"code": "01206251", "name": "Engineering Economy", "credits": 3},
                {"code": "01205202", "name": "Electrical Engineering Laboratory I", "credits": 1},
                {"code": "01208381", "name": "Mechanical Engineering Laboratory I", "credits": 1}
            ]
        },
        3: {
            "First": [
                {"code": "01206222", "name": "Applied Mathematics for Industrial Engineers", "credits": 3},
                {"code": "01206223", "name": "Introduction to Experimental Design for Engineers", "credits": 3},
                {"code": "01206272", "name": "Industrial Safety", "credits": 3},
                {"code": "01206311", "name": "Manufacturing Processes I", "credits": 3},
                {"code": "01206321", "name": "Operations Research for Engineers I", "credits": 3}
            ],
            "Second": [
                {"code": "01206312", "name": "Industrial Study", "credits": 1},
                {"code": "01206322", "name": "Quality Control", "credits": 3},
                {"code": "01206323", "name": "Operations Research for Engineers II", "credits": 3},
                {"code": "01206341", "name": "Industrial Work Study", "credits": 3},
                {"code": "01206361", "name": "Computer Applications for Industrial Engineers", "credits": 3}
            ]
        },
        4: {
            "First": [
                {"code": "01206342", "name": "Production Planning and Control", "credits": 3},
                {"code": "01206371", "name": "Maintenance Engineering", "credits": 3},
                {"code": "01206381", "name": "Industrial Engineering Laboratory I", "credits": 1},
                {"code": "01206452", "name": "Industrial Cost Analysis", "credits": 3}
            ],
            "Second": [
                {"code": "01206343", "name": "Industrial Plant Design", "credits": 3},
                {"code": "01206382", "name": "Industrial Engineering Laboratory II", "credits": 1},
                {"code": "01206495", "name": "Industrial Engineering Project Preparation", "credits": 1},
                {"code": "01206497", "name": "Seminar", "credits": 1},
                {"code": "01206499", "name": "Industrial Engineering Project", "credits": 2}
            ]
        }
    }
    
    # Get prerequisite relationships from actual course data
    prerequisites = get_prerequisite_relationships()
    
    # Generate CSS styles with prerequisite arrows
    css_styles = """
    <style>
        .curriculum-container {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 10px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .student-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
            text-align: left;
        }
        
        .year-container {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
            position: relative;
        }
        
        .year-column {
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .year-header {
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
            padding: 10px;
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            border-radius: 5px;
        }
        
        .semester-section {
            margin-bottom: 20px;
        }
        
        .semester-header {
            font-size: 14px;
            font-weight: bold;
            color: #34495e;
            text-align: center;
            margin-bottom: 10px;
            padding: 8px;
            background: #ecf0f1;
            border-radius: 5px;
        }
        
        .course-box {
            margin-bottom: 8px;
            padding: 8px;
            border-radius: 5px;
            border: 2px solid #bdc3c7;
            background: white;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
        }
        
        .course-box:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .course-box:hover .prerequisites-tooltip {
            display: block;
        }
        
        .prerequisites-tooltip {
            display: none;
            position: absolute;
            top: -40px;
            left: 50%;
            transform: translateX(-50%);
            background: #2c3e50;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 10px;
            white-space: nowrap;
            z-index: 1000;
        }
        
        .prerequisites-tooltip::after {
            content: '';
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: #2c3e50 transparent transparent transparent;
        }
        
        .course-completed {
            background: linear-gradient(135deg, #2ecc71, #27ae60);
            color: white;
            border-color: #27ae60;
        }
        
        .course-failed {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            color: white;
            border-color: #c0392b;
        }
        
        .course-withdrawn {
            background: linear-gradient(135deg, #f39c12, #e67e22);
            color: white;
            border-color: #e67e22;
        }
        
        .course-unidentified {
            background: linear-gradient(135deg, #9b59b6, #8e44ad);
            color: white;
            border-color: #8e44ad;
        }
        
        .course-code {
            font-size: 11px;
            font-weight: bold;
            margin-bottom: 4px;
        }
        
        .course-name {
            font-size: 10px;
            line-height: 1.2;
            margin-bottom: 4px;
        }
        
        .course-info {
            font-size: 9px;
            opacity: 0.8;
        }
        
        .electives-section {
            margin-top: 30px;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .electives-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .elective-category {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
        }
        
        .category-header {
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            text-align: center;
            padding: 8px;
            color: white;
            border-radius: 5px;
        }
        
        .category-header.wellness {
            background: linear-gradient(45deg, #e74c3c, #c0392b);
        }
        
        .category-header.entrepreneurship {
            background: linear-gradient(45deg, #f39c12, #e67e22);
        }
        
        .category-header.language {
            background: linear-gradient(45deg, #3498db, #2980b9);
        }
        
        .category-header.thai-citizen {
            background: linear-gradient(45deg, #9b59b6, #8e44ad);
        }
        
        .category-header.aesthetics {
            background: linear-gradient(45deg, #1abc9c, #16a085);
        }
        
        .category-header.technical {
            background: linear-gradient(45deg, #34495e, #2c3e50);
        }
        
        .category-header.unidentified {
            background: linear-gradient(45deg, #e67e22, #d35400);
        }
        
        .legend {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 15px;
            margin: 20px 0;
            padding: 15px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
        }
        
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 3px;
            border: 1px solid #bdc3c7;
        }
        
        .stats-summary {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .stat-item {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .stat-label {
            font-size: 12px;
            color: #7f8c8d;
            margin-top: 5px;
        }
        
        .prerequisite-info {
            background: #ecf0f1;
            border-radius: 5px;
            padding: 10px;
            margin-top: 20px;
            font-size: 12px;
        }
        
        .prerequisite-info h4 {
            margin: 0 0 10px 0;
            color: #2c3e50;
        }
        
        .credit-requirements {
            background: #e8f5e8;
            border-radius: 5px;
            padding: 15px;
            margin-top: 15px;
            font-size: 12px;
        }
        
        .credit-requirements h4 {
            margin: 0 0 10px 0;
            color: #27ae60;
        }
    </style>
    """
    
    # Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>IE Curriculum Flow Chart</title>
        <meta charset="utf-8">
        {css_styles}
    </head>
    <body>
        <div class="curriculum-container">
            <div class="header">
                <h1>Industrial Engineering Curriculum Flow Chart</h1>
                <div class="student-info">
                    <div><strong>Student ID:</strong> {student_info.get('id', 'N/A')}</div>
                    <div><strong>Name:</strong> {student_info.get('name', 'N/A')}</div>
                    <div><strong>Field of Study:</strong> {student_info.get('field_of_study', 'N/A')}</div>
                    <div><strong>Generated:</strong> Advanced Flow Chart System</div>
                </div>
            </div>
            
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background: linear-gradient(135deg, #2ecc71, #27ae60);"></div>
                    <span>Completed</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: linear-gradient(135deg, #e74c3c, #c0392b);"></div>
                    <span>Failed</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: linear-gradient(135deg, #f39c12, #e67e22);"></div>
                    <span>Withdrawn</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: white;"></div>
                    <span>Not Taken</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: linear-gradient(135deg, #9b59b6, #8e44ad);"></div>
                    <span>Unidentified</span>
                </div>
            </div>
            
            <div class="prerequisite-info">
                <h4>💡 How to read prerequisites:</h4>
                <p>Hover over any course box to see its prerequisite requirements. Courses are arranged in chronological order showing the recommended progression path.</p>
            </div>
            
            <div class="credit-requirements">
                <h4>📋 Credit Requirements (Total: 140 credits)</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                    <div>• IE Core: 110 credits</div>
                    <div>• Wellness: 7 credits</div>
                    <div>• Entrepreneurship: 3 credits</div>
                    <div>• Language & Communication: 15 credits</div>
                    <div>• Thai Citizen & Global: 2 credits</div>
                    <div>• Aesthetics: 3 credits</div>
                    <div>• Free Electives: Variable</div>
                </div>
            </div>
    """
    
    # Generate the main curriculum grid
    html_content += '<div class="year-container">'
    
    for year in range(1, 5):
        html_content += f'''
        <div class="year-column">
            <div class="year-header">Year {year}</div>
        '''
        
        for semester in ["First", "Second"]:
            html_content += f'''
            <div class="semester-section">
                <div class="semester-header">{semester} Semester</div>
            '''
            
            if year in curriculum_structure and semester in curriculum_structure[year]:
                for course in curriculum_structure[year][semester]:
                    code = course["code"]
                    name = course["name"]
                    credits = course["credits"]
                    
                    # Determine course status
                    css_class = "course-box"
                    status_info = ""
                    
                    if code in completed_courses:
                        css_class += " course-completed"
                        status_info = f"Grade: {completed_courses[code]['grade']}"
                    elif code in current_courses:
                        grade = current_courses[code]['grade']
                        if grade == "F":
                            css_class += " course-failed"
                            status_info = "Grade: F"
                        elif grade in ["W"]:
                            css_class += " course-withdrawn"
                            status_info = "Withdrawn"
                        else:
                            status_info = f"Current: {grade if grade else 'In Progress'}"
                    else:
                        status_info = "Not taken"
                    
                    # Get prerequisites for tooltip
                    prereq_list = prerequisites.get(code, [])
                    prereq_text = ", ".join(prereq_list) if prereq_list else "No prerequisites"
                    
                    html_content += f'''
                    <div class="{css_class}">
                        <div class="prerequisites-tooltip">Prerequisites: {prereq_text}</div>
                        <div class="course-code">{code}</div>
                        <div class="course-name">{name}</div>
                        <div class="course-info">{credits} credits • {status_info}</div>
                    </div>
                    '''
            
            html_content += '</div>'  # End semester-section
        
        html_content += '</div>'  # End year-column
    
    html_content += '</div>'  # End year-container
    
    # Add electives section with proper categorization
    html_content += '''
    <div class="electives-section">
        <h2 style="text-align: center; color: #2c3e50; margin-bottom: 20px;">Elective Courses & Requirements</h2>
        <div class="electives-grid">
    '''
    
    # Collect elective courses from student's transcript using proper classification
    elective_courses = {
        "Wellness (7 Credits Required)": [],
        "Entrepreneurship (3 Credits Required)": [],
        "Language & Communication (15 Credits Required)": [],
        "Thai Citizen & Global (2 Credits Required)": [],
        "Aesthetics (3 Credits Required)": [],
        "Technical Electives": [],
        "Free Electives": [],
        "Unidentified Courses": []
    }
    
    unidentified_count = 0
    
    for semester in semesters:
        for course in semester.get("courses", []):
            code = course.get("code", "")
            name = course.get("name", "")
            grade = course.get("grade", "")
            credits = course.get("credits", 0)
            
            # Skip if it's in the core curriculum
            is_core = False
            for year in curriculum_structure:
                for sem in curriculum_structure[year]:
                    if any(c["code"] == code for c in curriculum_structure[year][sem]):
                        is_core = True
                        break
                if is_core:
                    break
            
            if not is_core:
                category, subcategory, is_identified = classify_course_with_proper_detection(code, name, course_categories)[:3]
                
                course_info = {
                    "code": code,
                    "name": name,
                    "grade": grade,
                    "credits": credits,
                    "semester": semester.get("semester", ""),
                    "is_identified": is_identified
                }
                
                if category == "technical_electives":
                    elective_courses["Technical Electives"].append(course_info)
                elif category == "gen_ed":
                    if subcategory == "wellness":
                        elective_courses["Wellness (7 Credits Required)"].append(course_info)
                    elif subcategory == "entrepreneurship":
                        elective_courses["Entrepreneurship (3 Credits Required)"].append(course_info)
                    elif subcategory == "language_communication":
                        elective_courses["Language & Communication (15 Credits Required)"].append(course_info)
                    elif subcategory == "thai_citizen_global":
                        elective_courses["Thai Citizen & Global (2 Credits Required)"].append(course_info)
                    elif subcategory == "aesthetics":
                        elective_courses["Aesthetics (3 Credits Required)"].append(course_info)
                elif category == "unidentified":
                    elective_courses["Unidentified Courses"].append(course_info)
                    unidentified_count += 1
                else:
                    elective_courses["Free Electives"].append(course_info)
    
    # Generate electives HTML with proper category styling
    category_styles = {
        "Wellness (7 Credits Required)": "wellness",
        "Entrepreneurship (3 Credits Required)": "entrepreneurship", 
        "Language & Communication (15 Credits Required)": "language",
        "Thai Citizen & Global (2 Credits Required)": "thai-citizen",
        "Aesthetics (3 Credits Required)": "aesthetics",
        "Technical Electives": "technical",
        "Unidentified Courses": "unidentified"
    }
    
    for category, courses in elective_courses.items():
        if courses or "Required" in category:  # Show categories with courses OR required categories
            style_class = category_styles.get(category, "")
            
            # Calculate credits earned in this category
            earned_credits = sum(c["credits"] for c in courses if c["grade"] not in ["F", "W", "N", ""])
            
            html_content += f'''
            <div class="elective-category">
                <div class="category-header {style_class}">{category}</div>
                <div style="text-align: center; margin-bottom: 10px; font-weight: bold; color: #2c3e50;">
                    Credits Earned: {earned_credits}
                </div>
            '''
            
            if courses:
                for course in courses:
                    css_class = "course-box"
                    if course["grade"] in ["A", "B+", "B", "C+", "C", "D+", "D", "P"]:
                        css_class += " course-completed"
                    elif course["grade"] == "F":
                        css_class += " course-failed"
                    elif course["grade"] == "W":
                        css_class += " course-withdrawn"
                    elif not course.get("is_identified", True):
                        css_class += " course-unidentified"
                    
                    html_content += f'''
                    <div class="{css_class}">
                        <div class="course-code">{course["code"]}</div>
                        <div class="course-name">{course["name"]}</div>
                        <div class="course-info">{course["credits"]} credits • {course["grade"]} • {course["semester"]}</div>
                    </div>
                    '''
            else:
                html_content += '<div style="text-align: center; color: #7f8c8d; font-style: italic;">No courses taken yet</div>'
            
            html_content += '</div>'  # End elective-category
    
    html_content += '</div></div>'  # End electives-grid and electives-section
    
    # Add statistics summary
    total_completed = len([c for c in completed_courses.values()])
    total_credits = sum([c["credits"] for c in completed_courses.values()])
    
    html_content += f'''
    <div class="stats-summary">
        <h3 style="text-align: center; color: #2c3e50;">Progress Summary</h3>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-number">{total_completed}</div>
                <div class="stat-label">Courses Completed</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_credits}</div>
                <div class="stat-label">Credits Earned</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{unidentified_count}</div>
                <div class="stat-label">Unidentified Courses</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len(validation_results)}</div>
                <div class="stat-label">Total Registrations</div>
            </div>
        </div>
    </div>
    '''
    
    html_content += '''
        </div>
    </body>
    </html>
    '''
    
    return html_content, unidentified_count
