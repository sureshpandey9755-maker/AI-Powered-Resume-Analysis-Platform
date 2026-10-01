from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import pymupdf as fitz
from docx import Document
import re
from datetime import datetime
import io
import os

from app.database.db import init_db, SessionLocal, ResumeRecord

app = FastAPI(title="AI Resume Analyzer API", version="1.0")

@app.on_event("startup")
def startup_db_client():
    if not os.path.exists("./data"):
        os.makedirs("./data")
    init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------
# Skill Categories & Taxonomy
# -----------------------------------
SKILL_CATEGORIES = {
    "Programming Languages": ["python", "java", "cpp", "c++", "c#", "javascript", "typescript", "r", "go", "ruby", "php", "swift", "kotlin", "scala"],
    "Databases": ["sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "oracle", "sqlite", "dynamodb", "snowflake"],
    "Machine Learning & AI": ["machine learning", "deep learning", "nlp", "scikit-learn", "tensorflow", "pytorch", "keras", "opencv", "computer vision", "llm", "generative ai", "langchain"],
    "Cloud Platforms": ["aws", "azure", "gcp", "google cloud", "heroku", "digitalocean"],
    "Frameworks & Libraries": ["streamlit", "fastapi", "flask", "django", "react", "angular", "vue", "pandas", "numpy", "matplotlib", "seaborn"],
    "DevOps & Infrastructure": ["docker", "kubernetes", "git", "github", "gitlab", "ci/cd", "jenkins", "terraform", "ansible", "linux"]
}

# -----------------------------------
# Helper Functions
# -----------------------------------
def extract_pdf_text(file_bytes):
    document = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in document:
        text += page.get_text()
    document.close()
    return text

def extract_docx_text(file_bytes):
    document = Document(io.BytesIO(file_bytes))
    text = ""
    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_skills(text: str) -> dict:
    text_lower = text.lower()
    extracted_skills = {}
    for category, skills in SKILL_CATEGORIES.items():
        found = []
        for skill in skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found.append(skill.capitalize() if len(skill) > 3 else skill.upper())
        if found:
            extracted_skills[category] = sorted(list(set(found)))
    return extracted_skills

def extract_experience_timeline(text: str) -> list:
    year_pattern = r'(\b20\d{2}\b)\s*[\-–to]\s*(\b20\d{2}\b|present|current)'
    matches = re.findall(year_pattern, text.lower())
    timeline = []
    current_year = datetime.now().year

    for match in matches:
        start_year = int(match[0])
        end_val = match[1].strip()
        end_year = current_year if end_val in ['present', 'current'] else int(end_val)
        duration = max(1, end_year - start_year)
        timeline.append({"start": start_year, "end": end_val, "duration_years": duration})

    return timeline

# -----------------------------------
# Endpoints
# -----------------------------------
@app.get("/")
def home():
    return {"message": "AI Resume Analyzer API with SQL DB is active!"}

@app.post("/analyze-resume/")
async def analyze_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename
    contents = await file.read()

    if filename.lower().endswith(".pdf"):
        resume_text = extract_pdf_text(contents)
    elif filename.lower().endswith(".docx"):
        resume_text = extract_docx_text(contents)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file.")

    categorized_skills = extract_skills(resume_text)
    timeline = extract_experience_timeline(resume_text)
    total_exp = sum([item["duration_years"] for item in timeline]) if timeline else 1

    skill_experience_list = []
    for category, skills in categorized_skills.items():
        for skill in skills:
            exp_str = f"{total_exp}+ years" if total_exp > 1 else "1 year"
            skill_experience_list.append({
                "Technology": skill,
                "Category": category,
                "Estimated Experience": exp_str
            })

    # Save to SQLite Database
    db_record = ResumeRecord(
        filename=filename,
        total_skills=len(skill_experience_list),
        total_experience=total_exp,
        categorized_skills=categorized_skills,
        skill_experience_list=skill_experience_list,
        extracted_text=resume_text
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    return {
        "id": db_record.id,
        "filename": filename,
        "total_skills_count": len(skill_experience_list),
        "total_experience_years": total_exp,
        "categorized_skills": categorized_skills,
        "skill_wise_experience": skill_experience_list,
        "extracted_text": resume_text
    }

@app.get("/history/")
def get_history(db: Session = Depends(get_db)):
    records = db.query(ResumeRecord).order_by(ResumeRecord.created_at.desc()).all()
    return records