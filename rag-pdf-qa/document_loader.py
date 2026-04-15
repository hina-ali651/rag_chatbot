import os
import pdfplumber
import docx

def load_document(file_path: str) -> str:
    """
    Loads a document based on its extension and extracts the textual content.
    Supported file formats: .txt, .pdf, .docx
    
    Args:
        file_path (str): The absolute or relative path to the file.
        
    Returns:
        str: Extracted text from the document.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    # 1. Handle Plain Text Files
    if ext == '.txt':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Failed to read TXT: {e}")
    
    # 2. Handle PDF Files
    elif ext == '.pdf':
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        except Exception as e:
            raise Exception(f"Failed to read PDF: {e}")
        
        if not text.strip():
            raise Exception("PDF appears to be empty or contains invisible text (e.g., scanned images).")
            
        return text
        
    # 3. Handle Word Documents
    elif ext == '.docx':
        try:
            doc = docx.Document(file_path)
            # Combine all paragraphs with a newline
            text = "\n".join([para.text for para in doc.paragraphs])
            if not text.strip():
                 raise Exception("DOCX file appears to be empty.")
            return text
        except Exception as e:
            raise Exception(f"Failed to read DOCX: {e}")
            
    # File format is not supported
    else:
        raise ValueError(f"Unsupported file format: '{ext}'. Only .txt, .pdf, and .docx are supported.")
