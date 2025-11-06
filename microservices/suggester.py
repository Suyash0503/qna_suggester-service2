
from typing import Dict, Any, List

ACTION_VERBS = [
    "built", "designed", "implemented", "led", "optimized", "delivered", "improved",
    "migrated", "developed", "automated", "reduced"
]

def rewrite(resume: Dict[str, Any], jd: Dict[str, Any]) -> List[str]:
    """
    Generate resume improvement suggestions based on job description.
    """
    out = []

    # Missing skills
    r_skills = set(resume.get("skills", []))
    j_skills = set(jd.get("required_skills", []))
    missing = sorted(list(j_skills - r_skills))
    if missing:
        out.append("Add or emphasize these skills: " + ", ".join(missing))

    # Missing role keywords
    r_text = (resume.get("text") or "").lower()
    keywords = jd.get("keywords", [])
    missing_kw = [k for k in keywords if k not in r_text]
    if missing_kw:
        out.append("Include these keywords for alignment: " + ", ".join(missing_kw))

    # Strong action verbs
    if not any(v in r_text for v in ACTION_VERBS):
        out.append("Use stronger action verbs (e.g., built, designed, implemented, optimized).")

    # Education
    if jd.get("required_education"):
        if not set(resume.get("education", [])) & set(jd["required_education"]):
            out.append("Clearly list required education (degree & institution).")

    # Experience
    if jd.get("required_years", 0) > (resume.get("experience_years", 0) or 0):
        out.append("Quantify your experience with years and scope in relevant roles.")

    return out
