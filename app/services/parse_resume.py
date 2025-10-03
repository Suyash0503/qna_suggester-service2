# services/parse_resume.py
import io, os, re
import pdfplumber
from docx import Document
from typing import Dict, Any
from .storage import get_object_bytes
from .constants import SKILL_BANK, EDU_KEYWORDS  # moved out for reuse

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(?:(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4})")

def _ext_from_key(key: str) -> str:
    return os.path.splitext(key)[1].lower()

def _text_from_pdf(data: bytes) -> str:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return "\n".join((page.extract_text() or "").strip() for page in pdf.pages)

def _text_from_docx(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)

def _extract_fields(text: str) -> Dict[str, Any]:
    text_lower = text.lower()

    email = EMAIL_RE.search(text)
    phone = PHONE_RE.search(text)

    # naive name guess: first non-empty line that's not email/phone
    first_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    name = None
    for ln in first_lines[:5]:
        if not EMAIL_RE.search(ln) and not PHONE_RE.search(ln) and len(ln.split()) <= 6:
            if ln.lower() not in {"resume", "cv", "curriculum vitae"}:  # extra guard
                name = ln
                break

    # skills
    skills = sorted({s for s in SKILL_BANK if re.search(rf"\b{s}\b", text_lower)})

    # years of exp
    exp_years = 0
    m = re.search(r"(?:at least|min(?:imum) of)?\s*(\d+)\s*\+?\s*years?", text_lower)
    if m:
        exp_years = int(m.group(1))

    # education
    educ = [kw for kw in EDU_KEYWORDS if kw in text_lower]

    return {
        "name": name or "",
        "email": email.group(0) if email else "",
        "phone": phone.group(0) if phone else "",
        "skills": skills,
        "experience_years": exp_years,
        "education": educ,
        "text": text[:3000]  # cap for Dynamo item size sanity
    }

def run(resume_key: str) -> Dict[str, Any]:
    data = get_object_bytes(resume_key)
    ext = _ext_from_key(resume_key)

    if ext == ".pdf":
        text = _text_from_pdf(data)
    elif ext == ".docx":
        text = _text_from_docx(data)
    else:
        # fallback
        try:
            text = data.decode("utf-8", errors="ignore")
        except Exception:
            text = ""

    return _extract_fields(text)
