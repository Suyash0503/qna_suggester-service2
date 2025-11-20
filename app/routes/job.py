from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from typing import Dict, Any

router = APIRouter(prefix="/job", tags=["Job Description"])

# JD parser microservice URL (inside Docker network)
JD_PARSER_URL = "http://jd_parser:8002/parse-text"

class JobInput(BaseModel):
    title: str
    description: str


@router.post("/upload")
async def upload_job(job: JobInput):
    """
    Upload JD → Forward to JD Parser microservice → Return structured output
    """

    payload = {
        "title": job.title,
        "text": job.description
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(JD_PARSER_URL, json=payload)

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="JD Parser microservice failed"
            )

        parsed_jd = response.json().get("parsed_data", {})

        return {
            "message": f"Job '{job.title}' uploaded successfully",
            "job": parsed_jd
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JD upload failed: {e}")
