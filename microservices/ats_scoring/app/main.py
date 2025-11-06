from fastapi import FastAPI, Request
from microservices.ats_scoring.app.service import match
from microservices.ats_scoring.app.redis_client import get_redis_client


# Create FastAPI app instance
app = FastAPI(
    title="ATS Scoring Microservice",
    description="Microservice for computing ATS score based on resume and job description.",
    version="1.0"
)
redis_client = get_redis_client()

@app.get("/")
def health_check():
    """Simple route to verify service is running."""
    return {"status": "ATS Scoring service is running"}


@app.post("/score")
async def score_resume(request: Request):
    """Compute ATS score given resume and job description data."""
    data = await request.json()
    print(" Incoming data from Gateway:", data)
    resume = data.get("resume", {})
    jd = data.get("jd", {})
    user_id = data.get("user_id", "unknown")
    score, breakdown = match(resume, jd)
    redis_client.set(user_id, score)

    return {
        "user_id": user_id,
        "ats_score": score,
        "breakdown": breakdown
    }
