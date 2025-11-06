
import boto3, os, uuid
from botocore.exceptions import NoCredentialsError, ClientError
from fastapi import UploadFile
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = "ca-central-1"
S3_BUCKET = os.getenv("S3_BUCKET", "dra222")

s3 = boto3.client("s3", region_name=AWS_REGION)

def put_object(file: UploadFile) -> str:
    """
    Uploads a file to S3 under 'raw/' prefix with a UUID.
    Returns the S3 key.
    """
    key = f"raw/{uuid.uuid4()}_{file.filename}"
    try:
        s3.upload_fileobj(file.file, S3_BUCKET, key)
        return key
    except (NoCredentialsError, ClientError) as e:
        raise Exception(f"S3 upload error: {str(e)}")

def generate_presigned_url(key: str, expiry: int = 3600) -> str:
    """
    Generates a presigned URL valid for 'expiry' seconds.
    """
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=expiry
    )

def get_object_bytes(key: str) -> bytes:
    """
    Download raw object bytes from S3.
    Used by parsers (resume & JD).
    """
    try:
        resp = s3.get_object(Bucket=S3_BUCKET, Key=key)
        return resp["Body"].read()
    except ClientError as e:
        raise Exception(f"S3 download error: {str(e)}")
