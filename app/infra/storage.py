import boto3, os, uuid
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = "ca-central-1"
S3_BUCKET = os.getenv("S3_BUCKET", "ra222")

s3 = boto3.client("s3", region_name=AWS_REGION)


def put_object(file) -> str:
    """(Not used anymore for uploads)"""
    key = f"raw/{uuid.uuid4()}_{file.filename}"
    try:
        s3.upload_fileobj(file.file, S3_BUCKET, key)
        return key
    except (NoCredentialsError, ClientError) as e:
        raise Exception(f"S3 upload error: {str(e)}")


def put_object_bytes(file_bytes: bytes, filename: str) -> str:
    """
    Uploads bytes instead of UploadFile to avoid closed file errors.
    """
    key = f"raw/{uuid.uuid4()}_{filename}"
    try:
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=file_bytes)
        return key
    except (NoCredentialsError, ClientError) as e:
        raise Exception(f"S3 upload error: {str(e)}")


def get_object_bytes(key: str) -> bytes:
    """
    Download raw object bytes from S3.
    """
    try:
        resp = s3.get_object(Bucket=S3_BUCKET, Key=key)
        return resp["Body"].read()
    except ClientError as e:
        raise Exception(f"S3 download error: {str(e)}")
