from typing import List

def generate(resume: str, jd: str) -> List[str]:
    """
    Generate simple context-based interview questions.
    Later can be upgraded to Hugging Face QG model.
    """
    questions = []
    jd_lower = jd.lower()
    resume_lower = resume.lower()

    if "python" in jd_lower:
        questions.append("Tell me about a project where you used Python.")
    if "aws" in jd_lower:
        questions.append("Have you deployed or worked with cloud services like AWS?")
    if "fastapi" in resume_lower:
        questions.append("Can you explain how you built APIs with FastAPI?")
    if "sql" in jd_lower or "database" in jd_lower:
        questions.append("Have you worked on database design or optimization?")

    return questions or ["Tell me about yourself."]

def evaluate(answers: List[str], jd: str = "") -> int:
    """
    Evaluate answers by checking if they mention relevant job description keywords.
    Returns a score between 0–100.
    """
    jd_lower = jd.lower()
    jd_keywords = [kw for kw in ["python", "aws", "fastapi", "docker", "sql"] if kw in jd_lower]

    score = 0
    for ans in answers:
        ans_lower = ans.lower()
        for kw in jd_keywords:
            if kw in ans_lower:
                score += 10

    return min(score, 100)
