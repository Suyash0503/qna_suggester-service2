from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
import re

router = APIRouter(prefix="/job", tags=["Job Description"])

class JobInput(BaseModel):
    title: str
    description: str


class JobResponse(BaseModel):
    message: str
    job: Dict[str, Any]

def extract_job_details(description: str) -> Dict[str, Any]:
    """
    Lightweight JD parser (mock microservice)
    Extracts skills, keywords, and years of experience from text.
    """

    # Converting description to lowercase for pattern matching
    text = description.lower()

    # Example skill list (extend as needed)
    skill_keywords = [
        "python", "aws", "fastapi", "docker", "sql", "linux",
        "kubernetes", "git", "react", "node", "machine learning"
    ]
    found_skills = [skill for skill in skill_keywords if skill in text]

    experience_matches = re.findall(r"(\d+)\s*\+?\s*years?", text)
    experience_years = int(experience_matches[0]) if experience_matches else 0

    education_keywords = ["b.tech", "m.tech", "bachelor", "master", "degree"]
    found_education = [edu for edu in education_keywords if edu in text]

    words = re.findall(r"\b[a-zA-Z]{4,}\b", text)
    top_keywords = list(set(found_skills + found_education + words[:10]))

    return {
        "job_title": re.sub(r"[^a-zA-Z0-9 ]", "", description.split("\n")[0])[:80],
        "required_skills": found_skills,
        "required_years": experience_years,
        "required_education": found_education,
        "keywords": top_keywords,
    }

@router.post("/upload", response_model=JobResponse)
async def upload_job(job: JobInput):
    """
    Upload a Job Description (JD) and extract important info.
    Future integration: this will call the 'parse_jd' microservice.
    """
    jd_data = extract_job_details(job.description)

    return {
        "message": f"Job '{job.title}' uploaded successfully",
        "job": jd_data,
    }
