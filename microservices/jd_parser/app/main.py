from fastapi import FastAPI, UploadFile, File
from io import BytesIO
import docx
import fitz
import re
import uuid
import boto3
import os
from dotenv import load_dotenv
from typing import Dict, Any

from transformers import pipeline
from app.infra.storage import put_object, get_object_bytes

# --------------------------
# INIT
# --------------------------
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
DYNAMO_TABLE = os.getenv("DYNAMO_TABLE_JD")   # create a table "job_descriptions"
S3_BUCKET = os.getenv("S3_BUCKET")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(DYNAMO_TABLE)

app = FastAPI(title="Job Description Parser", version="1.0")

# --------------------------
# HuggingFace Models
# --------------------------
ner_model = pipeline(
    "token-classification",
    model="dslim/bert-base-NER",
    aggregation_strategy="simple"
)

skill_model = pipeline(
    "token-classification",
    model="Jean-Baptiste/roberta-large-ner-english",
    aggregation_strategy="simple"
)

# --------------------------
# TEXT EXTRACTION HELPERS
# --------------------------
def extract_pdf(data: bytes) -> str:
    pdf = fitz.open(stream=data, filetype="pdf")
    return "\n".join(page.get_text() for page in pdf)

def extract_docx(data: bytes) -> str:
    doc = docx.Document(BytesIO(data))
    return "\n".join([p.text for p in doc.paragraphs]).strip()

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


# --------------------------
# PARSING HELPERS
# --------------------------
def extract_entities(text: str):
    raw = ner_model(text)
    entity_map = {"ORG": [], "LOC": [], "PERSON": [], "MISC": []}
    
    for t in raw:
        label = t["entity_group"]
        word = t["word"].replace("##", "").strip()
        if label in entity_map and word not in entity_map[label]:
            entity_map[label].append(word)
    return entity_map


def extract_skills(text: str):
    raw = skill_model(text)
    skills = sorted({t["word"].replace("##", "").strip() for t in raw})
    return skills


def extract_job_title(text: str):
    # basic heuristic: Job Title usually appears in first 3 lines
    lines = text.split("\n")
    if len(lines) > 0:
        first_line = lines[0]
        return first_line.strip() if len(first_line) < 80 else None
    return None


def extract_responsibilities(text: str):
    patterns = [
        r"(responsibilities|duties|what you will do)[:\-](.*?)(requirements|skills|qualification|experience)",
    ]
    for p in patterns:
        m = re.search(p, text.lower(), re.S)
        if m:
            return m.group(2).strip()
    return None


def extract_requirements(text: str):
    patterns = [
        r"(requirements|skills needed|qualification)[:\-](.*)",
    ]
    for p in patterns:
        m = re.search(p, text.lower(), re.S)
        if m:
            return m.group(2).strip()
    return None


# --------------------------
# MAIN JD PARSER
# --------------------------
def parse_jd_text(text: str) -> Dict[str, Any]:
    cleaned = clean_text(text)

    ents = extract_entities(cleaned)
    skills = extract_skills(cleaned)

    jd_data = {
        "job_title": extract_job_title(text),
        "organizations": ents["ORG"],
        "locations": ents["LOC"],
        "skills": skills,
        "responsibilities": extract_responsibilities(text),
        "requirements": extract_requirements(text),
        "raw_text": cleaned
    }

    return jd_data


# --------------------------
# FASTAPI ENDPOINT
# --------------------------
@app.post("/parse-jd")
async def parse_jd(file: UploadFile = File(...)):
    try:
        # store file in S3
        s3_key = put_object(file)
        data = get_object_bytes(s3_key)

        fname = file.filename.lower()

        # extract text
        if fname.endswith(".pdf"):
            text = extract_pdf(data)
        elif fname.endswith(".docx"):
            text = extract_docx(data)
        else:
            text = data.decode("utf-8", errors="ignore")

        parsed = parse_jd_text(text)

        jd_id = str(uuid.uuid4())

        item = {
            "jd_id": jd_id,
            "s3_key": s3_key,
            "parsed_data": parsed
        }

        table.put_item(Item=item)

        return {
            "status": "success",
            "jd_id": jd_id,
            "s3_key": s3_key,
            "parsed_data": parsed
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/")
def health():
    return {"message": "JD Parser Running"}
