import json
from io import BytesIO
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from .models import (
    StudentProfile, Resume, ResumeAnalysis, InterviewSession,
    InterviewQuestion, InterviewAnswer, CodingSubmission,
    AnswerEvaluation, InterviewReport
)
from .resume_parser import heuristic_extract_entities, parse_resume_complete
from .ai_service import generate_personalized_questions, evaluate_answer_with_ai, generate_session_report_summary
from .code_executor import run_code_against_test_cases
from .pdf_generator import build_interview_report_pdf


class AIInterviewSystemTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = "test_student"
        self.password = "pass123456"
        self.email = "student@example.edu"
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
            first_name="Rahul",
            last_name="Verma"
        )
        self.profile = StudentProfile.objects.create(
            user=self.user,
            phone_number="+91 9876543210",
            college_name="National Institute of Engineering",
            degree="B.Tech",
            department="Computer Science & Engineering"
        )

    def test_01_user_authentication_and_profile(self):
        """Test registration, login, and profile accessibility."""
        login_success = self.client.login(username=self.username, password=self.password)
        self.assertTrue(login_success)

        # Check dashboard access
        resp = self.client.get('/dashboard/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Rahul")
        self.assertContains(resp, "National Institute of Engineering")

    def test_02_resume_entity_extraction(self):
        """Test extraction of the 12 required resume entities."""
        sample_resume_text = """
        Rahul Verma
        rahul.verma@example.edu | +91 9876543210
        Education:
        B.Tech in Computer Science, National Institute of Engineering, CGPA: 8.9
        Technical Skills:
        Python, Java, Django, MySQL, React, Git, Docker, REST API
        Projects:
        Farmer Marketplace Platform: A Django and MySQL web platform with payment gateway.
        AI Voice Agent: Speech recognition system with natural language response.
        Internships:
        Software Engineering Intern at TechCorp (3 months).
        Certifications:
        AWS Certified Cloud Practitioner, Python for Data Science.
        Achievements:
        Smart India Hackathon 2025 Finalist.
        """

        entities = heuristic_extract_entities(sample_resume_text, default_user=self.user)

        self.assertEqual(entities['student_name'], "Rahul Verma")
        self.assertEqual(entities['email'], "rahul.verma@example.edu")
        self.assertIn("Python", entities['technical_skills'])
        self.assertIn("Django", entities['technical_skills'])
        self.assertIn("MySQL", entities['technical_skills'])
        self.assertTrue(len(entities['projects']) >= 1)
        self.assertTrue(len(entities['education']) >= 1)
        self.assertTrue(len(entities['certifications']) >= 1)

    def test_03_personalized_question_generation(self):
        """Test generating resume-grounded questions including automatic coding question."""
        resume_data = {
            'student_name': "Rahul Verma",
            'technical_skills': ["Python", "Django", "MySQL", "React"],
            'programming_languages': ["Python", "Java"],
            'projects': ["Farmer Marketplace Platform"],
            'education': ["B.Tech CSE"]
        }

        questions = generate_personalized_questions(
            resume_data=resume_data,
            interview_type='mixed',
            difficulty='intermediate',
            count=5,
            target_role='Python Backend Developer'
        )

        self.assertEqual(len(questions), 5)
        # Verify at least one coding question is created with starter code
        has_coding = any(q['is_coding'] for q in questions)
        self.assertTrue(has_coding, "Mixed interview must generate at least one coding question.")

        coding_q = next(q for q in questions if q['is_coding'])
        self.assertIn('def ', coding_q['starter_code'])
        self.assertTrue(len(coding_q['test_cases']) > 0)

    def test_04_oral_answer_evaluation(self):
        """Test AI answer evaluation and follow-up generation."""
        question_text = "Explain the Django MVT architecture and how an HTTP request is handled."
        candidate_answer = """Django follows the Model-View-Template pattern. When an HTTP request arrives, 
        it passes through middleware and matches the URL pattern in urls.py. The matched view function processes 
        business logic, interacts with the Model via Django ORM to query the database, and renders data into 
        the Template to return an HttpResponse."""

        eval_res = evaluate_answer_with_ai(question_text, 'technical', candidate_answer, is_coding=False)

        self.assertGreaterEqual(eval_res['score'], 6.0)
        self.assertLessEqual(eval_res['score'], 10.0)
        self.assertTrue(len(eval_res['strengths']) > 0)
        self.assertTrue(len(eval_res['follow_up_question']) > 0)

    def test_05_coding_execution_sandbox(self):
        """Test sandbox code execution against test cases."""
        solution_code = """
import sys
def fib(n):
    res = [0, 1]
    while len(res) < n:
        res.append(res[-1] + res[-2])
    return " ".join(map(str, res[:n]))

if __name__ == "__main__":
    raw = sys.stdin.read().strip()
    n = int(raw if raw else 5)
    print(fib(n))
"""
        test_cases = [
            {'input': '5', 'expected_output': '0 1 1 2 3'},
            {'input': '1', 'expected_output': '0'}
        ]

        exec_res = run_code_against_test_cases(solution_code, 'python', test_cases)

        self.assertEqual(exec_res['status'], 'Accepted')
        self.assertEqual(exec_res['passed_test_cases'], 2)
        self.assertEqual(exec_res['total_test_cases'], 2)

    def test_06_reportlab_pdf_generation(self):
        """Test generation of the official ReportLab PDF performance report."""
        session = InterviewSession.objects.create(
            user=self.user,
            target_role="Full Stack Developer",
            interview_type="mixed",
            difficulty="intermediate",
            status="completed",
            overall_score=8.5,
            technical_score=9.0,
            coding_score=8.0,
            hr_score=8.5,
            project_score=8.5,
            communication_score=8.5
        )

        q1 = InterviewQuestion.objects.create(
            session=session,
            question_number=1,
            text="Explain Python OOP Concepts.",
            category="technical"
        )
        ans1 = InterviewAnswer.objects.create(
            question=q1,
            answer_text="OOP in Python involves Encapsulation, Inheritance, Polymorphism, and Abstraction."
        )
        AnswerEvaluation.objects.create(
            answer=ans1,
            score=8.5,
            strengths="Clear explanation of core pillars.",
            weaknesses="Could give a real-world class example.",
            improvements="Show code snippet of multiple inheritance.",
            recommended_topics=["Python MRO", "Metaclasses"]
        )

        report = InterviewReport.objects.create(
            session=session,
            readiness_level="Placement Ready (Excellent)",
            summary_notes="Candidate demonstrated solid technical fundamentals and articulate communication.",
            strengths_summary="Confident answers and solid grasp of OOP.",
            weaknesses_summary="Consider edge-case performance.",
            key_recommendations=["System Design", "Concurrency"]
        )

        pdf_buffer = build_interview_report_pdf(session, report)
        pdf_bytes = pdf_buffer.getvalue()

        # PDF files must start with %PDF
        self.assertTrue(pdf_bytes.startswith(b'%PDF'), "Generated document must be a valid PDF format.")
        self.assertGreater(len(pdf_bytes), 1000, "PDF size must contain content.")

    def test_07_api_interview_flow(self):
        """Test AJAX endpoints for answer submission, coding submission, finish, and PDF download."""
        self.client.login(username=self.username, password=self.password)

        session = InterviewSession.objects.create(
            user=self.user,
            target_role="Software Engineer",
            interview_type="mixed",
            difficulty="intermediate",
            status="in_progress"
        )

        # Question 1: Theoretical
        q1 = InterviewQuestion.objects.create(
            session=session,
            question_number=1,
            text="Explain the difference between a list and a tuple in Python.",
            category="technical",
            is_coding=False
        )

        # Question 2: Coding
        q2 = InterviewQuestion.objects.create(
            session=session,
            question_number=2,
            text="Write a program to check whether an integer is prime.",
            category="coding",
            is_coding=True,
            starter_code="def is_prime(n):\n    pass\n",
            test_cases=[{'input': '7', 'expected_output': 'PRIME'}]
        )

        # 1. Submit answer for Q1
        resp = self.client.post(
            f'/api/interview/{session.id}/submit-answer/',
            data=json.dumps({
                'question_id': q1.id,
                'answer_text': 'Lists are mutable whereas tuples are immutable. Tuples are also slightly more memory efficient.',
                'is_audio': True
            }),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'success')
        self.assertTrue(hasattr(q1, 'answer'))

        # 2. Run code sandbox for Q2
        run_resp = self.client.post(
            f'/api/interview/{session.id}/run-code/',
            data=json.dumps({
                'question_id': q2.id,
                'source_code': 'print("PRIME")',
                'language': 'python'
            }),
            content_type='application/json'
        )
        self.assertEqual(run_resp.status_code, 200)
        self.assertEqual(run_resp.json()['status'], 'Accepted')

        # 3. Submit code for Q2
        sub_resp = self.client.post(
            f'/api/interview/{session.id}/submit-code/',
            data=json.dumps({
                'question_id': q2.id,
                'source_code': 'print("PRIME")',
                'language': 'python'
            }),
            content_type='application/json'
        )
        self.assertEqual(sub_resp.status_code, 200)
        self.assertEqual(sub_resp.json()['status'], 'success')

        # 4. Finish interview
        finish_resp = self.client.post(
            f'/api/interview/{session.id}/finish/',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(finish_resp.status_code, 200)
        self.assertEqual(finish_resp.json()['status'], 'completed')

        # Refresh session from DB
        session.refresh_from_db()
        self.assertEqual(session.status, 'completed')
        self.assertIsNotNone(session.overall_score)
        self.assertTrue(hasattr(session, 'report'))

        # 5. Download PDF Report View
        pdf_resp = self.client.get(f'/interview/{session.id}/download-pdf/')
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp['Content-Type'], 'application/pdf')
        self.assertTrue(pdf_resp.content.startswith(b'%PDF'))
