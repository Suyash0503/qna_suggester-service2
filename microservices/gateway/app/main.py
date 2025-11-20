from fastapi import FastAPI
from app.routes.health import router as health_router
from app.routes.resume import router as resume_router
from app.routes.job import router as job_router
from app.routes.analyze import router as analyze_router

app = FastAPI(
    title="Resume Analyzer Gateway",
    description="Main API Gateway for all microservices",
    version="1.0.0"
)

# Health
app.include_router(
    health_router,
    prefix="/health",
    tags=["Health"]
)

# Resume
app.include_router(
    resume_router,
    prefix="/resume",
    tags=["Resume"]
)

# Job
app.include_router(
    job_router,
    prefix="/job",
    tags=["Job Description"]
)

# Analyze (full pipeline)
app.include_router(
    analyze_router,
    prefix="/analyze",
    tags=["ATS Scoring & Analysis"]
)
#QNA Microservice
app.include_router(
    analyze_router,
    prefix="/qna", 
    tags=["QnA Suggester"]
)

@app.get("/")
def root():
    return {"status": "ok", "message": "Gateway is running"}

