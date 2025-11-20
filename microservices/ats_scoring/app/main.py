from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Set
import re

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

# ----------------------------------------------------------
# FASTAPI APP
# ----------------------------------------------------------
app = FastAPI(
    title="ATS Scoring Microservice (Advanced)",
    version="2.0",
    description="More realistic ATS-style scoring between resume and job description.",
)

# ----------------------------------------------------------
# HUGGINGFACE MODEL FOR SEMANTIC SIMILARITY
# ----------------------------------------------------------
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)


def embed_text(text: str) -> np.ndarray:
    """
    Sentence embedding using mean-pooled transformer outputs.
    """
    text = text.strip()
    if not text:
        return np.zeros(384, dtype=float)

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
    )

    with torch.no_grad():
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1).squeeze(0)

    return embeddings.cpu().numpy()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if not a.any() or not b.any():
        return 0.0
    num = float(np.dot(a, b))
    den = float(np.linalg.norm(a) * np.linalg.norm(b))
    if den == 0:
        return 0.0
    return num / den


# ----------------------------------------------------------
# TEXT NORMALIZATION & SIMPLE EXTRACTION HELPERS
# ----------------------------------------------------------

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9+\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    return normalize(text).split()


def jaccard_similarity(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union


# ----------------------------------------------------------
# SKILL BANK + SYNONYMS
# ----------------------------------------------------------

SKILL_BANK = {
    "python", "java", "c++", "c", "javascript", "typescript",
    "fastapi", "django", "flask", "react", "angular", "node",
    "sql", "nosql", "mongodb", "postgresql", "mysql", "redis",
    "aws", "amazon web services", "azure", "gcp",
    "docker", "kubernetes", "git", "linux",
    "ci/cd", "jenkins", "github actions", "terraform",
    "nlp", "natural language processing",
    "machine learning", "deep learning",
    "pandas", "numpy", "pytorch", "tensorflow",
}

# Map canonical skill → variants that should be treated as that skill
SKILL_SYNONYMS = {
    "aws": {"amazon web services", "aws cloud"},
    "ci/cd": {"cicd", "continuous integration", "continuous delivery"},
    "nlp": {"natural language processing"},
    "machine learning": {"ml", "machine-learning"},
    "deep learning": {"dl", "deep-learning"},
    "docker": {"containers", "containerization"},
}


def expand_with_synonyms(skills: Set[str]) -> Set[str]:
    expanded = set(skills)
    for canonical, variants in SKILL_SYNONYMS.items():
        if canonical in skills or (variants & skills):
            expanded.add(canonical)
            expanded |= variants
    return expanded


def extract_skills_from_text(text: str) -> Set[str]:
    norm = normalize(text)
    skills_found: Set[str] = set()

    for skill in SKILL_BANK:
        pattern = re.escape(skill)
        if re.search(rf"\b{pattern}\b", norm):
            skills_found.add(skill)

    # add synonyms if any canonical form appears
    skills_found = expand_with_synonyms(skills_found)
    return {s.lower() for s in skills_found}


def extract_years_experience(text: str) -> Optional[float]:
    """
    Very rough heuristic: pick highest "X years" mention.
    """
    norm = normalize(text)
    matches = re.findall(r"(\d+)\+?\s*years?", norm)
    if not matches:
        return None
    years = max(int(x) for x in matches)
    return float(years)


def extract_education_levels(text: str) -> Set[str]:
    norm = normalize(text)
    edu = set()
    if "bachelor" in norm or "bsc" in norm or "b.e" in norm or "btech" in norm:
        edu.add("bachelor")
    if "master" in norm or "msc" in norm or "m.e" in norm or "mtech" in norm:
        edu.add("master")
    if "phd" in norm or "ph.d" in norm or "doctorate" in norm:
        edu.add("phd")
    return edu


# ----------------------------------------------------------
# REQUEST / RESPONSE MODELS
# ----------------------------------------------------------

class ScoreRequest(BaseModel):
    # Required texts
    resume_text: str
    job_description_text: str

    # Optional structured data (can come from your parsers)
    resume_skills: Optional[List[str]] = None
    jd_skills: Optional[List[str]] = None
    jd_must_have_skills: Optional[List[str]] = None

    resume_years_experience: Optional[float] = None
    jd_min_years_experience: Optional[float] = None

    resume_education_levels: Optional[List[str]] = None  # e.g. ["bachelor","master"]
    jd_education_required: Optional[List[str]] = None     # e.g. ["bachelor"]

    job_title: Optional[str] = None        # JD title
    resume_titles: Optional[List[str]] = None  # titles from resume (e.g. ["software engineer","backend dev"])


class ScoreBreakdown(BaseModel):
    overall_score: float

    semantic_similarity: float
    skill_match_score: float
    experience_match_score: float
    title_match_score: float
    education_match_score: float
    keyword_overlap_score: float

    must_have_penalty: float

    matched_skills: List[str]
    missing_skills: List[str]
    missing_must_have_skills: List[str]


class ScoreResponse(BaseModel):
    match_score: float        # 0-100
    feedback: str
    breakdown: ScoreBreakdown


# ----------------------------------------------------------
# CORE SCORING LOGIC
# ----------------------------------------------------------

def compute_title_match(job_title: Optional[str], resume_titles: Set[str], resume_text_tokens: Set[str]) -> float:
    if not job_title:
        return 0.0

    job_title_norm = " ".join(tokenize(job_title))
    job_tokens = set(job_title_norm.split())

    # If resume_titles are provided, compare with best one
    scores = []
    if resume_titles:
        for t in resume_titles:
            t_norm = " ".join(tokenize(t))
            t_tokens = set(t_norm.split())
            scores.append(jaccard_similarity(job_tokens, t_tokens))

    # Also compare with overall resume tokens as fallback
    scores.append(jaccard_similarity(job_tokens, resume_text_tokens))

    return max(scores) if scores else 0.0


def compute_experience_match(resume_years: Optional[float],
                             jd_years: Optional[float]) -> float:
    if resume_years is None and jd_years is None:
        return 0.0
    if jd_years is None:
        # JD didn't specify → don't punish much
        return 0.7
    if resume_years is None:
        # JD has requirement, resume doesn't show → low score
        return 0.2

    if resume_years >= jd_years:
        return 1.0
    # partial match: ratio
    return max(0.1, resume_years / jd_years)


def compute_education_match(resume_edu: Set[str], jd_edu: Set[str]) -> float:
    if not jd_edu and not resume_edu:
        return 0.0
    if not jd_edu:
        # no requirement specified
        return 0.7
    if not resume_edu:
        return 0.2

    # If highest resume level >= highest jd level → 1
    levels = ["bachelor", "master", "phd"]
    def highest_level(s: Set[str]) -> int:
        for i, lvl in reversed(list(enumerate(levels))):
            if lvl in s:
                return i
        return -1

    r = highest_level(resume_edu)
    j = highest_level(jd_edu)

    if r >= j and r != -1:
        return 1.0
    if r == -1:
        return 0.2
    # slightly lower level
    return 0.5


def compute_ats_score(payload: ScoreRequest) -> ScoreBreakdown:
    # ------------- semantic similarity -------------
    resume_emb = embed_text(payload.resume_text)
    jd_emb = embed_text(payload.job_description_text)
    sem_sim = cosine_similarity(resume_emb, jd_emb)  # 0-1

    # ------------- skills -------------
    if payload.resume_skills:
        resume_skills = {s.lower() for s in payload.resume_skills}
    else:
        resume_skills = extract_skills_from_text(payload.resume_text)

    if payload.jd_skills:
        jd_skills = {s.lower() for s in payload.jd_skills}
    else:
        jd_skills = extract_skills_from_text(payload.job_description_text)

    # ensure synonyms expanded
    resume_skills = expand_with_synonyms(resume_skills)
    jd_skills = expand_with_synonyms(jd_skills)

    matched_skills = sorted(resume_skills & jd_skills)
    missing_skills = sorted(jd_skills - resume_skills)

    if jd_skills:
        skill_match = len(matched_skills) / len(jd_skills)
    else:
        skill_match = 0.0

    # ------------- keywords overlap -------------
    resume_tokens = set(tokenize(payload.resume_text))
    jd_tokens = set(tokenize(payload.job_description_text))
    kw_overlap = jaccard_similarity(resume_tokens, jd_tokens)

    # ------------- experience -------------
    resume_years = payload.resume_years_experience or extract_years_experience(payload.resume_text)
    jd_years = payload.jd_min_years_experience or extract_years_experience(payload.job_description_text)
    exp_match = compute_experience_match(resume_years, jd_years)

    # ------------- education -------------
    resume_edu = set(
        e.lower() for e in (payload.resume_education_levels or [])
    ) or extract_education_levels(payload.resume_text)

    jd_edu = set(
        e.lower() for e in (payload.jd_education_required or [])
    ) or extract_education_levels(payload.job_description_text)

    edu_match = compute_education_match(resume_edu, jd_edu)

    # ------------- title match -------------
    resume_titles = set(t.lower() for t in (payload.resume_titles or []))
    title_match = compute_title_match(payload.job_title, resume_titles, resume_tokens)

    # ------------- must-have penalty -------------
    jd_must_have = {s.lower() for s in (payload.jd_must_have_skills or [])}
    missing_must_have = sorted(jd_must_have - resume_skills)

    if jd_must_have:
        missed_ratio = len(missing_must_have) / len(jd_must_have)
        must_have_penalty = 0.3 * missed_ratio  # up to -0.3
    else:
        must_have_penalty = 0.0

    # ------------- weighted final score -------------
    # You can tune weights as you like
    w_sem = 0.35
    w_skill = 0.35
    w_exp = 0.10
    w_title = 0.10
    w_edu = 0.05
    w_kw = 0.05

    base_score = (
        w_sem * sem_sim +
        w_skill * skill_match +
        w_exp * exp_match +
        w_title * title_match +
        w_edu * edu_match +
        w_kw * kw_overlap
    )

    final_score = base_score - must_have_penalty
    final_score = max(0.0, min(1.0, final_score))

    return ScoreBreakdown(
        overall_score=round(final_score * 100, 2),
        semantic_similarity=round(sem_sim * 100, 2),
        skill_match_score=round(skill_match * 100, 2),
        experience_match_score=round(exp_match * 100, 2),
        title_match_score=round(title_match * 100, 2),
        education_match_score=round(edu_match * 100, 2),
        keyword_overlap_score=round(kw_overlap * 100, 2),
        must_have_penalty=round(must_have_penalty * 100, 2),
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        missing_must_have_skills=missing_must_have,
    )


def generate_feedback(breakdown: ScoreBreakdown) -> str:
    score = breakdown.overall_score

    if score >= 80:
        level = "Excellent match"
    elif score >= 65:
        level = "Strong match"
    elif score >= 50:
        level = "Moderate match"
    else:
        level = "Low match"

    parts = [
        f"{level} (ATS score {score}%).",
        f" Semantic similarity: {breakdown.semantic_similarity}%.",
        f" Skill match: {breakdown.skill_match_score}%.",
        f" Experience alignment: {breakdown.experience_match_score}%.",
        f" Title match: {breakdown.title_match_score}%.",
        f" Education match: {breakdown.education_match_score}%.",
    ]

    if breakdown.missing_must_have_skills:
        missing = ", ".join(breakdown.missing_must_have_skills[:8])
        extra = " …" if len(breakdown.missing_must_have_skills) > 8 else ""
        parts.append(f" Missing MUST-HAVE skills: {missing}{extra}. This significantly lowers the score.")
    elif breakdown.missing_skills:
        missing = ", ".join(breakdown.missing_skills[:8])
        extra = " …" if len(breakdown.missing_skills) > 8 else ""
        parts.append(f" Consider adding or highlighting these skills (if you have them): {missing}{extra}.")

    return "".join(parts)


# ----------------------------------------------------------
# API ENDPOINTS
# ----------------------------------------------------------

@app.post("/score", response_model=ScoreResponse)
async def score_resume(payload: ScoreRequest) -> ScoreResponse:
    """
    Compute ATS score between a resume and a job description.

    You can call it in two ways:

    1) Simple mode (only texts):
    {
      "resume_text": "...",
      "job_description_text": "...",
      "job_title": "Software Engineer"
    }

    2) Advanced mode (from your parsers):
    {
      "resume_text": "...",
      "job_description_text": "...",
      "resume_skills": [...],
      "jd_skills": [...],
      "jd_must_have_skills": [...],
      "resume_years_experience": 2.5,
      "jd_min_years_experience": 3,
      "resume_education_levels": ["bachelor"],
      "jd_education_required": ["bachelor"],
      "job_title": "Backend Software Engineer",
      "resume_titles": ["Software Engineer", "Backend Developer"]
    }
    """
    breakdown = compute_ats_score(payload)
    feedback = generate_feedback(breakdown)

    return ScoreResponse(
        match_score=breakdown.overall_score,
        feedback=feedback,
        breakdown=breakdown,
    )


@app.get("/")
def health():
    return {"message": "ATS Scoring Microservice running"}
