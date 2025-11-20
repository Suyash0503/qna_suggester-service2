from fastapi import APIRouter, UploadFile, File, HTTPException
import httpx
import uuid

from app.infra.storage import put_object_bytes
from app.infra.db import save_analysis

router = APIRouter(prefix="/analyze", tags=["ATS Scoring & Analysis"])

# ---- Microservice URLs (use docker service names) ----
RESUME_PARSER_URL = "http://resume_parser:8001/parse"
JD_PARSER_URL = "http://jd_parser:8002/parse-jd"
ATS_SCORING_URL = "http://ats_scoring:8003/score"


@router.post("/score")
async def analyze_resume_and_jd(
    resume: UploadFile = File(...),
    jd: UploadFile = File(...)
):
    """
    Full pipeline:
    1) Upload resume + JD to S3
    2) Call Resume Parser MS
    3) Call JD Parser MS
    4) Call ATS Scoring MS
    5) Save in DynamoDB
    """

    try:
        # 1. Read uploaded files
        resume_bytes = await resume.read()
        jd_bytes = await jd.read()

        resume_s3_key = put_object_bytes(resume_bytes, resume.filename)
        jd_s3_key = put_object_bytes(jd_bytes, jd.filename)

        # 2. Call Resume Parser
        async with httpx.AsyncClient(timeout=20.0) as client:
            resume_response = await client.post(
                RESUME_PARSER_URL,
                files={"file": (resume.filename, resume_bytes, resume.content_type)}
            )

        if resume_response.status_code != 200:
            raise HTTPException(
                status_code=resume_response.status_code,
                detail="Resume Parser Microservice Failed."
            )

        parsed_resume = resume_response.json().get("parsed_data", {})
        resume_text = parsed_resume.get("raw_text", "")
        resume_skills = parsed_resume.get("skills", [])

        # 3. Call JD Parser
        async with httpx.AsyncClient(timeout=20.0) as client:
            jd_response = await client.post(
                JD_PARSER_URL,
                files={"file": (jd.filename, jd_bytes, jd.content_type)}
            )

        if jd_response.status_code != 200:
            raise HTTPException(
                status_code=jd_response.status_code,
                detail="JD Parser Microservice Failed."
            )

        parsed_jd = jd_response.json().get("parsed_data", {})
        jd_text = parsed_jd.get("raw_text", "")
        jd_skills = parsed_jd.get("skills", [])
        job_title = parsed_jd.get("job_title", "")

        # 4. Call ATS Scoring MS
        ats_payload = {
            "resume_text": resume_text,
            "job_description_text": jd_text,
            "resume_skills": resume_skills,
            "jd_skills": jd_skills,
            "job_title": job_title
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            ats_response = await client.post(ATS_SCORING_URL, json=ats_payload)

        if ats_response.status_code != 200:
            raise HTTPException(
                status_code=ats_response.status_code,
                detail="ATS Scoring Microservice Failed."
            )

        ats_json = ats_response.json()
        match_score = ats_json.get("match_score")
        breakdown = ats_json.get("breakdown", {})
        feedback = ats_json.get("feedback")

        # 5. Save in DynamoDB
        analysis_id = str(uuid.uuid4())
        save_analysis(
            resume_id=resume_s3_key,
            job_id=jd_s3_key,
            score=match_score,
            details={
                "resume_skills": resume_skills,
                "jd_skills": jd_skills,
                "job_title": job_title,
                "ats_breakdown": breakdown,
                "feedback": feedback
            }
        )

        # 6. Return response
        return {
            "status": "success",
            "analysis_id": analysis_id,
            "resume_s3_key": resume_s3_key,
            "jd_s3_key": jd_s3_key,
            "match_score": match_score,
            "feedback": feedback,
            "breakdown": breakdown
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis pipeline failed: {e}")
