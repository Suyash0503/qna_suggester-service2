from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import os
import re
from uuid import uuid4

router = APIRouter(prefix="/resume", tags=["Resume Upload"])

UPLOAD_DIR = "uploaded_resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ResumeUploadResponse(BaseModel):
    message: str
    key: str
    url: str
    extracted: Dict[str, Any]

def extract_resume_data(content: str) -> Dict[str, Any]:
    """Lightweight resume parser (mock for parse_resume microservice)."""

    lines = [line.strip() for line in content.split("\n") if line.strip()]
    name = lines[0] if lines else "Unknown"


    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", content)
    phone_match = re.search(r"\+?\d[\d\s\-\(\)]{8,}\d", content)

    skills_list = [
        "python", "aws", "docker", "fastapi", "sql", "java",
        "c++", "javascript", "machine learning", "linux", "git"
    ]
    found_skills = [skill for skill in skills_list if skill.lower() in content.lower()]

    exp_match = re.search(r"(\d+)\s*\+?\s*years?", content.lower())
    exp_years = int(exp_match.group(1)) if exp_match else 0

    return {
        "name": name,
        "email": email_match.group(0) if email_match else "N/A",
        "phone": phone_match.group(0) if phone_match else "N/A",
        "skills": found_skills,
        "experience_years": exp_years,
    }

@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """Upload a resume file, extract basic info, and return file key + mock URL."""
    try:
        contents = await file.read()
        text_content = contents.decode("utf-8", errors="ignore")

        key = f"{uuid4().hex}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, key)

        with open(file_path, "wb") as f:
            f.write(contents)

        extracted_data = extract_resume_data(text_content)

        presigned_url = f"http://127.0.0.1:8080/static/{key}"

        return {
            "message": "Resume uploaded successfully",
            "key": key,
            "url": presigned_url,
            "extracted": extracted_data,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {e}")
