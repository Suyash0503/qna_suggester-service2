from typing import Dict, Tuple

def match(resume: Dict, jd: Dict) -> Tuple[int, Dict]:
    """
    Compute ATS score and detailed breakdown between resume and job description.
    """

    resume_skills = set(map(str.lower, resume.get("skills", [])))
    jd_skills = set(map(str.lower, jd.get("required_skills", [])))
    resume_text = resume.get("text", "").lower()
    jd_keywords = [k.lower() for k in jd.get("keywords", [])]
    exp_years = resume.get("experience_years", 0)
    jd_years = jd.get("required_years", 0)
    education = [e.lower() for e in resume.get("education", [])]
    jd_edu = [e.lower() for e in jd.get("required_education", [])]

    skill_matches = resume_skills.intersection(jd_skills)
    skill_pct = len(skill_matches) / len(jd_skills) if jd_skills else 0

    exp_pct = min(exp_years / jd_years, 1.0) if jd_years else 1.0


    edu_pct = 1.0 if any(e in education for e in jd_edu) else 0.0


    keyword_hits = [k for k in jd_keywords if k in resume_text]
    keyword_pct = len(keyword_hits) / len(jd_keywords) if jd_keywords else 0

    total_score = (
        (skill_pct + exp_pct + edu_pct + keyword_pct) / 4
    ) * 100

    if total_score >= 85:
        summary = "Excellent match! Your resume aligns very well with the job requirements."
    elif total_score >= 70:
        summary = "Good match! You meet most requirements but could improve keyword relevance."
    elif total_score >= 50:
        summary = "Average match. Some key skills or keywords are missing."
    else:
        summary = "Low match. Consider adding relevant skills and keywords from the job description."

    breakdown = {
        "skills_match": f"{skill_pct*100:.1f}%",
        "experience_match": f"{exp_pct*100:.1f}%",
        "education_match": f"{edu_pct*100:.1f}%",
        "keywords_match": f"{keyword_pct*100:.1f}%",
        "summary": summary
    }

    return int(total_score), breakdown
