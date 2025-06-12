import json
from pathlib import Path

def load_comprehensive_course_data():
    """Load all course data including Gen-Ed and Technical Electives with improved error handling."""
    course_data_dir = Path(__file__).parent.parent / "course_data"
    
    # Try to load from existing files
    available_files = {}
    
    if course_data_dir.exists():
        # Priority order for course files
        course_files = [
            ("B-IE-2565.json", "Industrial Engineering 2565 (2022-2026)"),
            ("B-IE-2560.json", "Industrial Engineering 2560 (2017-2021)"),
            ("ie_core_courses.json", "IE Core Courses"),
            ("gen_ed_courses.json", "General Education Courses"),
            ("technical_electives.json", "Technical Electives")
        ]
        
        for filename, display_name in course_files:
            json_file = course_data_dir / filename
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Validate that the file contains course data
                    has_courses = (
                        'industrial_engineering_courses' in data or
                        'gen_ed_courses' in data or
                        'technical_electives' in data or
                        'other_related_courses' in data
                    )
                    
                    if has_courses:
                        available_files[display_name] = {
                            'data': data,
                            'filename': filename,
                            'path': str(json_file)
                        }
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
                    continue
        
        # Also scan for any other JSON files
        for json_file in course_data_dir.glob("*.json"):
            if json_file.name not in [f[0] for f in course_files]:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Create display name from filename
                    file_name = json_file.stem
                    if "2560" in file_name:
                        display_name = "Course Data 2560 (Legacy)"
                    elif "2565" in file_name:
                        display_name = "Course Data 2565 (Current)"
                    else:
                        display_name = file_name.replace("_", " ").title()
                    
                    # Check if it's not already added
                    if display_name not in available_files:
                        available_files[display_name] = {
                            'data': data,
                            'filename': json_file.name,
                            'path': str(json_file)
                        }
                except Exception as e:
                    print(f"Error loading {json_file.name}: {e}")
    
    return available_files

def validate_course_data_structure(data):
    """Validate the structure of course data."""
    required_fields = ['code', 'name', 'credits']
    
    # Check industrial engineering courses
    if 'industrial_engineering_courses' in data:
        for course in data['industrial_engineering_courses']:
            for field in required_fields:
                if field not in course:
                    return False, f"Missing field '{field}' in industrial engineering course"
    
    # Check general education courses
    if 'gen_ed_courses' in data:
        for category, courses in data['gen_ed_courses'].items():
            for course in courses:
                for field in required_fields:
                    if field not in course:
                        return False, f"Missing field '{field}' in gen-ed course"
    
    # Check technical electives
    if 'technical_electives' in data:
        for course in data['technical_electives']:
            for field in required_fields:
                if field not in course:
                    return False, f"Missing field '{field}' in technical elective"
    
    return True, "Valid structure"

def get_course_statistics(data):
    """Get statistics about the course data."""
    stats = {
        'ie_courses': 0,
        'gen_ed_courses': 0,
        'technical_electives': 0,
        'other_courses': 0,
        'total_courses': 0
    }
    
    if 'industrial_engineering_courses' in data:
        stats['ie_courses'] = len(data['industrial_engineering_courses'])
    
    if 'gen_ed_courses' in data:
        for category, courses in data['gen_ed_courses'].items():
            stats['gen_ed_courses'] += len(courses)
    
    if 'technical_electives' in data:
        stats['technical_electives'] = len(data['technical_electives'])
    
    if 'other_related_courses' in data:
        stats['other_courses'] = len(data['other_related_courses'])
    
    stats['total_courses'] = sum([
        stats['ie_courses'],
        stats['gen_ed_courses'], 
        stats['technical_electives'],
        stats['other_courses']
    ])
    
    return stats

def create_unified_course_lookup(data):
    """Create a unified lookup dictionary from course data."""
    lookup = {}
    
    # Add IE courses
    if 'industrial_engineering_courses' in data:
        for course in data['industrial_engineering_courses']:
            lookup[course['code']] = {
                **course,
                'category': 'ie_core',
                'subcategory': 'core'
            }
    
    # Add other related courses
    if 'other_related_courses' in data:
        for course in data['other_related_courses']:
            lookup[course['code']] = {
                **course,
                'category': 'ie_core',
                'subcategory': 'foundation'
            }
    
    # Add Gen-Ed courses
    if 'gen_ed_courses' in data:
        for subcategory, courses in data['gen_ed_courses'].items():
            for course in courses:
                lookup[course['code']] = {
                    **course,
                    'category': 'gen_ed',
                    'subcategory': subcategory
                }
    
    # Add Technical Electives
    if 'technical_electives' in data:
        for course in data['technical_electives']:
            lookup[course['code']] = {
                **course,
                'category': 'technical_electives',
                'subcategory': 'technical'
            }
    
    return lookup
