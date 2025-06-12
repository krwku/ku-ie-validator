# Course Registration Validation System Setup Guide

This comprehensive guide will help you set up and use the Course Registration Validation System, a tool for managing and validating student course registrations against university prerequisites and rules.

## Table of Contents
1. [System Overview](#system-overview)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Using the Transcript Editor](#using-the-transcript-editor)
5. [Validating Transcripts](#validating-transcripts)
6. [PDF Extraction](#pdf-extraction)
7. [Course Data Management](#course-data-management)
8. [Directory Structure](#directory-structure)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

## System Overview

The Course Registration Validation System is a modular application designed for academic administrators, registrars, and advisors to ensure students are registering for courses in accordance with university requirements.

### Key Features

- **Transcript Management**: Create, edit, and maintain student transcript records
- **PDF Extraction**: Import transcript data from PDF files with intelligent text parsing
- **Prerequisite Validation**: Automatically check if students have completed required prerequisite courses
- **Concurrent Registration Rules**: Handle special cases for concurrent course registration
- **Credit Limit Checks**: Verify semester credit loads against university policies
- **Comprehensive Reporting**: Generate detailed validation reports with clear explanations

### System Architecture

The system uses a modular architecture with separation between data models, business logic, and user interface:

- **Data Layer**: Manages transcript data structures and course information
- **Validation Layer**: Implements the rules for course registration validation
- **UI Layer**: Provides user-friendly interfaces for data management and validation

This separation allows for future extensions while maintaining a stable core system.

## Installation

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Processor**: 1.6 GHz or faster
- **Memory**: 4 GB RAM (8 GB recommended)
- **Disk Space**: 100 MB free space
- **Python**: Version 3.8 or higher
- **Display**: 1280 x 720 resolution or higher

### Prerequisites
- Python 3.8 or higher
- PyPDF2 library (for PDF extraction)
- Tkinter (usually included with Python)

### Installation Options

#### Option 1: Pip Installation (Recommended)
The easiest way to install is directly from the repository:

```bash
pip install git+https://github.com/Modern-research-group/course-registration-validator.git
```

After installation, you can run the application from any directory by typing:
```bash
course-validator
```

#### Option 2: Manual Installation (Windows)
1. Clone the repository:
   ```bash
   git clone https://github.com/Modern-research-group/course-registration-validator.git
   cd course-registration-validator
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python integrated_solution.py
   ```

#### Option 3: Manual Installation (Mac/Linux)
1. Clone the repository:
   ```bash
   git clone https://github.com/Modern-research-group/course-registration-validator.git
   cd course-registration-validator
   ```

2. Install the required dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python3 integrated_solution.py
   ```

### Verifying Installation Success
After running the application, you should see the main launcher window with options for "Launch Transcript Editor" and "Validate Transcript". If this window appears, your installation was successful.

If you encounter any errors, check the [Troubleshooting](#troubleshooting) section.

## Getting Started

### Initial Setup

When you first run the application, you'll see the main launcher window with these options:

1. **Launch Transcript Editor**: Opens the transcript editor interface for creating and editing transcripts
2. **Validate Transcript (JSON)**: Lets you select and validate a saved JSON transcript file
3. **View Reports**: Opens the reports directory to view previously generated validation reports

![Main Launcher Interface](illustration-placeholder)

### Course Data Selection

On first launch, you'll be prompted to select a course data file:

1. A dialog will appear asking you to choose a course data file
2. Navigate to your course_data directory
3. Select the appropriate JSON file (e.g., "industrial-engineering-courses.json")
4. Click "Open" to confirm your selection

The system needs this data to know course prerequisites, credit values, and other information essential for validation.

### Default Directories

The application creates several directories automatically:
- **course_data**: Stores course catalog information
- **logs**: Contains application logs for troubleshooting
- **reports**: Stores validation reports generated by the system

### Creating Your First Transcript

The quickest way to get started is:

1. Click "Launch Transcript Editor" from the main launcher
2. Enter student information in the top-left panel
3. Click "Add Semester" to create a new semester
4. Select the semester and add courses using the "Add Course" button
5. Save your transcript using File > Save As
6. Return to the launcher to validate the transcript

This basic workflow will get you familiar with the main components of the system.

## Using the Transcript Editor

The Transcript Editor is the main interface for creating and editing transcript data. It provides a comprehensive set of tools for managing student records.

### Editor Layout
The editor is divided into several key areas:
- **Left Side**: Student information and semester navigation
- **Right Side**: Current semester details and course management
- **Menu Bar**: Access to file operations, tools, and validation

![Transcript Editor Layout](illustration-placeholder)

### Student Information Panel

The Student Information panel allows you to enter basic student details:

| Field | Description | Example |
|-------|-------------|---------|
| Student ID | University ID number | 6010500045 |
| Name | Student's full name | Mr. Maximus Regisstar |
| Field of Study | Major or program | Industrial Engineering |
| Date of Admission | When student enrolled | Sep 01, 2020 |

**Important**: Click "Apply Changes" after updating information to save it to the transcript.

### Managing Semesters

The Semesters panel on the left manages the student's academic terms:

| Action | Button/Method | Effect |
|--------|---------------|--------|
| Add Semester | "Add Semester" button | Creates a new term (intelligently choosing next logical semester) |
| Select Semester | Click on semester in list | Makes that semester active for editing |
| Edit Semester | "Edit Semester" button | Opens dialog to modify semester properties |
| Delete Semester | "Delete" button | Removes the selected semester after confirmation |
| Reorder Up | "Move Up ↑" button | Moves semester earlier in the sequence |
| Reorder Down | "Move Down ↓" button | Moves semester later in the sequence |

**Tip**: Semesters follow a logical order: First Semester → Second Semester → Summer Session → First Semester (next year)

### Current Semester Details

When a semester is selected, you can edit its details in the Current Semester panel:

1. **Semester Type**: Choose from dropdown (First, Second, or Summer)
2. **Year**: Enter the calendar year (e.g., 2022)
3. **Semester GPA**: Enter the GPA earned in this term
4. **Cumulative GPA**: Enter the overall GPA up to this point
5. **Total Credits**: Automatically calculated based on courses (read-only)

Remember to click "Apply Changes" after making modifications.

### Managing Courses

The Courses panel displays all courses in the current semester:

| Column | Description |
|--------|-------------|
| Course Code | The unique identifier (e.g., 01206221) |
| Course Name | Full name of the course |
| Grade | The grade earned (A, B+, B, C+, C, D+, D, F, W, P, N) |
| Credits | Number of credit hours |

Course management actions:
- **Add Course**: Adds a new course to the current semester
- **Edit Course**: Modifies the selected course
- **Delete Course**: Removes the selected course after confirmation
- **Move Course**: Transfers selected course(s) to a different semester

### Adding/Editing Courses

The course dialog provides a detailed interface for course management:

1. **Course Code**:
   - Enter the course code manually (e.g., 01206221)
   - Use the "Lookup" button to search the course catalog
   - The system will validate against the course database

2. **Course Name**:
   - Enter manually or will auto-populate from course catalog
   - For known courses, this field will fill automatically when code is entered

3. **Grade**:
   - Select from dropdown: A, B+, B, C+, C, D+, D, F, W, P, N
   - W = Withdrawn, P = Pass, N = Not graded yet

4. **Credits**:
   - Enter number of credit hours
   - Will auto-fill for known courses

5. **Course Information**:
   - Displays additional details for courses in the catalog
   - Shows prerequisites and other requirements

**Keyboard Shortcuts**:
- Tab: Move between fields
- Enter: In course code field, performs lookup
- Ctrl+S: Save course (when dialog is open)
- Esc: Cancel and close dialog

### Saving Transcripts

The system offers multiple options for saving your work:

| Action | Menu Path | Shortcut | Description |
|--------|-----------|----------|-------------|
| Save | File > Save | Ctrl+S | Saves to current file (if previously saved) |
| Save As | File > Save As | Ctrl+Shift+S | Saves to a new JSON file |
| New Transcript | File > New Transcript | Ctrl+N | Starts a fresh transcript (prompts to save current) |
| Open JSON | File > Open JSON | Ctrl+O | Opens an existing transcript file |

**File Format**: Transcripts are saved in JSON format, which can be validated or further edited later.

## Validating Transcripts

Validation is the core functionality of the system. It checks if course registrations follow university rules, particularly regarding prerequisites and credit limits.

### Validation Rules

The validator checks for several types of issues:

1. **Prerequisite Requirements**:
   - Has the student passed all required prerequisite courses?
   - If a prerequisite was failed, is concurrent registration valid?
   - Are prerequisite groups (where only one of several courses is required) satisfied?

2. **Credit Limits**:
   - Regular semester: Typically 22 credits maximum
   - Summer session: Typically 9 credits maximum
   - Credit limit violations generate warnings, not errors

3. **Concurrent Registration**:
   - Special rule: Students can take a course concurrently with its prerequisite if they previously failed that prerequisite
   - Withdrawn courses don't qualify for concurrent registration

4. **Chain Validation**:
   - If a prerequisite is invalid, all dependent courses become invalid
   - This creates a cascading effect through the curriculum

### Validation Methods

#### From the Transcript Editor
1. Open a transcript in the editor
2. Navigate to Tools > Validate Transcript
3. If prompted, select or confirm the course data file
4. The validation report will appear in a new window
5. Review the summary and detailed results

#### From the Main Launcher
1. Select "Validate Transcript (JSON)" from the main screen
2. Navigate to and select a JSON transcript file
3. If prompted, select the course data file for validation
4. The validation report will appear automatically
5. You'll be asked if you want to view the detailed report

#### Batch Validation (Advanced)
For validating multiple transcripts:
```bash
python validator.py --batch path/to/transcripts/ --output path/to/reports/
```

### Understanding Validation Reports

The validation report is divided into sections:

#### 1. Header Section
```
================================================================================
COURSE REGISTRATION VALIDATION REPORT
Generated: 2023-03-26 15:42:23
================================================================================
```

#### 2. Student Information
```
STUDENT INFORMATION
--------------------------------------------------------------------------------
Student ID:       6010500045
Name:             Mr. Maximus Regisstar
Field of Study:   Industrial Engineering
Date of Admission: September 1, 2020
Current GPA:      3.45
Academic Status:  NORMAL
```

#### 3. Validation Summary
```
VALIDATION SUMMARY
--------------------------------------------------------------------------------
Semesters Analyzed:    6
Registrations Checked: 42
Invalid Registrations: 3
```

#### 4. Semester Details
```
SEMESTER DETAILS
--------------------------------------------------------------------------------

First 2020
----------
Total Credits: 18
Overall - Semester GPA: 3.45, Cumulative GPA: 3.45

Courses:
Code       Name                                     Grade   Credits  Status
--------------------------------------------------------------------------------
01206221   Applied Probability and Statistics       A       3        Valid
01205201   Introduction to Electrical Engineering   B+      3        Valid
```

#### 5. Invalid Registrations
```
INVALID REGISTRATIONS DETAILS
--------------------------------------------------------------------------------

Semester: Second 2020
  • Course: 01206321 - Operations Research for Engineers I
    Type: Prerequisite
    Reason: Prerequisite 01206221 not satisfied
```

#### 6. Courses Not Found
```
COURSES NOT IN COURSE DATA
--------------------------------------------------------------------------------
The following courses were not found in the course data file and could not be validated.
Please check prerequisites manually for these courses:

Code       Name                                     Semester
----------------------------------------------------------------------
01999999   Special Topics in Engineering            First 2021
```

### Interpreting Common Validation Errors

| Error Message | Interpretation | Solution |
|---------------|----------------|----------|
| "Prerequisite X not satisfied" | Student hasn't passed the required prerequisite | Ensure student completes prerequisite first |
| "Prerequisite X is invalid in current semester" | The prerequisite course itself has validation issues | Fix the prerequisite course issue first |
| "Prerequisite X withdrawn (W) in this semester" | Student withdrew from a prerequisite in same semester | Can't take dependent course in same term |
| "No prerequisite groups are satisfied" | None of the alternative prerequisite options are met | Student must meet at least one option |
| "NOTICE: Exceeds typical X credits..." | Warning about high credit load | Consider reducing course load (warning only) |

### Validation Report Files

Reports are saved automatically to the "reports" directory with filenames based on student ID:
```
reports/validation_report_6010500045.txt
```

These files can be opened in any text editor for review.

## PDF Extraction

The system includes a powerful feature to extract transcript data from PDF files. This can save significant time compared to manual data entry, though some manual correction is typically needed to ensure accuracy.

### PDF Extraction Process

The extraction process works in two phases:
1. **Text Extraction**: Converting the PDF to text using PyPDF2
2. **Data Parsing**: Identifying student information, semesters, courses, and grades

### Supported PDF Format

The extractor works best with PDFs that have:
- Clear text (not scanned images)
- Consistent formatting of course information
- Standard semester headers
- Distinct student information section

### Extraction Steps

1. In the Transcript Editor, navigate to **File > Try Extract from PDF**
2. In the file dialog, select a PDF transcript file
3. If you already have data in the editor, you'll be asked:
   - **Yes**: Replace current transcript with extracted data
   - **No**: Append extracted semesters to current transcript
   - **Cancel**: Cancel the extraction
4. The extraction dialog will open showing the raw extracted text
5. Review the text and make any necessary corrections:
   - Fix any misrecognized course codes
   - Correct improperly formatted semester headings
   - Ensure student information is correctly formatted
6. Click "Process Text" to create transcript data from the text
7. The system will extract:
   - Student ID, name, field of study, and admission date
   - All semesters with their appropriate type and year
   - Courses with codes, names, grades, and credits
   - GPA information for each semester

### Extraction Patterns

The system looks for specific patterns in the text:

| Element | Pattern Example | Notes |
|---------|-----------------|-------|
| Student ID | Student No 6010500045 | Must include "Student No" prefix |
| Name | Name Mr. Maximus Regisstar | Must include "Name" prefix |
| Field of Study | Field of Study Industrial Engineering | Must include "Field of Study" prefix |
| Date | Date of Admission September 1, 2020 | Must include "Date of Admission" prefix |
| Semester | First Semester 2020 | Can be "First", "Second" or "Summer" |
| Course | 01206221 Applied Probability A 3 | Format: Code Name Grade Credits |
| GPA | sem. G.P.A. = 3.45 cum. G.P.A. = 3.50 | Both semester and cumulative GPA |

### Tips for Successful Extraction

1. **Text Quality**: Ensure the PDF contains actual text, not just images
2. **Manual Correction**: Always review the extracted text before processing
3. **Semester Headers**: Check that all semester headers are properly recognized
4. **Course Lines**: Verify that course information is on single lines
5. **Special Characters**: Remove or fix any unusual characters in the extracted text

### Handling Extraction Problems

If extraction fails or produces poor results:
1. Try copying the text directly from your PDF viewer
2. Paste it into the extraction dialog manually
3. Format the text to match expected patterns
4. Process the manually corrected text

### Alternative to PDF Extraction

If PDF extraction isn't working well for your documents, consider:
1. Creating a new transcript manually in the editor
2. Using "File > Save As" to save a template
3. Duplicating this template for similar transcripts in the future

This can be more efficient than struggling with PDF extraction for incompatible documents.

## Course Data Management

Course data is central to the validation system's operation. This section explains how to manage and update the course catalog.

### Course Data Format

Course data is stored in JSON format with the following structure:

```json
{
  "industrial_engineering_courses": [
    {
      "code": "01206221",
      "name": "Applied Probability and Statistics for Engineers",
      "credits": "3(3-0-6)",
      "prerequisites": [
        "01417168"
      ],
      "corequisites": []
    },
    {
      "code": "01206222",
      "name": "Applied Mathematics for Industrial Engineers",
      "credits": "3(3-0-6)",
      "prerequisites": [
        "01417267"
      ],
      "corequisites": []
    }
  ]
}
```

Key elements:
- **code**: Unique course identifier
- **name**: Full course name
- **credits**: Total credits, often with lecture-lab-self study hours in parentheses
- **prerequisites**: Array of course codes that must be completed before taking this course
- **corequisites**: Array of course codes that must be taken concurrently
- **prerequisite_groups**: (Advanced) Groups of alternatives where any one course satisfies the requirement

### Adding New Course Data Files

To add a new course data file:

1. In the Transcript Editor, go to **File > Select Course Data**
2. In the dialog that appears, click **Add New File**
3. Browse to and select your JSON course data file
4. The file will be copied to the course_data directory
5. Select the file from the list and click **Select**

### Creating Course Data Files

To create a new course data file:

1. Start with the template structure shown above
2. Add each course as an entry in the "industrial_engineering_courses" array
3. Ensure each course has a unique code
4. Save the file with a descriptive name, e.g., "mechanical-engineering-courses.json"

### Advanced: Prerequisite Groups

For complex prerequisites (where students need to complete one course from a set of options), use prerequisite_groups:

```json
{
  "code": "01403114",
  "name": "Laboratory in Fundamentals of General Chemistry",
  "credits": "1(0-3-2)",
  "prerequisites": [],
  "corequisites": [],
  "prerequisite_groups": [
    {
      "courses": ["01403117"],
      "concurrent_allowed": true
    }
  ]
}
```

This structure indicates that course 01403117 can be taken concurrently with this lab course.

### Default Course Data Location

Course data files are stored in the course_data directory within the application folder. When selecting course data, you'll see all available files in this directory.

## Directory Structure

The system uses a well-organized directory structure:

```
course-registration-validator/
├── course_data/          # Course data files (JSON)
│   └── industrial-engineering-courses.json
├── data/                 # Data management modules
│   ├── course_manager.py   # Course operations
│   ├── semester_manager.py # Semester operations
│   ├── student_manager.py  # Student info operations
│   └── transcript_model.py # Core data model
├── logs/                 # Application logs
│   └── transcript_editor_YYYYMMDD-HHMMSS.log
├── reports/              # Validation reports
│   └── validation_report_STUDENTID.txt
├── ui/                   # User interface components
│   ├── course_lookup.py    # Course catalog dialog
│   ├── dialogs.py          # Common dialogs
│   ├── pdf_extraction_dialog.py # PDF extraction UI
│   └── validation_report.py     # Report display
├── utils/                # Utility modules
│   ├── config.py           # Application configuration
│   ├── file_operations.py  # File I/O operations
│   ├── logger_setup.py     # Logging configuration
│   ├── pdf_extractor.py    # PDF extraction logic
│   └── validation_adapter.py # Validation interface
├── app.py                # Main application module
├── integrated_solution.py  # Integrated launcher
├── transcript_editor_app.py  # Transcript editor entry point
└── validator.py          # Core validation logic
```

### File Descriptions

| File/Directory | Purpose |
|----------------|---------|
| course_data/ | Contains JSON files with course information |
| data/ | Data management modules for core functionality |
| logs/ | Timestamped log files for troubleshooting |
| reports/ | Validation reports generated by the system |
| ui/ | User interface components and dialogs |
| utils/ | Utility functions and helpers |
| app.py | Main transcript editor application |
| integrated_solution.py | Launcher for accessing all components |
| transcript_editor_app.py | Entry point for transcript editor |
| validator.py | Core validation logic and rules implementation |

### Important Paths

The system automatically manages several paths:
- **App Directory**: The location where the application is installed
- **Course Data Directory**: `app_dir/course_data/`
- **Reports Directory**: `app_dir/reports/`
- **Logs Directory**: `app_dir/logs/`

These directories are created automatically if they don't exist.

## Troubleshooting

This section covers common issues you might encounter and their solutions.

### Application Launch Issues

| Problem | Possible Cause | Solution |
|---------|----------------|----------|
| Application doesn't start | Python version too old | Install Python 3.8 or higher |
| | Missing PyPDF2 | Run `pip install PyPDF2` |
| | Tkinter not installed | Install tkinter package for your OS |
| `ModuleNotFoundError` | Missing dependency | Install requirements with `pip install -r requirements.txt` |
| | Incorrect Python path | Ensure you're using the correct Python interpreter |
| Permission error | Insufficient privileges | Run as administrator (Windows) or use sudo (Linux) |
| Blank window appears | Display scaling issue | Try setting Windows display scaling to 100% |

### PDF Extraction Issues

| Problem | Possible Cause | Solution |
|---------|----------------|----------|
| No text extracted | PDF contains images, not text | Use a PDF with actual text content |
| | PDF has security restrictions | Use an unrestricted PDF file |
| Incorrect extraction | PDF format not recognized | Manually correct the extracted text |
| | Unusual formatting | Edit text to match expected patterns |
| Student info not found | Different labeling convention | Ensure labels match patterns (e.g., "Student No") |
| Semesters not detected | Header format different | Format headers as "First/Second/Summer Semester YYYY" |
| Courses not parsed | Different data format | Ensure course format matches expected pattern |

### Validation Issues

| Problem | Possible Cause | Solution |
|---------|----------------|----------|
| All courses show as valid despite issues | Incorrect course data file | Select the correct course data file |
| | Course codes don't match | Ensure transcript course codes match course data |
| Incorrect prerequisite validation | Missing prerequisite in course data | Update course data file with correct prerequisites |
| | Course data not properly formatted | Check JSON format of course data file |
| GPA calculation errors | Invalid grade formats | Use standard grades (A, B+, B, etc.) |
| | Missing credits | Ensure all courses have credit values |
| "Course not found" errors | Course missing from catalog | Add course to course data file |
| | Typographical error in course code | Correct course code in transcript |

### File Operation Issues

| Problem | Possible Cause | Solution |
|---------|----------------|----------|
| Cannot save transcript | Permission issue | Check folder permissions |
| | Invalid file path | Choose a different save location |
| Cannot open JSON file | Corrupted file | Restore from backup or create new transcript |
| | Invalid JSON format | Ensure file is properly formatted JSON |
| Reports not generating | Reports directory missing | Create 'reports' directory manually |
| | Permission issue | Check write permissions for reports directory |

### Course Data Issues

| Problem | Possible Cause | Solution |
|---------|----------------|----------|
| Course data not loading | File not found | Place JSON file in course_data directory |
| | Invalid JSON format | Check for syntax errors in the file |
| | Missing required fields | Ensure all courses have the required fields |
| Cannot find course in lookup | Course missing from data | Add course to course data file |
| | Course data file not selected | Select correct course data file |
| Prerequisites not recognized | Different course code format | Ensure consistent course code format |
| | Missing prerequisite in data | Add missing courses to course data |

### Logging and Diagnostics

To troubleshoot more complex issues:

1. **Check log files**: Look in the logs directory for detailed error messages
   - Log files are named `transcript_editor_YYYYMMDD-HHMMSS.log`
   - Most recent log file will have the latest timestamp

2. **Enable debug logging**: Set more detailed logging by editing logger_setup.py
   - Change `level=logging.INFO` to `level=logging.DEBUG`
   - Restart the application

3. **Console output**: If running from command line, check console for error messages

4. **Verify configuration**: Check config.py to ensure paths are correctly set

### Common Error Messages

| Error Message | Meaning | Solution |
|---------------|---------|----------|
| "Failed to load course data" | Course data file missing or invalid | Check course data file path and format |
| "Validator not initialized" | Validation system not properly set up | Select course data file first |
| "Error extracting text from PDF" | PDF extraction failed | Use a different PDF or extract text manually |
| "Failed to save transcript data" | Save operation failed | Check file permissions and path |
| "No text extracted from PDF" | PDF does not contain extractable text | Use a different PDF or enter data manually |
