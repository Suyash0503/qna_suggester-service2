
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services import parse_jd

router = APIRouter(tags=["job"])

class JobInput(BaseModel):
    title: str
    description: str

class JobResponse(BaseModel):
    message: str
    job: Dict[str, Any]

@router.post("/upload", response_model=JobResponse)
async def upload_job(job: JobInput):
    # Use _extract since description is plain text, not a file key
    jd_data = parse_jd._extract(job.description)
    return {"message": f"Job '{job.title}' uploaded successfully", "job": jd_data}
