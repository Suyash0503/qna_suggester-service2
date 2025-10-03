
from fastapi import APIRouter
from app.models.schemas import (
    AnalyzeRequest, AnalyzeResponse,
    AnalyzeInput, ATSResponse, SuggestionResponse,
    QuestionResponse, ExamInput, ExamResponse
)
from app.services import parse_resume, parse_jd, scorer, suggester, qna, db

router = APIRouter(tags=["analyze"])


# ---------- Full Analysis (resume_key + jd_key from S3/Dynamo) ----------
@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    # Parse stored resume and JD files
    r = parse_resume.run(req.resume_key)
    j = parse_jd.run(req.jd_key)

    # Compute score + suggestions
    score, breakdown = scorer.match(r, j)
    suggestions = suggester.rewrite(r, j)

    # Prepare details for persistence
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

    # Save analysis in DynamoDB
    db.save_analysis(resume_id=req.resume_key, job_id=req.jd_key, score=score, details=details)

    return {"score": score, "suggestions": suggestions, "extracted": r}


# ---------- Modular Endpoints (direct text input) ----------
@router.post("/ats-score", response_model=ATSResponse)
async def get_ats_score(data: AnalyzeInput):
    # Here scorer.match returns (score, breakdown), so pick score only
    score, _ = scorer.match(
        {"skills": data.resume_text.split()}, 
        {"required_skills": data.jd_text.split()}
    )
    return {"ats_score": score}


@router.post("/suggestions", response_model=SuggestionResponse)
async def get_suggestions(data: AnalyzeInput):
    # For modular text inputs, call suggester directly
    suggestions = suggester.rewrite(
        {"skills": data.resume_text.split(), "text": data.resume_text},
        {"required_skills": data.jd_text.split(), "keywords": data.jd_text.split()}
    )
    return {"suggestions": suggestions}


@router.post("/questions", response_model=QuestionResponse)
async def generate_questions(data: AnalyzeInput):
    questions = qna.generate(data.resume_text, data.jd_text)
    return {"questions": questions}


@router.post("/exam-score", response_model=ExamResponse)
async def evaluate_exam(data: ExamInput):
    score = qna.evaluate(data.answers)
    return {"exam_score": score}
