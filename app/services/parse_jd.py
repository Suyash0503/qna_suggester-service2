# def run(jd_key: str) -> dict:
#     # TODO: implement job description parsing
#     return {
#         "text": "Sample extracted JD text",
#         "skills": ["Python", "AWS"]
#     }
# services/parse_jd.py
import io, os, re
import pdfplumber
from docx import Document
from typing import Dict, Any, List
from .storage import get_object_bytes
from .parse_resume import SKILL_BANK, EDU_KEYWORDS

def _ext_from_key(key: str) -> str:
    return os.path.splitext(key)[1].lower()

def _text_from_pdf(data: bytes) -> str:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

def _text_from_docx(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)

def _extract(text: str) -> Dict[str, Any]:
    lower = text.lower()

    # Pull a job title from the top line (naive)
    first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    job_title = first_line[:80]

    required_skills = sorted({s for s in SKILL_BANK if re.search(rf"\b{s}\b", lower)})
    # keywords (besides skills) — add domain words you care about
    KEYWORDS = {"lead", "senior", "cloud", "microservices", "api", "agile", "ci/cd"}
    keywords = sorted({k for k in KEYWORDS if re.search(rf"\b{k}\b", lower)})

    edu_required = [kw for kw in EDU_KEYWORDS if kw in lower]

    # required years
    req_years = 0
    m = re.search(r"(\d+)\s*\+?\s*years?", lower)
    if m:
        req_years = int(m.group(1))

    return {
        "job_title": job_title,
        "required_skills": required_skills,
        "keywords": keywords,
        "required_education": edu_required,
        "required_years": req_years,
        "text": text[:3000],
    }

def run(jd_key: str) -> Dict[str, Any]:
    data = get_object_bytes(jd_key)
    ext = _ext_from_key(jd_key)

    if ext == ".pdf":
        text = _text_from_pdf(data)
    elif ext == ".docx":
        text = _text_from_docx(data)
    else:
        text = data.decode("utf-8", errors="ignore")

    return _extract(text)
