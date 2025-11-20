from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ResumeInput(BaseModel):
    skills: List[str]
    experience_years: Optional[int] = 0
    education: Optional[List[str]] = []
    text: Optional[str] = ""

class JDInput(BaseModel):
    required_skills: List[str]
    required_years: Optional[int] = 0
    required_education: Optional[List[str]] = []
    keywords: Optional[List[str]] = []

class ScoreResponse(BaseModel):
    user_id: str
    ats_score: float
    breakdown: Dict[str, Any]
