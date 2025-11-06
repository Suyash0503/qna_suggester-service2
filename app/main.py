from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.gateway import gateway
import httpx
import os
import redis
import json
import logging

# RESUME_PARSER_URL = "http://resume_parser:8001/parse"
# ATS_MICROSERVICE_URL = "http://ats_scoring:8000/score"
# JOB_MATCHER_URL = "http://job_matcher:8002/match"
# QNA_SUGGESTER_URL = "http://qna_suggester:8003/suggest"

RESUME_PARSER_URL = "http://127.0.0.1:8001/parse"
ATS_MICROSERVICE_URL = "http://127.0.0.1:8000/score"
JOB_MATCHER_URL = "http://127.0.0.1:8002/match"
QNA_SUGGESTER_URL = "http://127.0.0.1:8003/suggest"


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    redis_client.ping()
    REDIS_ENABLED = True
    print(" Redis connected successfully.")
except Exception:
    redis_client = None
    REDIS_ENABLED = False
    print(" Redis not connected — proceeding without cache.")

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")


app = FastAPI(
    title="Resume Analyzer API",
    description=(
        "Central Gateway orchestrating Resume Parser, ATS Scoring, "
        "Job Matcher, and QnA Suggester microservices.\n\n"
        "Upload a resume to trigger the full Resume Analysis Pipeline."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gateway, prefix="/api/v1")

@app.get("/", tags=["Root"])
def root():
    return {"message": "Resume Analyzer Gateway is live!"}

@app.post("/api/v1/analyze", tags=["Resume Analysis Pipeline"])
async def analyze_resume(file: UploadFile = File(...)):
    """
    Pipeline:
       Send resume to Resume Parser (8001)
       Send parsed data to ATS Scoring (8000)
       Send ATS result + resume text to Job Matcher (8002)
       Send skills to QnA Suggester (8003)
       (Optional) Cache results in Redis
    """
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:

            logging.info(" Sending resume to Resume Parser (8001)")
            parser_response = await client.post(
                RESUME_PARSER_URL,
                files={"file": (file.filename, await file.read(), file.content_type)},
            )
            if parser_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Resume Parser service failed.")
            parsed_resume = parser_response.json().get("parsed_data", {})
            logging.info(" Resume parsed successfully.")

            job_description = {
                "required_skills": ["python", "aws", "docker"],
                "required_years": 2,
                "required_education": ["B.Tech"],
                "keywords": ["engineer", "fastapi"],
            }

            ats_payload = {"user_id": "U001", "resume": parsed_resume, "jd": job_description}
            logging.info(" Sending parsed resume to ATS Scoring (8000)")
            ats_response = await client.post(ATS_MICROSERVICE_URL, json=ats_payload)
            if ats_response.status_code != 200:
                raise HTTPException(status_code=500, detail="ATS Scoring service failed.")
            ats_result = ats_response.json()
            logging.info(" ATS Scoring completed with score: %s", ats_result.get("ats_score"))

            matcher_payload = {
                "resume_text": parsed_resume.get("text", ""),
                "job_list": [
                    {"title": "Python Developer", "description": "Looking for engineer with FastAPI and AWS skills."},
                    {"title": "Cloud Engineer", "description": "Experience in Docker, AWS, and scalable APIs."},
                ],
            }
            logging.info(" Sending data to Job Matcher (8002)")
            matcher_response = await client.post(JOB_MATCHER_URL, json=matcher_payload)
            if matcher_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Job Matcher service failed.")
            matcher_result = matcher_response.json()
            logging.info(" Job Matcher returned best match: %s", matcher_result.get("best_match"))

            suggester_payload = {"skills": parsed_resume.get("skills", [])}
            logging.info(" Fetching interview questions from QnA Suggester (8003)")
            qna_response = await client.post(QNA_SUGGESTER_URL, json=suggester_payload)
            if qna_response.status_code != 200:
                raise HTTPException(status_code=500, detail="QnA Suggester service failed.")
            qna_result = qna_response.json()
            logging.info(" QnA Suggestions received successfully.")

            combined_result = {
                "ats_score": ats_result.get("ats_score"),
                "breakdown": ats_result.get("breakdown"),
                "best_match": matcher_result.get("best_match"),
                "suggested_qna": qna_result.get("suggested_qna", {}),
            }

            if REDIS_ENABLED:
                redis_client.set("last_analysis", json.dumps(combined_result))
                logging.info(" Cached latest analysis in Redis.")

            return {
                "status": "success",
                "parsed_resume": parsed_resume,
                "ats_score": ats_result.get("ats_score"),
                "breakdown": ats_result.get("breakdown"),
                "job_matches": matcher_result.get("matches", []),
                "best_match": matcher_result.get("best_match"),
                "suggested_qna": qna_result.get("suggested_qna", {}),
            }

    except httpx.ConnectError as e:
        logging.error("Connection error: %s", e)
        raise HTTPException(status_code=503, detail=f"Connection error: {e}")

    except httpx.ReadTimeout:
        logging.error("Timeout: One of the microservices took too long.")
        raise HTTPException(status_code=504, detail="A microservice timed out.")

    except Exception as e:
        logging.exception("Unhandled error occurred.")
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {e}")
