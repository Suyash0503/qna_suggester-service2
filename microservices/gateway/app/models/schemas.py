
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# ---------- Resume Upload ----------
class ResumeUploadResponse(BaseModel):
    key: str = Field(..., description="S3 key for the uploaded resume")
    url: str = Field(..., description="Presigned download URL (temporary)")

# ---------- Job Upload ----------
class JobInput(BaseModel):
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Full job description text")

class JobResponse(BaseModel):
    message: str
    job: Dict[str, Any]

# ---------- Analysis ----------
class AnalyzeRequest(BaseModel):
    resume_key: str = Field(..., description="S3 key of uploaded resume")
    jd_key: str = Field(..., description="S3 key of uploaded job description")

class AnalyzeResponse(BaseModel):
    score: float
    suggestions: List[str]
    extracted: Dict[str, Any]

# More granular analysis (ATS, suggestions, questions, exam)
class AnalyzeInput(BaseModel):
    resume_text: str
    jd_text: str

class ATSResponse(BaseModel):
    ats_score: float

class SuggestionResponse(BaseModel):
    suggestions: List[str]

class QuestionResponse(BaseModel):
    questions: List[str]

class ExamInput(BaseModel):
    answers: List[str]

class ExamResponse(BaseModel):
    exam_score: float

# ---------- Health ----------
class HealthResponse(BaseModel):
    ok: bool
    db: Optional[bool] = None
    redis: Optional[bool] = None
