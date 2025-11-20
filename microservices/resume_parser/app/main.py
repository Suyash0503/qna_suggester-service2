from fastapi import FastAPI, UploadFile, File
from io import BytesIO
import docx
import fitz
import re
from typing import Dict, Any, List
from collections import defaultdict

from transformers import pipeline
from app.infra.storage import put_object, get_object_bytes

app = FastAPI(title="Resume Parser (HuggingFace Edition)", version="5.0")

# --------------------------------------------------------
# 1) HuggingFace MODELS
# --------------------------------------------------------

# General NER (PER, ORG, LOC, MISC)
hf_ner = pipeline(
    "token-classification",
    model="dslim/bert-base-NER",
    aggregation_strategy="simple",
)

# Skills-like entities (we will still add manual parsing)
skill_ner = pipeline(
    "token-classification",
    model="Jean-Baptiste/roberta-large-ner-english",
    aggregation_strategy="simple",
)


# --------------------------------------------------------
# 2) TEXT EXTRACTION HELPERS
# --------------------------------------------------------
def extract_pdf(data: bytes) -> str:
    pdf = fitz.open(stream=data, filetype="pdf")
    return "\n".join(page.get_text() for page in pdf)


def extract_docx(data: bytes) -> str:
    doc = docx.Document(BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\x00", "")).strip()


# --------------------------------------------------------
# 3) SECTION DETECTION
# --------------------------------------------------------

SECTION_HEADERS = {
    "summary": [
        "summary",
        "professional summary",
        "profile",
        "about me",
        "career objective",
        "objective",
    ],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
    ],
    "education": [
        "education",
        "academic background",
        "qualifications",
        "academic qualifications",
    ],
    "projects": [
        "projects",
        "personal projects",
        "academic projects",
        "selected projects",
    ],
    "skills": [
        "skills",
        "technical skills",
        "key skills",
        "core competencies",
        "competencies",
    ],
    "certifications": [
        "certifications",
        "licenses",
        "certification",
        "licenses & certifications",
    ],
}


def split_sections(raw_text: str) -> Dict[str, str]:
    """
    Very simple heuristic section splitter:
    looks for lines that match known headings and groups following lines
    until next heading.
    """

    lines = [l.rstrip() for l in raw_text.splitlines()]
    sections: Dict[str, List[str]] = defaultdict(list)

    current_section = "other"
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        lower = stripped.lower()
        matched_section = None

        for sec_name, header_variants in SECTION_HEADERS.items():
            for header in header_variants:
                # exact header line (optionally with colon)
                pattern = rf"^{re.escape(header)}\s*:?\s*$"
                if re.match(pattern, lower):
                    matched_section = sec_name
                    break
            if matched_section:
                break

        if matched_section:
            current_section = matched_section
        else:
            sections[current_section].append(stripped)

    return {k: "\n".join(v).strip() for k, v in sections.items() if v}


# --------------------------------------------------------
# 4) NER + HEURISTICS
# --------------------------------------------------------

def extract_entities_all(text: str) -> Dict[str, List[str]]:
    """
    Run NER on the full text and group entities.
    dslim/bert-base-NER returns entity_group in {PER, ORG, LOC, MISC}.
    """
    entities = hf_ner(text)
    buckets: Dict[str, List[str]] = {"PER": [], "ORG": [], "LOC": [], "MISC": []}

    for item in entities:
        label = item["entity_group"]  # PER / ORG / LOC / MISC
        word = item["word"].replace("##", "").strip()
        if label in buckets and word:
            buckets[label].append(word)

    for key in buckets:
        buckets[key] = sorted(set(buckets[key]))

    return buckets


def extract_name(text: str) -> str | None:
    """
    Try to get the candidate name from the first few lines
    using NER (PER only).
    """
    # Only first ~5 lines, usually name + headline
    head = "\n".join(text.splitlines()[:5])
    ents = hf_ner(head)

    candidates: List[str] = []
    for e in ents:
        if e["entity_group"] == "PER":
            candidates.append(e["word"].replace("##", "").strip())

    if not candidates:
        return None

    # Often NER splits first + last; join consecutive tokens
    # Simple strategy: return joined unique tokens
    uniq = []
    for c in candidates:
        if c not in uniq:
            uniq.append(c)

    return " ".join(uniq)


def extract_emails_and_phone(text: str) -> Dict[str, str | None]:
    cleaned = clean(text)

    email_matches = re.findall(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", cleaned
    )
    phone_matches = re.findall(r"\+?\d[\d\s\-]{7,16}", cleaned)

    return {
        "email": email_matches[0] if email_matches else None,
        "phone": phone_matches[0] if phone_matches else None,
    }


def extract_experience_years(text: str) -> float:
    """
    Use simple numeric 'X years', 'Y months' detection.
    """
    years = re.findall(r"(\d+\.?\d*)\s+years?", text.lower())
    months = re.findall(r"(\d+)\s+months?", text.lower())

    total = sum(float(y) for y in years)

    if months:
        total += round(sum(int(m) for m in months) / 12.0, 2)

    return round(total, 2)


# --------------------------------------------------------
# 5) SKILLS EXTRACTION
# --------------------------------------------------------

