import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_interview_system.settings')

application = get_wsgi_application()
app = application

# Automatic migration & setup on Vercel Serverless startup
if os.getenv('VERCEL'):
    try:
        from django.core.management import call_command
        from django.db import connection

        # Introspect existing database tables
        tables = connection.introspection.table_names()
        if 'auth_user' not in tables:
            call_command('migrate', interactive=False)

        from django.contrib.auth.models import User
        from interview.models import StudentProfile, Resume, ResumeAnalysis, InterviewSession, InterviewQuestion, InterviewAnswer, AnswerEvaluation, InterviewReport
        from django.utils import timezone

        # 1. Ensure Admin Superuser
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            admin_user.first_name = "System"
            admin_user.last_name = "Administrator"
            admin_user.save()

            StudentProfile.objects.create(
                user=admin_user,
                phone_number="+91 9999999999",
                college_name="Engineering Faculty",
                degree="Admin",
                department="Computer Science"
            )

        # 2. Ensure Demo Student User
        if not User.objects.filter(username='student').exists():
            student_user = User.objects.create_user(
                username='student',
                email='student@example.com',
                password='student123',
                first_name="Rahul",
                last_name="Sharma"
            )
            StudentProfile.objects.create(
                user=student_user,
                phone_number="+91 9876543210",
                college_name="National Institute of Technology",
                degree="B.Tech",
                department="Computer Science & Engineering",
                bio="Passionate computer science student preparing for full-stack and backend software engineering campus placements."
            )

            # Pre-seed sample completed interview for immediate dashboard analytics
            session = InterviewSession.objects.create(
                user=student_user,
                target_role="Full Stack Python Developer",
                interview_type="mixed",
                difficulty="intermediate",
                total_questions_target=5,
                duration_minutes=30,
                status="completed",
                overall_score=8.5,
                technical_score=9.0,
                coding_score=8.0,
                hr_score=8.5,
                project_score=8.5,
                communication_score=8.5,
                started_at=timezone.now(),
                completed_at=timezone.now()
            )

            q1 = InterviewQuestion.objects.create(
                session=session,
                question_number=1,
                text="Explain Python OOP Concepts and the difference between deep copy and shallow copy.",
                category="technical",
                is_coding=False
            )
            ans1 = InterviewAnswer.objects.create(
                question=q1,
                answer_text="OOP in Python involves Encapsulation, Inheritance, Polymorphism, and Abstraction. Shallow copy duplicates the object reference, while deep copy recursively duplicates all nested objects.",
                is_audio=True
            )
            AnswerEvaluation.objects.create(
                answer=ans1,
                score=8.5,
                technical_correctness=9.0,
                relevance=8.5,
                clarity=8.5,
                strengths="Clear explanation of core OOP pillars and exact distinction between copy mechanisms.",
                weaknesses="Could give a quick practical code example.",
                improvements="State memory addresses using id() when explaining shallow copies.",
                recommended_topics=["Memory Management", "Python Copy Module"],
                model_answer="Encapsulation bundles data and methods; deep copy copies nested objects independently."
            )

            InterviewReport.objects.create(
                session=session,
                readiness_level="Placement Ready (Excellent)",
                summary_notes="Candidate demonstrated solid technical fundamentals, articulate communication, and structured problem-solving.",
                strengths_summary="Confident responses, clear articulation, and solid understanding of OOP.",
                weaknesses_summary="Consider edge-case analysis in complex production constraints.",
                key_recommendations=["System Design", "Concurrency", "STAR Method"]
            )

    except Exception as exc:
        print("Vercel startup migration exception:", exc)
