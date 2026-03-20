import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from services.ai_service import generate_questions, evaluate_answer, final_evaluation
from services.pdf_parser import extract_text_from_pdf_file, cleanup_temp_file, MAX_FILE_SIZE
from routes.generate_questions import router as questions_router

app = FastAPI(title="AI Interviewer API", version="2.0.0")

# Include routers
app.include_router(questions_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "AI Interviewer API is running",
        "version": "2.0.0"
    }


@app.get("/health")
def health_check():
    """Health check for monitoring"""
    return {"status": "healthy"}


@app.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    """
    Upload and parse a CV PDF file.
    
    - **file**: PDF file to upload (max 10MB, 100 pages)
    
    Returns:
        - cv_text: Extracted text from the CV
    """
    temp_file_path = None
    
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported. Please upload a PDF."
            )
        
        # Validate content type
        if file.content_type and 'pdf' not in file.content_type.lower():
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only PDF files are accepted."
            )
        
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
                        cleanup_temp_file(temp_file_path)
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
            cleanup_temp_file(temp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if temp_file_path:
            cleanup_temp_file(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error processing CV: {str(e)}")


@app.post("/questions")
def questions(data: dict):
    """
    Generate interview questions based on CV and job level.
    
    - **cv_text**: Extracted text from the CV
    - **level**: Job level (junior, intermediate, senior, lead, manager)
    - **role**: The role being interviewed for
    
    Returns:
        - questions: List of 7 generated questions
    """
    cv_text = data.get("cv_text")
    level = data.get("level", "intermediate")
    role = data.get("role", "general")
    
    if not cv_text:
        raise HTTPException(status_code=400, detail="cv_text is required")
    
    if not cv_text.strip():
        raise HTTPException(status_code=400, detail="CV text is empty")
    
    questions = generate_questions(cv_text, level, role)
    
    return {
        "questions": questions,
        "count": len(questions),
        "level": level,
        "role": role
    }


@app.post("/evaluate")
def evaluate(data: dict):
    """
    Evaluate a single interview answer.
    
    - **answer**: The candidate's answer
    - **question**: The question that was asked (optional)
    
    Returns:
        - score: Overall score (0-100)
        - fluency: Fluency/clarity score
        - confidence: Confidence score
        - correctness: Relevance/accuracy score
        - feedback: Text feedback
        - suggestions: Suggestions for improvement
    """
    answer = data.get("answer")
    question = data.get("question", "")
    
    if not answer:
        raise HTTPException(status_code=400, detail="answer is required")
    
    result = evaluate_answer(answer, question)
    
    return {
        **result,
        "success": True
    }


@app.post("/final")
def final(data: dict):
    """
    Generate final evaluation report.
    
    - **answers**: List of all candidate answers
    - **questions**: Optional list of questions asked
    
    Returns:
        - overall_score: Final score (0-100)
        - average_scores: Sub-scores (fluency, confidence, correctness)
        - strengths: List of strengths
        - areas_for_improvement: List of areas to improve
        - recommendations: List of recommendations
        - detailed_report: Formatted report text
    """
    answers = data.get("answers", [])
    questions = data.get("questions", [])
    
    if not answers:
        raise HTTPException(status_code=400, detail="answers is required")
    
    result = final_evaluation(answers, questions)
    
    return {
        **result,
        "success": True
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
