from fastapi import APIRouter
from services.ai_service import generate_questions

router = APIRouter()

@router.post("/questions")
def questions(data: dict):
    return {
        "questions": generate_questions(
            data["cv_text"],
            data.get("level", "easy"),
            data.get("role", "HR")
        )
    }