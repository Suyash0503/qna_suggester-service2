from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.resume import router as resume_router
from app.api.v1.job import router as job_router
from app.api.v1.analyze import router as analyze_router

# Central API Gateway Router
gateway = APIRouter()

# Health check for the main backend
gateway.include_router(
    health_router,
    prefix="/health",
    tags=["Health"]
)

# Resume upload & management
gateway.include_router(
    resume_router,
    prefix="/resume",
    tags=["Resume"]
)

# Job upload & JD parsing
gateway.include_router(
    job_router,
    prefix="/job",
    tags=["Job Description"]
)

# Analyze pipeline (Resume → ATS → Job Match → QnA)
gateway.include_router(
    analyze_router,
    prefix="/analyze",
    tags=["ATS Scoring & Analysis"]
)
