import json
from pathlib import Path

def load_comprehensive_course_data():
    """Load all course data including Gen-Ed and Technical Electives"""
    course_data_dir = Path(__file__).parent.parent / "course_data"
    
    # Try to load from existing files
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
                    display_name = file_name.replace("_", " ").title()
                
                available_files[display_name] = {
                    'data': data,
                    'filename': json_file.name,
                    'path': str(json_file)
                }
            except Exception as e:
                print(f"Error loading {json_file.name}: {e}")
    
    return available_files
