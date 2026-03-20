from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.question_generator import get_question_generator
from services.pdf_parser import extract_text_from_pdf

router = APIRouter(prefix="/api/questions", tags=["Questions d'entretien"])


class GenerateQuestionsRequest(BaseModel):
    """Modele de requete pour la generation de questions"""
    cv_text: str
    level: Optional[str] = "medium"  # junior, medium, senior
    max_questions: Optional[int] = 10


class GenerateQuestionsResponse(BaseModel):
    """Modele de response pour les questions generatees"""
    questions: List[str]
    count: int
    level: str


@router.post("/generate", response_model=GenerateQuestionsResponse)
async def generate_questions(request: GenerateQuestionsRequest):
    """
    Genere des questions d'entretien a partir d'un texte de CV
    
    Args:
        request: Contient le texte du CV, le niveau et le nombre de questions
    
    Returns:
        Liste des questions d'entretien generatees
    """
    try:
        # Verifier que le texte n'est pas vide
        if not request.cv_text or len(request.cv_text.strip()) < 50:
            raise HTTPException(
                status_code=400, 
                detail="Le texte du CV est trop court ou vide"
            )
        
        # Recuperer le generateur
        generator = get_question_generator()
        
        # Generer les questions
        questions = generator.generate(
            cv_text=request.cv_text,
            max_questions=request.max_questions
        )
        
        return GenerateQuestionsResponse(
            questions=questions,
            count=len(questions),
            level=request.level
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la generation: {str(e)}")


@router.post("/generate-from-file")
async def generate_questions_from_file(
    file: UploadFile = File(...),
    level: str = "medium",
    max_questions: int = 10
):
    """
    Genere des questions d'entretien a partir d'un fichier CV (PDF ou texte)
    
    Args:
        file: Fichier PDF ou texte du CV
        level: Niveau du poste (junior, medium, senior)
        max_questions: Nombre maximum de questions
    
    Returns:
        Liste des questions d'entretien generatees
    """
    try:
        # Verifier le type de fichier
        if file.content_type not in ["application/pdf", "text/plain"]:
            raise HTTPException(
                status_code=400,
                detail="Seuls les fichiers PDF et texte sont acceptés"
            )
        
        # Extraire le texte du fichier
        if file.content_type == "application/pdf":
            content = await file.read()
            cv_text = extract_text_from_pdf(content)
        else:
            cv_text = await file.read()
            cv_text = cv_text.decode("utf-8")
        
        # Generer les questions
        generator = get_question_generator()
        questions = generator.generate(cv_text, max_questions)
        
        return GenerateQuestionsResponse(
            questions=questions,
            count=len(questions),
            level=level
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
