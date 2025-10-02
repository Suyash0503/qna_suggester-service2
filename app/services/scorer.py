# def match(resume: dict, jd: dict) -> float:
#     # Basic overlap score (to be replaced with ML model)
#     resume_skills = set(resume.get("skills", []))
#     jd_skills = set(jd.get("skills", []))
#     common = resume_skills & jd_skills
#     return len(common) / max(len(jd_skills), 1) * 100

# services/scorer.py
from typing import Dict, Any, Tuple

WEIGHTS = {
    "skills": 0.60,
    "experience": 0.20,
    "education": 0.10,
    "keywords": 0.10,
}

def _pct(numer: int, denom: int) -> float:
    if denom <= 0:
        return 1.0  # if JD doesn’t specify, treat as satisfied
    return max(0.0, min(1.0, numer / denom))

def match(resume: Dict[str, Any], jd: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    r_skills = set(resume.get("skills", []))
    j_skills = set(jd.get("required_skills", []))
    skills_pct = _pct(len(r_skills & j_skills), len(j_skills))

    r_years = resume.get("experience_years", 0) or 0
    j_years = jd.get("required_years", 0) or 0
    exp_pct = 1.0 if r_years >= j_years else r_years / (j_years or 1)

    r_edu = set(resume.get("education", []))
    j_edu = set(jd.get("required_education", []))
    edu_pct = 1.0 if not j_edu else (1.0 if (r_edu & j_edu) else 0.0)

    r_text = (resume.get("text") or "").lower()
    keywords = jd.get("keywords", [])
    kw_hits = sum(1 for k in keywords if k in r_text)
    kw_pct = _pct(kw_hits, len(keywords))

    score = (
        skills_pct * WEIGHTS["skills"]
        + exp_pct * WEIGHTS["experience"]
        + edu_pct * WEIGHTS["education"]
        + kw_pct * WEIGHTS["keywords"]
    ) * 100.0

    breakdown = {
        "skills_pct": round(skills_pct, 3),
        "experience_pct": round(exp_pct, 3),
        "education_pct": round(edu_pct, 3),
        "keywords_pct": round(kw_pct, 3),
    }
    return round(score, 1), breakdown
