import boto3, os
from botocore.exceptions import NoCredentialsError
from fastapi import UploadFile
from dotenv import load_dotenv
load_dotenv()
print("DEBUG AWS_ACCESS_KEY_ID:", os.getenv("AWS_ACCESS_KEY_ID"))
print("DEBUG AWS_SECRET_ACCESS_KEY:", os.getenv("AWS_SECRET_ACCESS_KEY"))


AWS_REGION = "ca-central-1"
S3_BUCKET = os.getenv("S3_BUCKET", "dra222")

s3 = boto3.client("s3", region_name=AWS_REGION)

async def put_object(file: UploadFile):
    key = f"raw/{file.filename}"
    try:
        s3.upload_fileobj(file.file, S3_BUCKET, key)
        return key
    except NoCredentialsError:
        raise Exception("AWS credentials not found")

def generate_presigned_url(key: str, expiry=3600):
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=expiry
    )
