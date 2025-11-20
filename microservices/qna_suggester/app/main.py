from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from app.query_huggingface import generate_interview_questions
import json, hashlib

# ✔ Protobuf is handled inside redis_cache.py using qna_topic.proto

from app.redis_cache import (
    async_cache_get_qna_topics,
    async_cache_set_qna_topics,
)







app = FastAPI(
    title="Interview QnA Microservice",
    description="Generates interview questions using a local Hugging Face model.",
    version="2.0"
)

# ----------------------------
# ✅ Pydantic Models for Input
# ----------------------------
class ResumeData(BaseModel):
    skills: List[str]

class JDData(BaseModel):
    keywords: List[str]

class SuggestionRequest(BaseModel):
    resume: ResumeData
    jd: JDData
    suggestions: Optional[bool] = False


## ----------------------------
# ✅ POST Endpoint (FINAL VERSION)
# ----------------------------
@app.post("/suggest")
async def suggest_questions(request_data: SuggestionRequest):
    """
    Generate interview questions using skills + JD.
    ✔ Checks Redis first (dynamic caching)
    ✔ Loads Protobuf → JSON if found
    ✔ If not found → generates → stores → returns
    ✔ Output JSON stays EXACTLY same as old API
    """

    resume_skills = request_data.resume.skills
    jd_keywords = request_data.jd.keywords
    include_suggestions = request_data.suggestions

    # -------------------------------------------------
    # 1️⃣ Create a stable Redis key from request data
    # -------------------------------------------------
    raw_key = json.dumps(
        {
            "resume": resume_skills,
            "jd": jd_keywords,
            "suggestions": include_suggestions,
        },
        sort_keys=True,
    )
    cache_key = "qna:" + hashlib.sha256(raw_key.encode()).hexdigest()

    # -------------------------------------------------
    # 2️⃣ Try to load from Redis (cached result)
    # -------------------------------------------------
    cached = await async_cache_get_qna_topics(cache_key)
    if cached:
        # cached = { "topics": {topic: {...}}, "suggestions": [...] }
        questions_out = {
            topic: details.get("merged", [])
            for topic, details in cached["topics"].items()
        }

        response = {
            "status": "success",
            "questions": questions_out,
            "cached": True
        }

        if cached["suggestions"]:
            response["general_tips"] = cached["suggestions"]

        return response

    # -------------------------------------------------
    # 3️⃣ Cache MISS → Generate new questions
    # -------------------------------------------------
    result = generate_interview_questions(
        resume_skills,
        jd_keywords,
        include_suggestions,
    )
    # result = { "status": "success", "questions": {...}, "general_tips": [...] }

    raw_questions = result.get("questions", {})
    general_tips = result.get("general_tips", []) or []

    # -------------------------------------------------
    # 4️⃣ Normalize → Protobuf structure
    # -------------------------------------------------
    normalized = {}
    for topic, qlist in raw_questions.items():
        normalized[topic] = {
            "static_questions": qlist,   # treat all as static
            "ai_questions": [],          # no split yet
            "merged": qlist,             # merged = same list
        }

    # -------------------------------------------------
    # 5️⃣ Save to Redis (Protobuf)
    # -------------------------------------------------
    await async_cache_set_qna_topics(
        cache_key,
        questions_by_topic=normalized,
        general_tips=general_tips,
    )

    # -------------------------------------------------
    # 6️⃣ Return SAME JSON format (AWS safe)
    # -------------------------------------------------
    return {
        "status": "success",
        "questions": raw_questions,
        "general_tips": general_tips,
        "cached": False,
    }



# ----------------------------
# ✅ Root Endpoint
# ----------------------------
@app.get("/")
async def root():
    return {
        "message": "Interview QnA Generator is running.",
        "status": "ready",
        "usage": "POST /suggest with resume.skills and jd.keywords"
    }
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

from app.redis_routes import router as redis_router


app.include_router(redis_router, prefix="/cache")

