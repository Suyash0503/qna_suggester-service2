from fastapi import APIRouter, UploadFile, File
from app.models.schemas import ResumeUploadResponse
from app.services.storage import put_object, generate_presigned_url

router = APIRouter(tags=["upload"])

@router.post("/upload/resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    key = put_object(file)
    url = generate_presigned_url(key, expiry=3600)
    return {"key": key, "url": url}
