from fastapi import FastAPI, Request

app = FastAPI(
    title="QnA Suggester Microservice",
    description="Generates interview questions based on resume skills and job description.",
    version="1.1.0",
)

QNA_DATA = {
    "python": ["What are Python decorators?", "Explain list vs tuple."],
    "aws": ["What is EC2?", "Explain S3 lifecycle policies."],
    "docker": ["What is a Docker volume?", "Difference between Docker and VM?"],
    "fastapi": ["How does FastAPI handle async requests?"],
    "engineer": ["What responsibilities does a software engineer have?"],
}


@app.get("/", tags=["Health"])
def health_check():
    """Simple route to verify microservice is up."""
    return {"status": "QnA Suggester service running"}


@app.post("/suggest", tags=["QnA Generation"])
async def suggest_qna(request: Request):
    """
    Generate interview QnA suggestions from skills and job keywords.
    Accepts JSON payload with:
    {
        "resume": {"skills": [...]},
        "jd": {"keywords": [...]},
        "suggestions": [...]
    }
    """
    try:
        data = await request.json()
        resume = data.get("resume", {})
        jd = data.get("jd", {})
        prev_suggestions = data.get("suggestions", [])

        all_topics = set(resume.get("skills", [])) | set(jd.get("keywords", []))

        qna = {}
        for topic in all_topics:
            qna[topic] = QNA_DATA.get(topic.lower(), ["No specific questions found."])

        if prev_suggestions:
            qna["general_tips"] = [
                "Review key topics: " + ", ".join(all_topics),
                "Focus on " + ", ".join(prev_suggestions),
            ]

        return {"status": "success", "questions": qna}

    except Exception as e:
        return {"status": "error", "message": str(e)}
