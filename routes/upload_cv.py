from fastapi import APIRouter, UploadFile, File, HTTPException
from services.pdf_parser import extract_text_from_pdf_file
import tempfile
import os

router = APIRouter()

@router.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    """
    Upload and parse a CV PDF file.
    """
    temp_file_path = None
    
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported. Please upload a PDF."
            )
        
        # Validate file size (max 10MB)
        MAX_FILE_SIZE = 10 * 1024 * 1024
        
        # Save to temporary file
        temp_dir = tempfile.gettempdir()
        fd, temp_file_path = tempfile.mkstemp(suffix='.pdf', dir=temp_dir)
        
        try:
            # Write uploaded file to temp location with size check
            with os.fdopen(fd, 'wb') as f:
                total_size = 0
                chunk_size = 8192
                
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    
                    total_size += len(chunk)
                    if total_size > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=400,
                            detail=f"File too large. Maximum size is {MAX_FILE_SIZE/(1024*1024)}MB"
                        )
                    f.write(chunk)
            
            # Extract text from PDF
            with open(temp_file_path, 'rb') as f:
                cv_text = extract_text_from_pdf_file(f)
            
            if not cv_text or not cv_text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract text from PDF. The file may be empty or scanned."
                )
            
            return {
                "cv_text": cv_text,
                "success": True,
                "message": "CV uploaded and processed successfully"
            }
            
        finally:
            # Always clean up temp file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CV: {str(e)}")