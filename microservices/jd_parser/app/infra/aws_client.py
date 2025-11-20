import boto3
import os
import dotenv 

AWS_REGION = os.getenv("ca-central-1")
S3_BUCKET = os.getenv("ra222")
DYNAMO_TABLE =os.getenv("resumes")

# s3_client = boto3.client("s3", region_name = ca-central-1)
# dynamo_client = boto3.resource("dynamodb", region_name = )
# dynamo_table = 