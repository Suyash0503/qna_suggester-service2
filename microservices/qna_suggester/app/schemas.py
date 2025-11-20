from pydantic import BaseModel
from typing import List, Optional

# ---------------------- Existing Models (KEEP SAME!) ----------------------

class Resume(BaseModel):
    """Model for resume data."""
    skills: List[str]

class JobDescription(BaseModel):
    """Model for job description data."""
    keywords: List[str]

class QnARequest(BaseModel):
    """Request model for interview question generation."""
    resume: Resume
    jd: JobDescription
    suggestions: Optional[bool] = False  # KEEP SAME FOR AWS DEPLOYMENT

# ---------------------- New Model for Redis Protobuf ----------------------

class CacheProtoModel(BaseModel):
    """Model for protobuf Redis caching."""
    data: str


