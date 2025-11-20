# app/api/v1/qna.py
from fastapi import APIRouter
import httpx, os

router = APIRouter()
QNA_SUGGESTER_URL = os.getenv("QNA_SUGGESTER_URL", "http://qna-suggester:8003/suggest")

@router.post("/suggest")
async def suggest_questions(payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(QNA_SUGGESTER_URL, json=payload)
        return response.json()
