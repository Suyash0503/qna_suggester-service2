
import os, re
from typing import Dict, Any, Tuple

# Weights can be tuned from environment/config
WEIGHTS = {
    "skills": float(os.getenv("WEIGHT_SKILLS", 0.60)),
    "experience": float(os.getenv("WEIGHT_EXPERIENCE", 0.20)),
    "education": float(os.getenv("WEIGHT_EDUCATION", 0.10)),
    "keywords": float(os.getenv("WEIGHT_KEYWORDS", 0.10)),
}

def _pct(numer: int, denom: int) -> float:
    if denom <= 0:
        return 1.0  # treat as satisfied if JD doesn’t specify
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
    edu_pct = 1.0 if not j_edu else _pct(len(r_edu & j_edu), len(j_edu))

    r_text = (resume.get("text") or "").lower()
    keywords = jd.get("keywords", [])
    kw_hits = sum(1 for k in keywords if re.search(rf"\b{k}\b", r_text))
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
