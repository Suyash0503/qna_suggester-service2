from fastapi import APIRouter, UploadFile, File
from app.services.storage import put_object, generate_presigned_url

router = APIRouter(tags=["upload"])

@router.post("/upload/resume")
async def upload_resume(file: UploadFile = File(...)):
    # Save file to S3 (or local if modified later)
    key = await put_object(file)

    # Generate presigned URL valid for 1 hour
    url = generate_presigned_url(key, expiry=3600)

    return {
        "key": key,
        "url": url
    }
