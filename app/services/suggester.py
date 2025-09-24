def rewrite(resume: dict, jd: dict) -> list[str]:
    # Simple suggestion: missing skills
    resume_skills = set(resume.get("skills", []))
    jd_skills = set(jd.get("skills", []))
    missing = jd_skills - resume_skills
    return [f"Consider adding {skill}" for skill in missing]
