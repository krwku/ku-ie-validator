import io
import PyPDF2

def extract_text_from_pdf_bytes(pdf_bytes):
    """
    Extract text from PDF bytes using PyPDF2.
    FIXED: Properly handles BytesIO object.
    """
    try:
        # Create BytesIO object from bytes
        pdf_file = io.BytesIO(pdf_bytes)
        
        # Pass the BytesIO object to PdfReader (NOT the raw bytes)
        reader = PyPDF2.PdfReader(pdf_file)  # FIXED: was pdf_bytes, now pdf_file
        
        all_text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text and page_text.strip():
                all_text.append(page_text)
        
        return "\n".join(all_text)
    
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {e}")