def split_manual_skills(skills_text: str) -> List[str]:
    """
    Parse manual 'Skills' section lines like:
    'Python, AWS, Docker | React • FastAPI'
    """
    items: List[str] = []
    for line in skills_text.splitlines():
        # remove leading bullets
        line = re.sub(r"^[•\-\u2022]+\s*", "", line.strip())
        parts = re.split(r"[,\|/·•;\t]+", line)
        for p in parts:
            p = p.strip()
            if p:
                items.append(p)
    # normalize case a bit
    norm = sorted({p.strip() for p in items if len(p.strip()) > 1})
    return norm


def extract_skills(text: str, sections: Dict[str, str]) -> List[str]:
    """
    Combine manual parsing of the skills section + HF skill NER.
    """
    manual: List[str] = []
    if "skills" in sections:
        manual = split_manual_skills(sections["skills"])

    # HF skill extractions on full text
    ner_results = skill_ner(text)
    model_skills = {
        r["word"].replace("##", "").strip()
        for r in ner_results
        if len(r["word"].replace("##", "").strip()) > 1
    }

    all_skills = {s.strip() for s in manual} | {s for s in model_skills}
    return sorted(all_skills)


# --------------------------------------------------------
# 6) EDUCATION / CERTIFICATIONS / EXPERIENCE TEXT
# --------------------------------------------------------

DEGREE_PATTERNS = [
    r"bachelor of [a-zA-Z ]+",
    r"master of [a-zA-Z ]+",
    r"b\.?sc\.?",
    r"m\.?sc\.?",
    r"b\.?tech\.?",
    r"b\.?e\.?",
    r"m\.?tech\.?",
    r"ph\.?d\.?",
    r"mba",
]


def extract_education(sections: Dict[str, str]) -> List[str]:
    edu_text = sections.get("education", "")
    if not edu_text:
        return []

    lines = [l.strip() for l in edu_text.splitlines() if l.strip()]
    results: List[str] = []

    for ln in lines:
        lower = ln.lower()
        if any(re.search(p, lower) for p in DEGREE_PATTERNS):
            results.append(ln)

    # if nothing matched patterns, just return all edu lines as fallback
    if not results:
        results = lines

    return results


def extract_certifications(sections: Dict[str, str]) -> List[str]:
    cert_text = sections.get("certifications", "")
    if not cert_text:
        return []

    lines = [l.strip() for l in cert_text.splitlines() if l.strip()]
    # split lines by commas or bullets
    certs: List[str] = []
    for ln in lines:
        ln = re.sub(r"^[•\-\u2022]+\s*", "", ln)
        parts = re.split(r"[,\|/·;]+", ln)
        for p in parts:
            p = p.strip()
            if p:
                certs.append(p)

    return sorted(set(certs))


def extract_experience_text(sections: Dict[str, str]) -> List[str]:
    exp_text = sections.get("experience", "")
    if not exp_text:
        return []
    lines = [l.strip() for l in exp_text.splitlines() if l.strip()]
    return lines


def extract_projects(sections: Dict[str, str]) -> List[str]:
    proj_text = sections.get("projects", "")
    if not proj_text:
        return []
    lines = [l.strip() for l in proj_text.splitlines() if l.strip()]
    return lines


# --------------------------------------------------------
# 7) FINAL PARSER
# --------------------------------------------------------

def parse_resume_text(raw_text: str) -> Dict[str, Any]:
    """
    High-level orchestration:
    - section detection
    - NER
    - heuristics (name, email, phone, skills, experience, education, etc.)
    """

    # Keep original newlines for section splitting
    sections = split_sections(raw_text)

    # Cleaned for regex operations
    cleaned = clean(raw_text)

    # Global entities (persons, orgs, locations)
    entities = extract_entities_all(cleaned)

    # Name (first lines only)
    name = extract_name(raw_text)

    # Contact
    contact = extract_emails_and_phone(raw_text)

    # Skills
    skills = extract_skills(cleaned, sections)

    # Education / Certs / Projects / Experience text
    education = extract_education(sections)
    certifications = extract_certifications(sections)
    experience_lines = extract_experience_text(sections)
    project_lines = extract_projects(sections)

    # Experience duration (approx)
    experience_years = extract_experience_years(cleaned)

    # Summary = just take "summary" section if available
    summary = sections.get("summary")

    return {
        "name": name,
        "contact_info": contact,
        "summary": summary,
        "skills": skills,
        "organizations": entities.get("ORG", []),
        "locations": entities.get("LOC", []),
        "people_mentioned": entities.get("PER", []),
        "misc_entities": entities.get("MISC", []),
        "education": education,
        "certifications": certifications,
        "work_experience_lines": experience_lines,
        "project_lines": project_lines,
        "experience_years": experience_years,
        "sections_detected": list(sections.keys()),
        "raw_text": cleaned,
    }

#  FASTAPI ENDPOINTS

@app.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    try:
        # store in S3 using your existing infra helpers
        s3_key = put_object(file)
        data = get_object_bytes(s3_key)

        fname = file.filename.lower()
        if fname.endswith(".pdf"):
            text = extract_pdf(data)
        elif fname.endswith(".docx"):
            text = extract_docx(data)
        else:
            text = data.decode("utf-8", errors="ignore")

        parsed = parse_resume_text(text)

        return {
            "status": "success",
            "s3_key": s3_key,
            "parsed_data": parsed,
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/")
def health():
    return {"message": "Resume Parser API running (HF v5.0)"}
