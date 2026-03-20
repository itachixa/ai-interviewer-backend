from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from services.ai_service import generate_questions, evaluate_answer, final_evaluation
from services.pdf_parser import extract_text

app = FastAPI()

# 🔥 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📄 Upload CV
@app.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    try:
        with open("temp.pdf", "wb") as f:
            f.write(await file.read())

        text = extract_text("temp.pdf")

        return {"cv_text": text}

    except Exception as e:
        return {"error": str(e)}


# 🎯 Questions
@app.post("/questions")
def questions(data: dict):
    return {
        "questions": generate_questions(data["cv_text"])
    }


# 📊 Evaluate
@app.post("/evaluate")
def evaluate(data: dict):
    return evaluate_answer(data["answer"])


# 🧠 Final
@app.post("/final")
def final(data: dict):
    return {
        "result": final_evaluation(data["answers"])
    }