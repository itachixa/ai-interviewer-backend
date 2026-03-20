from fastapi import APIRouter, UploadFile, File
from openai import OpenAI

client = OpenAI(api_key="YOUR_API_KEY")
router = APIRouter()

@router.post("/speech-to-text")
async def speech(file: UploadFile = File(...)):
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=file.file
    )
    return {"text": transcript.text}