import re
from datetime import datetime

# Technical Skills Dictionary Categorization
SKILL_CATEGORIES = {
    "Programming Languages": ["python", "java", "cpp", "c++", "c#", "javascript", "typescript", "r", "go", "ruby", "php", "swift", "kotlin", "scala"],
    "Databases": ["sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "oracle", "sqlite", "dynamodb", "snowflake"],
    "Machine Learning & AI": ["machine learning", "deep learning", "nlp", "scikit-learn", "tensorflow", "pytorch", "keras", "opencv", "computer vision", "llm", "generative ai", "langchain"],
    "Cloud Platforms": ["aws", "azure", "gcp", "google cloud", "heroku", "digitalocean"],
    "Frameworks & Libraries": ["streamlit", "fastapi", "flask", "django", "react", "angular", "vue", "pandas", "numpy", "matplotlib", "seaborn"],
    "DevOps & Infrastructure": ["docker", "kubernetes", "git", "github", "gitlab", "ci/cd", "jenkins", "terraform", "ansible", "linux"]
}

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
        
        if end_val in ['present', 'current']:
            end_year = current_year
        else:
            end_year = int(end_val)

        duration = max(1, end_year - start_year)
        timeline.append({
            "start": start_year,
            "end": "Present" if end_val in ['present', 'current'] else end_year,
            "duration_years": duration
        })

    return timeline

def map_skill_experience(text: str, extracted_skills: dict):
    timeline = extract_experience_timeline(text)
    total_exp = sum([item["duration_years"] for item in timeline]) if timeline else 1

    skill_experience_list = []

    for category, skills in extracted_skills.items():
        for skill in skills:
            exp_str = f"{total_exp}+ years" if total_exp > 1 else "1 year"
            skill_experience_list.append({
                "Technology": skill,
                "Category": category,
                "Estimated Experience": exp_str
            })

    return skill_experience_list, total_exp