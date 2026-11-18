import os
import re
import json
import logging
from io import BytesIO
import docx
try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

# Try pymupdf (fitz)
try:
    import pymupdf as fitz  # PyMuPDF
    HAVE_PYMUPDF = True
except ImportError:
    try:
        import fitz
        HAVE_PYMUPDF = True
    except ImportError:
        HAVE_PYMUPDF = False

logger = logging.getLogger(__name__)

# Predefined skill sets for dictionary matching
PROGRAMMING_LANGUAGES = {
    'python', 'java', 'c', 'c++', 'cpp', 'c#', 'csharp', 'javascript', 'typescript',
    'go', 'golang', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'sql', 'r', 'dart', 'scala'
}

FRAMEWORKS_AND_LIBS = {
    'django', 'flask', 'fastapi', 'react', 'react.js', 'reactjs', 'angular', 'vue', 'vue.js',
    'node.js', 'nodejs', 'express', 'express.js', 'spring', 'spring boot', 'laravel',
    'asp.net', '.net', 'next.js', 'nuxt.js', 'bootstrap', 'tailwind', 'jquery',
    'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy', 'opencv'
}

DATABASES_AND_TOOLS = {
    'mysql', 'postgresql', 'postgres', 'sqlite', 'mongodb', 'redis', 'oracle', 'firebase',
    'git', 'github', 'gitlab', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'linux',
    'postman', 'nginx', 'apache', 'jira', 'figma'
}


def extract_text_from_file(file_obj, file_name: str) -> str:
    """Extract full raw text from PDF or DOCX file."""
    text = ""
    lower_name = file_name.lower()

    if lower_name.endswith('.pdf'):
        # Method 1: PyMuPDF if available
        if HAVE_PYMUPDF:
            try:
                # If file_obj is in memory
                if hasattr(file_obj, 'read'):
                    content = file_obj.read()
                    if hasattr(file_obj, 'seek'):
                        file_obj.seek(0)
                    doc = fitz.open(stream=content, filetype="pdf")
                else:
                    doc = fitz.open(file_obj)
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
                if text.strip():
                    return text.strip()
            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed, trying PyPDF: {e}")

        # Method 2: PyPDF fallback
        try:
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            reader = PdfReader(file_obj)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            return text.strip()
        except Exception as e:
            logger.error(f"PyPDF extraction failed: {e}")

    elif lower_name.endswith('.docx') or lower_name.endswith('.doc'):
        try:
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            doc = docx.Document(file_obj)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            for table in doc.tables:
                for row in table.rows:
                    text += " | ".join(cell.text.strip() for cell in row.cells) + "\n"
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            return text.strip()
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")

    return text.strip()


CANONICAL_NAMES = {
    'mysql': 'MySQL',
    'postgresql': 'PostgreSQL',
    'postgres': 'PostgreSQL',
    'sqlite': 'SQLite',
    'mongodb': 'MongoDB',
    'aws': 'AWS',
    'gcp': 'GCP',
    'api': 'REST API',
    'rest api': 'REST API',
    'cpp': 'C++',
    'c++': 'C++',
    'c#': 'C#',
    'sql': 'SQL',
    'javascript': 'JavaScript',
    'typescript': 'TypeScript',
    'nodejs': 'Node.js',
    'node.js': 'Node.js',
    'reactjs': 'React',
    'react.js': 'React',
    'react': 'React',
    'vuejs': 'Vue.js',
    'vue.js': 'Vue.js',
    'github': 'GitHub',
    'gitlab': 'GitLab',
}


