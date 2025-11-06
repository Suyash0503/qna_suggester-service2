# app/api/v1/health.py
from fastapi import APIRouter
import httpx

router = APIRouter(prefix="/health", tags=["Health"])

ATS_SCORING_URL = "http://127.0.0.1:8000/"

@router.get("/")
async def health_check():
    """
    Global health check endpoint for the main backend.
    Optionally pings the ATS scoring microservice to confirm connectivity.
    """
    microservices_status = {}
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(ATS_SCORING_URL)
            if res.status_code == 200:
                microservices_status["ats_scoring"] = "running"
            else:
                microservices_status["ats_scoring"] = f"unhealthy ({res.status_code})"
    except Exception as e:
        microservices_status["ats_scoring"] = f"unreachable ({e})"

    return {
        "status": "ok",
        "message": "Main backend is running",
        "microservices": microservices_status
    }
