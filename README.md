# AI Interview Preparation System

An Intelligent Resume-Based Voice and Video Interview Platform with Automatic Coding Assessment.

Built with **Python**, **Django Framework**, **Bootstrap 5**, **Google Gemini AI**, **Monaco Editor**, **Web MediaDevices API**, **Web Audio API**, **Web Speech API**, **Judge0 Sandbox**, and **ReportLab**.

---

## 🚀 Features

- **Student Authentication & Profile**:
  - Secure registration and login with email verification and password hashing.
  - Student profile management with college name, degree, department, phone, and bio.
- **Analytics Dashboard**:
  - 6 Key Performance Metric Badges: Total Interviews, Average Score, Technical Score, Coding Score, HR Score, and Growth / Improvement Rate.
  - Resume management and recent interview history with direct report and PDF download links.
- **Resume Upload & 12-Entity NLP Extraction**:
  - Drag-and-drop file upload for **PDF** and **DOCX** files (up to 5MB).
  - Multi-tier text extraction powered by PyMuPDF and python-docx.
  - Extracts 12 key entities: Student Name, Email, Phone, Education, Technical Skills, Programming Languages, Frameworks, Projects, Internships, Certifications, Work Experience, and Achievements.
  - Interactive skill tags and AI profile analysis summary.
- **AI Resume-Based Question Generator**:
  - Contextual Gemini AI prompt engineering strictly grounded in the candidate's actual uploaded resume.
  - 150+ offline fallback question bank across Python, Django, Java, JavaScript, React, SQL, DSA, HR, and coding challenges.
- **Live Video & Voice Interview Room**:
  - Live candidate webcam preview via `navigator.mediaDevices.getUserMedia`.
  - Real-time Web Audio API frequency visualizer drawing live sound waveforms on a canvas.
  - AI Voice Interviewer speaking questions aloud with `SpeechSynthesis` (TTS).
  - Speech-to-Text (`SpeechRecognition`) streaming candidate answers in real time with an editable fallback textarea.
  - Camera toggle, mic mute, repeat question, and pause/end controls.
  - Zero unauthorized recording: all media streams are stopped upon interview completion.
- **Automatic Coding Question Detection & Monaco Editor**:
  - Automatically detects coding questions (`is_coding: true`) and seamlessly transitions the workspace to **Monaco Code Editor** (VS Code interface).
  - Multi-language support: Python, JavaScript, Java, C++, and C.
  - **Run Code**: executes code against sample test cases via Judge0 REST API or an isolated local subprocess sandbox.
  - **Submit Solution**: evaluates against hidden test cases, calculates execution metrics (time, memory), and submits code for AI evaluation.
- **AI Answer Evaluation**:
  - Multi-criteria scoring (0 to 10 scale) evaluating technical correctness, depth, structure, time/space complexity, and clarity.
  - Generates strengths, weaknesses, actionable tips, recommended topics, model answers, and dynamic follow-up questioning.
- **Certified Performance Report & PDF Download**:
  - Chart.js 5-axis Radar Chart (Competency Matrix) and Bar Chart (Question-by-Question score distribution).
  - Question-by-question review with candidate answers, code submissions, AI feedback, and model answers.
  - Downloadable multi-page corporate **ReportLab PDF report** with candidate verification QR code.
- **Admin Dashboard**:
  - Full administrative management of student accounts, interview sessions, coding submissions, and question banks.

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, FontAwesome 6, Chart.js 4, Monaco Editor (VS Code).
- **Backend**: Python 3.13, Django Framework.
- **Database**: SQLite (default local development) / MySQL (configurable via `.env`).
- **Artificial Intelligence**: Google Gemini API (`gemini-1.5-flash`).
- **Resume Processing**: PyMuPDF (`fitz`), python-docx, PyPDF2.
- **Voice & Video**: Web Speech API (`SpeechSynthesis`, `SpeechRecognition`), MediaDevices API, Web Audio API.
- **Code Execution**: Judge0 API & Isolated Subprocess Sandbox.
- **PDF Generation**: ReportLab & qrcode.

---

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Lokeshabm/Ai_Interview_preperation_System.git
cd Ai_Interview_preperation_System
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in the configuration details:
```env
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Google Gemini API Key (from https://aistudio.google.com/)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Judge0 RapidAPI Key (optional, safe sandbox fallback enabled by default)
JUDGE0_API_KEY=
JUDGE0_API_HOST=judge0-ce.p.rapidapi.com
```

### 5. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Admin)
```bash
python manage.py createsuperuser
# Or run the automatic setup script:
python create_admin.py
```
*(Default admin: `admin` / `admin123`)*

### 7. Run Automated Tests
```bash
python manage.py test interview
```

### 8. Start the Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🧪 Testing Verification

The project includes an end-to-end automated test suite:
- `test_01_user_authentication_and_profile`: Registration, login, profile view.
- `test_02_resume_entity_extraction`: 12-entity extraction from resume text.
- `test_03_personalized_question_generation`: Resume-grounded questions & coding flag detection.
- `test_04_oral_answer_evaluation`: Multi-criteria 0-10 evaluation & feedback.
- `test_05_coding_execution_sandbox`: Python execution against test cases.
- `test_06_reportlab_pdf_generation`: Multi-page PDF generation with QR code.
- `test_07_api_interview_flow`: Full AJAX flow, coding submission, finish, and PDF download.

---

## 📄 License
This project is licensed under the MIT License.
