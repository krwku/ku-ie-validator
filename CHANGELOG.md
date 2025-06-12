# Changelog

All notable changes to this project will be documented in this file.

## [0.2.3] - 2025-05-29

### Fixed
- **Improved PDF text extraction**: Enhanced PDF extractor with more robust regex patterns to handle PyPDF2 spacing issues
- **Better course parsing**: Added flexible patterns to handle missing spaces in extracted text
- **Enhanced semester detection**: More reliable semester header recognition
- **Added debug logging**: Better error reporting for PDF extraction failures

### Technical Details
- Updated `extract_semesters()` method in `pdf_extractor.py`
- Added text preprocessing to fix common PyPDF2 formatting issues
- Implemented multiple fallback patterns for course and semester parsing
- Improved error handling and debug output

## [0.2.0] - Previous Release

### Added
- Initial PDF extraction functionality
- Transcript editor interface
- Course validation system
- Batch processing capabilities
