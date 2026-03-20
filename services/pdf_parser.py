import os
import tempfile
from PyPDF2 import PdfReader
from typing import BinaryIO

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


def extract_text_from_pdf_file(file: BinaryIO, max_pages: int = 100) -> str:
    """
    Extract text from a PDF file object.
    
    Args:
        file: File object (BytesIO or uploaded file)
        max_pages: Maximum number of pages to process (default 100)
    
    Returns:
        Extracted text as string
    """
    try:
        pdf = PdfReader(file)
        
        # Check page count
        num_pages = len(pdf.pages)
        if num_pages > max_pages:
            raise ValueError(f"PDF too long: {num_pages} pages (max {max_pages})")
        
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        # Clean up extracted text
        text = clean_text(text)
        
        if not text.strip():
            raise ValueError("No text could be extracted from PDF")
        
        return text
        
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error reading PDF: {str(e)}")


def clean_text(text: str) -> str:
    """Clean and normalize extracted text"""
    # Remove excessive whitespace
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove excessive spaces
        line = ' '.join(line.split())
        if line.strip():
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def extract_text(pdf_path: str) -> str:
    """Extract text from a PDF file path (used by main.py)"""
    try:
        # Check file size
        file_size = os.path.getsize(pdf_path)
        if file_size > MAX_FILE_SIZE:
            return f"Error: File too large ({file_size / (1024*1024):.1f}MB). Maximum size is {MAX_FILE_SIZE/(1024*1024)}MB"
        
        pdf = PdfReader(pdf_path)
        
        if len(pdf.pages) > 100:
            return f"Error: Too many pages ({len(pdf.pages)}). Maximum is 100"
        
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        return clean_text(text)
        
    except Exception as e:
        return f"Error extracting text: {str(e)}"


def save_uploaded_file(uploaded_file: BinaryIO, temp_dir: str = None) -> str:
    """
    Save uploaded file to a temporary location securely.
    
    Args:
        uploaded_file: The uploaded file object
        temp_dir: Optional temp directory path
    
    Returns:
        Path to the saved temporary file
    """
    if temp_dir is None:
        temp_dir = tempfile.gettempdir()
    
    # Create secure temp file path
    fd, temp_path = tempfile.mkstemp(suffix='.pdf', dir=temp_dir)
    
    try:
        # Write file content
        with os.fdopen(fd, 'wb') as f:
            # Read in chunks to handle large files
            chunk_size = 8192
            total_size = 0
            
            while True:
                chunk = uploaded_file.read(chunk_size)
                if not chunk:
                    break
                
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    os.unlink(temp_path)
                    raise ValueError(f"File too large. Maximum size is {MAX_FILE_SIZE/(1024*1024)}MB")
                
                f.write(chunk)
        
        return temp_path
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def cleanup_temp_file(file_path: str) -> None:
    """
    Securely delete a temporary file.
    
    Args:
        file_path: Path to file to delete
    """
    try:
        if file_path and os.path.exists(file_path):
            # Overwrite with zeros before deleting for security
            file_size = os.path.getsize(file_path)
            with open(file_path, 'wb') as f:
                f.write(b'\x00' * min(file_size, 1024))  # Overwrite first 1KB
            os.unlink(file_path)
    except Exception:
        # Best effort - file might not exist or be locked
        pass
