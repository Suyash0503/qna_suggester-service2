from fastapi import FastAPI, Request
import math

app = FastAPI(
    title="Job Matcher Microservice",
    description="Matches parsed resume data against available job descriptions.",
    version="1.1.0",
)


@app.get("/", tags=["Health"])
def health_check():
    """Verify microservice is running."""
    return {"status": "Job Matcher service running"}


@app.post("/match", tags=["Job Matching"])
async def match_jobs(request: Request):
    """
    Compare candidate resume content with multiple job descriptions.
    Input JSON:
    {
        "resume": {"text": "...", "skills": [...]},
        "jd": {"required_skills": [...], "keywords": [...]},
        "ats_score": 75
    }
    """
    try:
        data = await request.json()
        resume = data.get("resume", {})
        jd = data.get("jd", {})
        ats_score = data.get("ats_score", 0)

        resume_text = resume.get("text", "").lower()
        resume_skills = set(resume.get("skills", []))
        jd_skills = set(jd.get("required_skills", []))
        jd_keywords = set(jd.get("keywords", []))

        matched_skills = resume_skills & jd_skills
        skill_match_pct = (len(matched_skills) / max(len(jd_skills), 1)) * 100

        text_tokens = set(resume_text.split())
        keyword_overlap = len(text_tokens & jd_keywords)
        keyword_pct = (keyword_overlap / max(len(jd_keywords), 1)) * 100

        final_match = round((0.6 * skill_match_pct + 0.3 * ats_score + 0.1 * keyword_pct), 2)

        suggestions = []
        if final_match >= 80:
            suggestions.append("Highly suitable for Software Engineer / Backend Developer roles")
        elif final_match >= 60:
            suggestions.append("Moderately suitable — consider emphasizing missing skills")
        else:
            suggestions.append("Low suitability — enhance project details or missing keywords")

        return {
            "status": "success",
            "matches": [
                {
                    "job_title": "Software Engineer",
                    "skill_match_pct": round(skill_match_pct, 2),
                    "keyword_match_pct": round(keyword_pct, 2),
                    "ats_score": ats_score,
                    "final_match": final_match,
                }
            ],
            "suggestions": suggestions,
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
