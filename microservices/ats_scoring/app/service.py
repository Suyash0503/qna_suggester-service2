from typing import Dict, Tuple, List
from sentence_transformers import SentenceTransformer, util
from rapidfuzz import fuzz
import numpy as np

# ---------------------------------------------------------
# Load semantic model ONCE at service startup (optimized)
# ---------------------------------------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# ---------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------

def normalize_list(values: List[str]) -> List[str]:
    """Normalize list values to lowercase clean tokens."""
    if not values:
        return []
    return [v.lower().strip() for v in values if isinstance(v, str) and len(v.strip()) > 1]


def semantic_similarity(text1: str, text2: str) -> float:
    """Compute semantic similarity using embeddings."""
    text1 = (text1 or "").strip()
    text2 = (text2 or "").strip()

    if not text1 or not text2:
        return 0.0

    emb1 = model.encode(text1, convert_to_tensor=True)
    emb2 = model.encode(text2, convert_to_tensor=True)
    sim = util.cos_sim(emb1, emb2).item()

    return float(max(sim * 100, 0))  # return % similarity


def multi_skill_semantic_match(resume_skills: List[str], jd_skills: List[str]) -> float:
    """Semantic comparison of skills (better than pure fuzzy match)."""
    if not resume_skills or not jd_skills:
        return 0.0

    resume_joined = ", ".join(resume_skills)
    jd_joined = ", ".join(jd_skills)

    return semantic_similarity(resume_joined, jd_joined)


def fuzzy_skill_match(resume_skills, jd_skills):
    """Fuzzy matching score using RapidFuzz."""
    if not resume_skills or not jd_skills:
        return 0.0

    scores = []
    for skill in jd_skills:
        best_score = max(
            fuzz.partial_ratio(skill.lower(), r.lower()) for r in resume_skills
        )
        scores.append(best_score)

    return float(np.mean(scores)) if scores else 0.0


def experience_score(resume_years, jd_years):
    """Compare experience using ratio comparison."""
    try:
        resume_years = float(resume_years)
        jd_years = float(jd_years)
    except:
        return 0.0

    if jd_years <= 0:
        return 100.0
    return float(min((resume_years / jd_years) * 100, 100))


def education_score(resume_edu, jd_edu):
    """Simple keyword-based matching."""
    resume_edu = normalize_list(resume_edu)
    jd_edu = normalize_list(jd_edu)

    if not resume_edu or not jd_edu:
        return 0.0

    for req in jd_edu:
        if any(req in r for r in resume_edu):
            return 100.0

    return 0.0


# ---------------------------------------------------------
#  MAIN MATCH FUNCTION
# ---------------------------------------------------------

def match(resume: Dict, jd: Dict) -> Tuple[int, Dict]:

    # Extract fields safely
    resume_text = resume.get("text", "")
    jd_text = jd.get("text", "")

    resume_skills = normalize_list(resume.get("skills", []))
    jd_skills = normalize_list(jd.get("required_skills", []))

    resume_years = resume.get("experience_years", 0)
    jd_years = jd.get("required_years", 0)

    resume_edu = resume.get("education", [])
    jd_edu = jd.get("required_education", [])

    # -----------------------------------------------------
    # Sub-scores
    # -----------------------------------------------------
    fuzzy_skill_score = fuzzy_skill_match(resume_skills, jd_skills)
    semantic_skill_score = multi_skill_semantic_match(resume_skills, jd_skills)

    # Combined skill score (industry formula)
    skill_score = (fuzzy_skill_score * 0.6) + (semantic_skill_score * 0.4)

    exp_score = experience_score(resume_years, jd_years)
    edu_score = education_score(resume_edu, jd_edu)
    context_score = semantic_similarity(resume_text, jd_text)

    # -----------------------------------------------------
    # Weighted ATS scoring (industry standard)
    # -----------------------------------------------------
    final_score = (
        skill_score * 0.45 +
        exp_score * 0.25 +
        edu_score * 0.10 +
        context_score * 0.20
    )

    # Normalize to 0–100
    final_score = float(max(min(final_score, 100), 0))

    # -----------------------------------------------------
    # Breakdown
    # -----------------------------------------------------
    breakdown = {
        "skills_match": f"{skill_score:.1f}%",
        "experience_match": f"{exp_score:.1f}%",
        "education_match": f"{edu_score:.1f}%",
        "context_match": f"{context_score:.1f}%",
        "summary": (
            "Excellent match! Highly aligned with job requirements." if final_score >= 80 else
            "Good match. Improving keywords & skills alignment will help." if final_score >= 60 else
            "Average match. Consider tailoring resume to job role." if final_score >= 40 else
            "Low match. Add missing skills and keywords."
        )
    }

    return round(final_score), breakdown
