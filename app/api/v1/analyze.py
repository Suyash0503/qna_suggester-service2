from fastapi import APIRouter
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services import parse_resume, parse_jd, scorer, suggester

router = APIRouter(tags=["analyze"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    r = parse_resume.run(req.resume_key)
    j = parse_jd.run(req.jd_key)
    score = scorer.match(r, j)            
    suggestions = suggester.rewrite(r, j) 
    return {"score": score, "suggestions": suggestions, "extracted": r}
