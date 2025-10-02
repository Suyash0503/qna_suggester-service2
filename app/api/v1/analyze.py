# from fastapi import APIRouter
# from app.models.schemas import AnalyzeRequest, AnalyzeResponse
# from app.services import parse_resume, parse_jd, scorer, suggester

# router = APIRouter(tags=["analyze"])

# @router.post("/analyze", response_model=AnalyzeResponse)
# async def analyze(req: AnalyzeRequest):
#     r = parse_resume.run(req.resume_key)
#     j = parse_jd.run(req.jd_key)
#     score = scorer.match(r, j)            
#     suggestions = suggester.rewrite(r, j) 
#     return {"score": score, "suggestions": suggestions, "extracted": r}

# api/v1/analyze.py
from fastapi import APIRouter
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services import parse_resume, parse_jd, scorer, suggester, db

router = APIRouter(tags=["analyze"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    r = parse_resume.run(req.resume_key)
    j = parse_jd.run(req.jd_key)
    score, breakdown = scorer.match(r, j)
    suggestions = suggester.rewrite(r, j)

    details = {
        "breakdown": breakdown,
        "resume": {
            "name": r.get("name"), "email": r.get("email"), "phone": r.get("phone"),
            "skills": r.get("skills"), "experience_years": r.get("experience_years"),
        },
        "jd": {
            "job_title": j.get("job_title"), "required_skills": j.get("required_skills"),
            "keywords": j.get("keywords"), "required_years": j.get("required_years")
        }
    }

    # persist analysis (use keys as ids)
    db.save_analysis(resume_id=req.resume_key, job_id=req.jd_key, score=score, details=details)

    return {"score": score, "suggestions": suggestions, "extracted": r}
