from pydantic import BaseModel
class AnalyzeRequest(BaseModel):
    resume_key: str
    jd_key: str

class AnalyzeResponse(BaseModel):
    score: float
    suggestions: list[str]
    extracted: dict
