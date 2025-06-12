import json
from pathlib import Path

def classify_course_with_year_placement(course_code, course_name=""):
    """
    Classify course and determine its recommended year/semester placement.
    Returns: (category, subcategory, is_identified, year, semester)
    """
    code = course_code.upper()
    
    # Year 1 courses
    year1_first = ["01417167", "01420111", "01420113", "01403117", "01403114", "01208111"]
    year1_second = ["01417168", "01420112", "01420114", "01208281", "01204111"]
    
    # Year 2 courses  
    year2_first = ["01417267", "01208221", "01208241", "01213211", "01205201"]
    year2_second = ["01206221", "01206251", "01205202", "01208381"]
    
    # Year 3 courses
    year3_first = ["01206222", "01206223", "01206272", "01206311", "01206321"]
    year3_second = ["01206312", "01206322", "01206323", "01206341", "01206361"]
    
    # Year 4 courses
    year4_first = ["01206342", "01206371", "01206381", "01206452"]
    year4_second = ["01206343", "01206382", "01206495", "01206497", "01206499"]
    
    # Determine placement
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
    
    # Technical electives (flexible placement)
    technical_patterns = [
        "01206411", "01206412", "01206413", "01206414", "01206421", "01206422",
        "01206423", "01206424", "01206431", "01206432", "01206441", "01206442",
        "01206443", "01206444", "01206445", "01206446", "01206461", "01206462",
        "01206463", "01206464", "01206465", "01206490"
    ]
    if code in technical_patterns:
        return ("technical_electives", "technical", True, None, None)
    
    # Gen-Ed courses (flexible placement)
    if code.startswith("01175") or code in ["01101102", "01173151"]:
        return ("gen_ed", "wellness", True, None, None)
    elif code.startswith("01355") or code.startswith("01361"):
        return ("gen_ed", "language", True, None, None)
    elif code in ["01418104", "01418111"]:
        return ("gen_ed", "language", True, None, None)
    
    # Unidentified
    return ("unidentified", "unknown", False, None, None)

def create_semester_flow_html(student_info, semesters, validation_results, course_data=None):
    """
    Create an HTML visualization that replicates the semester-based flow chart.
    """
    
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
    
    # Generate CSS styles
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
            background: linear-gradient(45deg, #16a085, #1abc9c);
            color: white;
            border-radius: 5px;
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
                    
                    html_content += f'''
                    <div class="{css_class}">
                        <div class="course-code">{code}</div>
                        <div class="course-name">{name}</div>
                        <div class="course-info">{credits} credits • {status_info}</div>
                    </div>
                    '''
            
            html_content += '</div>'  # End semester-section
        
        html_content += '</div>'  # End year-column
    
    html_content += '</div>'  # End year-container
    
    # Add electives section
    html_content += '''
    <div class="electives-section">
        <h2 style="text-align: center; color: #2c3e50; margin-bottom: 20px;">Elective Courses</h2>
        <div class="electives-grid">
    '''
    
    # Collect elective courses from student's transcript
    elective_courses = {
        "Technical Electives": [],
        "Gen-Ed Courses": [],
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
                category, subcategory, is_identified = classify_course_with_year_placement(code, name)[:3]
                
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
                    elective_courses["Gen-Ed Courses"].append(course_info)
                elif category == "unidentified":
                    elective_courses["Unidentified Courses"].append(course_info)
                    unidentified_count += 1
                else:
                    elective_courses["Free Electives"].append(course_info)
    
    # Generate electives HTML
    for category, courses in elective_courses.items():
        if courses:  # Only show categories with courses
            html_content += f'''
            <div class="elective-category">
                <div class="category-header">{category}</div>
            '''
            
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
