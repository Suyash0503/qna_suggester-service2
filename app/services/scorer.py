def match(resume: dict, jd: dict) -> float:
    # Basic overlap score (to be replaced with ML model)
    resume_skills = set(resume.get("skills", []))
    jd_skills = set(jd.get("skills", []))
    common = resume_skills & jd_skills
    return len(common) / max(len(jd_skills), 1) * 100