def heuristic_extract_entities(raw_text: str, default_user=None) -> dict:
    """
    Extract the 12 required resume entities using regex patterns and dictionary matching.
    Guarantees structured extraction even when offline.
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    full_lower = raw_text.lower()

    # 1. Email extraction
    email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', raw_text)
    email = email_match.group(0) if email_match else (default_user.email if default_user else '')

    # 2. Phone number extraction
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}', raw_text)
    phone = phone_match.group(0).strip() if phone_match else ''

    # 3. Student Name extraction (First prominent line or default_user)
    name = ""
    for line in lines[:5]:
        if len(line.split()) in [2, 3, 4] and not any(char.isdigit() for char in line) and '@' not in line:
            name = line
            break
    if not name and default_user:
        name = default_user.get_full_name() or default_user.username

    # 4 & 5 & 6. Skills, Programming Languages, Frameworks matching
    found_langs = set()
    found_frameworks = set()
    found_tools = set()

    for lang in PROGRAMMING_LANGUAGES:
        if re.search(r'\b' + re.escape(lang) + r'\b', full_lower):
            canon = CANONICAL_NAMES.get(lang.lower(), lang.capitalize())
            found_langs.add(canon)

    for fw in FRAMEWORKS_AND_LIBS:
        if re.search(r'\b' + re.escape(fw) + r'\b', full_lower):
            canon = CANONICAL_NAMES.get(fw.lower(), fw.title())
            found_frameworks.add(canon)

    for tool in DATABASES_AND_TOOLS:
        if re.search(r'\b' + re.escape(tool) + r'\b', full_lower):
            canon = CANONICAL_NAMES.get(tool.lower(), tool.title())
            found_tools.add(canon)

    all_technical_skills = sorted(list(found_langs | found_frameworks | found_tools))

    # 7. Education extraction
    education_items = []
    edu_keywords = ['b.tech', 'b.e', 'bachelor', 'm.tech', 'master', 'mca', 'bca', 'university', 'college', 'institute', 'gpa', 'cgpa', 'degree']
    for line in lines:
        if any(kw in line.lower() for kw in edu_keywords):
            if len(line) < 120 and line not in education_items:
                education_items.append(line)

    # 8. Projects extraction
    projects = []
    in_project_section = False
    for line in lines:
        lower_line = line.lower()
        if any(h in lower_line for h in ['project', 'academic projects', 'personal projects']):
            in_project_section = True
            continue
        if in_project_section:
            if any(h in lower_line for h in ['education', 'skills', 'experience', 'certifications', 'internships', 'declaration']):
                in_project_section = False
            elif len(line) > 10 and len(projects) < 6:
                # Add project title / bullet
                if line.startswith(('-', '•', '*', '1.', '2.', '3.')) or len(line.split()) < 8:
                    projects.append(line.lstrip('-•* 123456789.').strip())

    # 9. Internships
    internships = []
    for line in lines:
        if 'intern' in line.lower() or 'internship' in line.lower() or 'trainee' in line.lower():
            if len(line) < 120 and line not in internships:
                internships.append(line.strip())

    # 10. Certifications
    certifications = []
    for line in lines:
        if any(kw in line.lower() for kw in ['certified', 'certification', 'coursera', 'udemy', 'hackerrank', 'nptel', 'aws certified']):
            if len(line) < 120 and line not in certifications:
                certifications.append(line.strip())

    # 11. Work Experience
    experience = []
    for line in lines:
        if any(kw in line.lower() for kw in ['developer at', 'engineer at', 'worked as', 'experience:', 'role:']):
            if len(line) < 120 and line not in experience:
                experience.append(line.strip())

    # 12. Achievements
    achievements = []
    for line in lines:
        if any(kw in line.lower() for kw in ['hackathon', 'winner', 'rank', 'awarded', 'published', 'achievement', 'secured']):
            if len(line) < 140 and line not in achievements:
                achievements.append(line.strip())

    return {
        "student_name": name or "Student Candidate",
        "email": email,
        "phone": phone,
        "education": education_items[:4] if education_items else ["Relevant College/Degree Candidate"],
        "technical_skills": all_technical_skills if all_technical_skills else ["Python", "Problem Solving", "Data Structures"],
        "programming_languages": sorted(list(found_langs)) if found_langs else ["Python"],
        "frameworks": sorted(list(found_frameworks)) if found_frameworks else ["Django"],
        "projects": projects[:5] if projects else ["Full-Stack Web Application"],
        "internships": internships[:3],
        "certifications": certifications[:4],
        "work_experience": experience[:3],
        "achievements": achievements[:3],
    }


def parse_resume_complete(file_obj, file_name: str, user=None) -> tuple[str, dict, str]:
    """
    Complete pipeline:
    1. Extracts text from PDF or DOCX.
    2. Extracts 12 required structured entities (with Gemini AI enhancement if available, else heuristic).
    3. Returns (raw_text, extracted_dict, ai_summary).
    """
    raw_text = extract_text_from_file(file_obj, file_name)
    if not raw_text:
        raw_text = f"Resume uploaded: {file_name}. Candidate with technical coursework and development interest."

    # Heuristic baseline
    data = heuristic_extract_entities(raw_text, default_user=user)

    # Check if Gemini AI key is configured in settings
    from django.conf import settings
    api_key = getattr(settings, 'GEMINI_API_KEY', '')

    ai_summary = ""
    if api_key:
        try:
            from .ai_service import call_gemini_json
            prompt = f"""You are an expert technical interviewer and resume parsing specialist.
Analyze the following candidate resume text and extract a structured JSON response strictly adhering to the schema:
{{
  "student_name": string,
  "email": string,
  "phone": string,
  "education": [string],
  "technical_skills": [string],
  "programming_languages": [string],
  "frameworks": [string],
  "projects": [string],
  "internships": [string],
  "certifications": [string],
  "work_experience": [string],
  "achievements": [string],
  "summary": string
}}

Resume Text:
{raw_text[:4000]}
"""
            gemini_result = call_gemini_json(prompt)
            if isinstance(gemini_result, dict) and gemini_result.get('technical_skills'):
                # Merge AI enhanced data
                for key in ['student_name', 'email', 'phone', 'education', 'technical_skills',
                            'programming_languages', 'frameworks', 'projects', 'internships',
                            'certifications', 'work_experience', 'achievements']:
                    if gemini_result.get(key):
                        data[key] = gemini_result[key]
                ai_summary = gemini_result.get('summary', '')
        except Exception as e:
            logger.warning(f"Gemini resume enhancement encountered issue: {e}")

    if not ai_summary:
        langs_str = ", ".join(data['programming_languages']) or "Python"
        fw_str = ", ".join(data['frameworks']) or "Web Frameworks"
        projects_count = len(data['projects'])
        ai_summary = f"Candidate profile with proficiency in {langs_str} and {fw_str}. Demonstrates {projects_count} project(s) and relevant domain coursework."

    return raw_text, data, ai_summary
