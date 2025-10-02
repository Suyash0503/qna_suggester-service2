import boto3, os
from dotenv import load_dotenv
load_dotenv()

AWS_REGION = "ca-central-1"
TABLE = os.getenv("DYNAMO_TABLE", "resumes")

dynamo = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamo.Table(TABLE)

def save_analysis(resume_id: str, job_id: str, score: float, details: dict):
    table.put_item(
        Item={
            "resume_id": resume_id,
            "job_id": job_id,
            "score": score,
            "details": details
        }
    )

def get_analysis(resume_id: str, job_id: str):
    resp = table.get_item(Key={"resume_id": resume_id, "job_id": job_id})
    return resp.get("Item")
