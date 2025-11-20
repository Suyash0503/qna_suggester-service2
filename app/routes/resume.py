from fastapi import APIRouter, UploadFile, File, HTTPException
import httpx
from app.infra.storage import put_object_bytes

router = APIRouter(prefix="/resume", tags=["Resume Upload"])

# Resume Parser Microservice URL (Docker internal)
RESUME_PARSER_URL = "http://resume_parser:8001/parse"


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload resume → S3 → Resume Parser Microservice → return extracted data
    """

    try:
        # -----------------------------
        # 1. Read file bytes
        # -----------------------------
        file_bytes = await file.read()

        # -----------------------------
        # 2. Upload to S3
        # -----------------------------
        s3_key = put_object_bytes(file_bytes, file.filename)

        # -----------------------------
        # 3. Forward to Resume Parser MS
        # -----------------------------
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                RESUME_PARSER_URL,
                files={"file": (file.filename, file_bytes, file.content_type)}
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Resume Parser Microservice Failed"
            )

        parsed_resume = response.json().get("parsed_data", {})

        # -----------------------------
        # 4. Return clean response
        # -----------------------------
        return {
            "status": "success",
            "resume_s3_key": s3_key,
            "parsed_resume": parsed_resume
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume upload failed: {e}")
