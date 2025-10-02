# def rewrite(resume: dict, jd: dict) -> list[str]:
#     # Simple suggestion: missing skills
#     resume_skills = set(resume.get("skills", []))
#     jd_skills = set(jd.get("skills", []))
#     missing = jd_skills - resume_skills
#     return [f"Consider adding {skill}" for skill in missing]
# services/suggester.py
from typing import Dict, Any, List

ACTION_VERBS = [
    "built", "designed", "implemented", "led", "optimized", "delivered", "improved",
    "migrated", "developed", "automated", "reduced"
]

def rewrite(resume: Dict[str, Any], jd: Dict[str, Any]) -> List[str]:
    out = []

    r_skills = set(resume.get("skills", []))
    j_skills = set(jd.get("required_skills", []))
    missing = sorted(list(j_skills - r_skills))
    if missing:
        out.append(f"Consider adding these missing skills: {', '.join(missing)}")

    r_text = (resume.get("text") or "").lower()
    keywords = jd.get("keywords", [])
    missing_kw = [k for k in keywords if k not in r_text]
    if missing_kw:
        out.append(f"Include role keywords: {', '.join(missing_kw)}")

    # style suggestion
    if not any(v in (resume.get("text") or "").lower() for v in ACTION_VERBS):
        out.append("Use stronger action verbs (e.g., built, designed, implemented, optimized).")

    # education
    if jd.get("required_education"):
        if not set(resume.get("education", [])) & set(jd["required_education"]):
            out.append("Ensure required education is clearly listed (degree & institution).")

    # experience
    if jd.get("required_years", 0) > (resume.get("experience_years", 0) or 0):
        out.append("Quantify your experience with years and scope in relevant roles.")

    return out
