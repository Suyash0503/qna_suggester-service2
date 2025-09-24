from fastapi import FastAPI
from app.api.v1.analyze import router as analyze_router
from app.api.v1.uploads import router as upload_router
from app.api.v1.health import router as health_router

app = FastAPI(title="Resume Analyzer")
app.include_router(health_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")
app.include_router(analyze_router, prefix="/api/v1")
