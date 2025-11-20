# app/infra/db.py
import boto3, os, botocore
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ca-central-1")
TABLE = os.getenv("DYNAMO_TABLE", "resumes")

dynamo = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamo.Table(TABLE)


def _convert_floats(obj):
    """Recursively convert floats to Decimal for DynamoDB."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: _convert_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_floats(v) for v in obj]
    return obj


def save_analysis(resume_id: str, job_id: str, score: float, details: dict):
    """
    Store analysis results in DynamoDB.
    Key = resume_s3_key + job_s3_key
    """
    try:
        safe_score = Decimal(str(score)) if isinstance(score, float) else score
        safe_details = _convert_floats(details)

        table.put_item(
            Item={
                "resume_id": resume_id,
                "job_id": job_id,
                "score": safe_score,
                "details": safe_details
            }
        )
    except botocore.exceptions.ClientError as e:
        raise Exception(f"DynamoDB error: {e.response['Error']['Message']}")
