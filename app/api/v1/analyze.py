from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import httpx
from storage import put_object  
from db import save_analysis    

router = APIRouter(prefix="/analyze", tags=["ATS Scoring & Analysis"])

ATS_SCORING_URL = "http://127.0.0.1:8000/score"


@router.post("/file")
async def analyze_from_files(
    resume: UploadFile = File(...),
    jd: UploadFile = File(...),
):
    """
    Accepts two uploaded files (resume + JD),
    uploads them to S3, extracts content as text,
    and forwards to the ATS microservice for scoring.
    Stores results in DynamoDB.
    """
    try:
        resume_s3_key = put_object(resume)
        jd_s3_key = put_object(jd)

        resume_bytes = await resume.read()
        jd_bytes = await jd.read()

        resume_text = resume_bytes.decode("utf-8", errors="ignore")
        jd_text = jd_bytes.decode("utf-8", errors="ignore")


        resume_data = {
            "skills": ["python", "aws", "fastapi"],
            "experience_years": 3,
            "education": ["B.Tech"],
            "text": resume_text,
        }

        jd_data = {
            "required_skills": ["python", "aws", "docker"],
            "required_years": 2,
            "required_education": ["B.Tech"],
            "keywords": ["engineer", "fastapi"],
        }

        payload = {
            "user_id": "U001",
            "resume": resume_data,
            "jd": jd_data,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(ATS_SCORING_URL, json=payload)
            response.raise_for_status()
            ats_result = response.json()

        save_analysis(
            user_id="U001",
            parsed_resume=resume_data,
            ats_score=ats_result.get("ats_score"),
            job_matches=[] 
        )

        return {
            "status": "success",
            "resume_s3_key": resume_s3_key,
            "jd_s3_key": jd_s3_key,
            "ats_score": ats_result.get("ats_score"),
            "breakdown": ats_result.get("breakdown"),
        }

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="ATS microservice is unavailable.")
    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail="ATS microservice timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File-based analysis failed: {e}")


@router.post("/text")
async def analyze_from_text(
    resume_text: str = Form(...),
    jd_text: str = Form(...),
):
    """
    Accept plain text inputs (resume + job description)
    and send to ATS microservice for scoring.
    Also stores results in DynamoDB.
    """
    try:
        resume_data = {
            "skills": resume_text.split(),
            "experience_years": 2,
            "education": ["B.Tech"],
            "text": resume_text,
        }

        jd_data = {
            "required_skills": jd_text.split(),
            "required_years": 2,
            "required_education": ["B.Tech"],
            "keywords": jd_text.split(),
        }

        payload = {
            "user_id": "demo_user",
            "resume": resume_data,
            "jd": jd_data,
        }


        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(ATS_SCORING_URL, json=payload)
            response.raise_for_status()
            ats_result = response.json()

        save_analysis(
            user_id="demo_user",
            parsed_resume=resume_data,
            ats_score=ats_result.get("ats_score"),
            job_matches=[]
        )

        return {
            "status": "success",
            "ats_score": ats_result.get("ats_score"),
            "breakdown": ats_result.get("breakdown"),
        }

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="ATS microservice is unavailable.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text-based analysis failed: {e}")


@router.get("/health")
def analyze_health():
    """Simple health endpoint to confirm Analyze router is running."""
    return {"status": "ok", "message": "Analyze router connected successfully to ATS microservice"}
