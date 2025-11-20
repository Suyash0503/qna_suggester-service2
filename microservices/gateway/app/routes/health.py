from fastapi import APIRouter
import httpx

router = APIRouter(prefix="/health", tags=["Health"])

# Use Docker service URLs (NOT localhost)
ATS_SCORING_URL = "http://ats_scoring:8003/health"
RESUME_PARSER_URL = "http://resume_parser:8001/health"
JD_PARSER_URL = "http://jd_parser:8002/health"


@router.get("/")
async def health_check():
    """
    Global health check for all microservices.
    """
    microservices_status = {}

    async def check_service(name, url):
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    microservices_status[name] = "running"
                else:
                    microservices_status[name] = f"unhealthy ({response.status_code})"
        except Exception as e:
            microservices_status[name] = f"unreachable ({e})"

    # Check all microservices
    await check_service("ats_scoring", ATS_SCORING_URL)
    await check_service("resume_parser", RESUME_PARSER_URL)
    await check_service("jd_parser", JD_PARSER_URL)

    return {
        "status": "ok",
        "message": "Gateway is running",
        "microservices": microservices_status
    }
