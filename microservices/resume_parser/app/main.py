from fastapi import FastAPI, UploadFile, File
from io import BytesIO
import docx, fitz, re
from storage import put_object, get_object_bytes


app = FastAPI(title="Resume Parser Microservice", version="1.1")

@app.get("/")
def health():
    return {"status": "Resume Parser service running"}


@app.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    try:
        # Reading file content
        s3_key = put_object(file)
        content = get_object_bytes(s3_key)
        text = ""

        if file.filename.endswith(".docx"):
            doc = docx.Document(BytesIO(content))
            text = "\n".join([p.text for p in doc.paragraphs])
        elif file.filename.endswith(".pdf"):
            pdf = fitz.open(stream=content, filetype="pdf")
            text = "\n".join([page.get_text() for page in pdf])
        else:
            text = content.decode("utf-8", errors="ignore")

        text_lower = text.lower()

        SKILL_KEYWORDS = [
            "python", "java", "c++", "aws", "docker", "kubernetes", "linux", "sql",
            "fastapi", "flask", "django", "html", "css", "javascript", "react",
            "node", "git", "rest", "microservices", "machine learning", "tensorflow",
            "pandas", "numpy", "matlab", "azure", "gcp"
        ]
        found_skills = sorted(list({s for s in SKILL_KEYWORDS if s in text_lower}))

        edu_keywords = {
            "B.Tech": ["b.tech", "bachelor", "bachelors"],
            "M.Eng": ["m.eng", "master", "m.tech", "postgraduate"],
            "PhD": ["phd", "doctorate"]
        }
        found_edu = []
        for degree, variants in edu_keywords.items():
            if any(v in text_lower for v in variants):
                found_edu.append(degree)
        if not found_edu:
            found_edu = ["Other"]

        years = re.findall(r"20\d{2}", text)
        if years:
            min_year, max_year = min(map(int, years)), max(map(int, years))
            experience_years = max(1, max_year - min_year)
        else:
            experience_years = 2 

        clean_text = re.sub(r"\s+", " ", text.strip())
        snippet = clean_text[:1500] 

        return {
            "status": "success",
            "s3_key": s3_key,
            "parsed_data": {
                "text": text[:1000],
                "skills": found_skills,
                "education": found_edu,
                "experience_years": experience_years
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
