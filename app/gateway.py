
from fastapi import APIRouter

# Import routers from v1
from app.api.v1.health import router as health_router
from app.api.v1.resume import router as resume_router
from app.api.v1.job import router as job_router
from app.api.v1.analyze import router as analyze_router

# Create central gateway router
gateway = APIRouter()

# Register sub-routers (organized by service)
gateway.include_router(health_router, prefix="/health", tags=["health"])
gateway.include_router(resume_router, prefix="/resume", tags=["resume"])
gateway.include_router(job_router, prefix="/job", tags=["job"])
gateway.include_router(analyze_router, prefix="/analyze", tags=["analyze"])
