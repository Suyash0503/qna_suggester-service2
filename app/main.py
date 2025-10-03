
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.gateway import gateway

# Initialize FastAPI app
app = FastAPI(
    title="Resume Analyzer API",
    description="Backend service for ATS scoring, suggestions, and job preparation.",
    version="1.0.0",
)

# Middleware (for CORS)
# Restrict allow_origins in production to only your frontend domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach the gateway (facade) under /api/v1
app.include_router(gateway, prefix="/api/v1")

# Root endpoint (simple health check/info)
@app.get("/", tags=["root"])
def root():
    return {"message": "Resume Analyzer API is running"}
