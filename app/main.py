from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import logging

from microservices.gateway.app.main import gateway
from app.infra.storage import put_object
from app.infra.db import save_analysis

app = FastAPI(title="Resume Analyzer API Gateway", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# microservices
RESUME_PARSER_URL = os.getenv("RESUME_PARSER_URL", "http://127.0.0.1:8001/parse")
JD_PARSER_URL      = os.getenv("JD_PARSER_URL", "http://127.0.0.1:8002/parse-jd")
ATS_SCORING_URL    = os.getenv("ATS_SCORING_URL", "http://127.0.0.1:8003/score")
logging.basicConfig(level=logging.INFO)


@app.post("/api/v1/analyze")
async def analyze_resume(file: UploadFile = File(...), jd: UploadFile = File(...)):
    """
    Pipeline:
    1. Upload files to S3
    2. Send resume to Resume Parser Service → extract text/skills
    3. Send parsed resume text + job description text to ATS scoring service
    4. Save final score & parsed data to DynamoDB
    """

    try:
        logging.info(" Uploading files to S3...")
        resume_s3_key = put_object(file)
        jd_s3_key = put_object(jd)

        logging.info(" Sending file to Resume Parser Service (8002)...")
        async with httpx.AsyncClient(timeout=15.0) as client:
            parser_response = await client.post(
                RESUME_PARSER_URL,
                files={"file": (file.filename, await file.read(), file.content_type)},
            )

        if parser_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Resume Parser service failed.")

        parsed_resume = parser_response.json().get("parsed_data")
        if not parsed_resume:
            raise HTTPException(status_code=500, detail="Parser returned no data.")

        resume_text = parsed_resume.get("text", "")

        # Read JD text directly
        jd_text = (await jd.read()).decode("utf-8", errors="ignore")

        logging.info(" Sending parsed data to ATS Scoring (8000)...")
        score_payload = {
            "resume_text": resume_text,
            "job_description": jd_text,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            ats_response = await client.post(ATS_SCORING_URL, json=score_payload)

        if ats_response.status_code != 200:
            raise HTTPException(status_code=500, detail="ATS Scoring service failed.")

        ats_result = ats_response.json()
        ats_score = ats_result.get("score")

        logging.info(" Saving results to DynamoDB...")
        save_analysis(
            user_id="U001",
            parsed_resume=parsed_resume,
            ats_score=ats_score,
            job_matches=[]  # Future feature placeholder
        )

        return {
            "status": "success",
            "resume_s3_key": resume_s3_key,
            "jd_s3_key": jd_s3_key,
            "parsed_skills": parsed_resume.get("skills", []),
            "experience_years": parsed_resume.get("experience_years", 1),
            "education": parsed_resume.get("education", []),
            "ats_score": ats_score,
            "breakdown": ats_result.get("breakdown"),   # Provided by ATS Microservice
        }

    except Exception as e:
        logging.error(f" Pipeline execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {e}")


@app.get("/")
def health():
    return {"status": "API Gateway running"}

app.include_router(gateway)
