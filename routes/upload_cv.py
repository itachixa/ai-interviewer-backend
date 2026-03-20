from fastapi import APIRouter, UploadFile, File
from services.pdf_parser import extract_text_from_pdf

router = APIRouter()

@router.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    try:
        text = extract_text_from_pdf(file.file)
        return {"cv_text": text}
    except Exception as e:
        return {"error": f"❌ Error uploading CV: {str(e)}"}