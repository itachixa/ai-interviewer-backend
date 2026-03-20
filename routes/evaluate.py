from fastapi import APIRouter
from services.ai_service import evaluate_answer

router = APIRouter()

@router.post("/evaluate")
def eval(data: dict):
    return {"result": evaluate_answer(data["answer"])}