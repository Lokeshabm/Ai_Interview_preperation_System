import os
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_interview_system.settings')

# Deterministic PBKDF2 hashes for 'admin123' and 'student123'
# Ensures session auth hash (get_session_auth_hash) matches across all multi-container Vercel lambdas
ADMIN_HASH = 'pbkdf2_sha256$1200000$aiinterviewadminsalt2026$OIIP7DRxm0TZBXkHdA/bBQlRjfHPceOPcmjctoPMX3s='
STUDENT_HASH = 'pbkdf2_sha256$1200000$aiinterviewstudentsalt2026$zHVBIDnHiHhYs/XS56i7ouWdXpZDbZ8E3r4S/FA/Xhg='

if os.getenv('VERCEL'):
    try:
        import django
        django.setup()
        from django.core.management import call_command
        from django.db import connection

        # Introspect existing database tables
        tables = connection.introspection.table_names()
        if 'auth_user' not in tables:
            call_command('migrate', interactive=False)

        from django.contrib.auth.models import User
        from interview.models import StudentProfile, InterviewSession, InterviewQuestion, InterviewAnswer, AnswerEvaluation, InterviewReport
        from django.utils import timezone

        # 1. Ensure Admin Superuser with deterministic hash
        admin_user = User.objects.filter(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password=ADMIN_HASH,
                first_name="System",
                last_name="Administrator",
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            admin_user.save()
            StudentProfile.objects.get_or_create(
                user=admin_user,
                defaults={
                    'phone_number': "+91 9999999999",
                    'college_name': "Engineering Faculty",
                    'degree': "Admin",
                    'department': "Computer Science"
                }
            )
        else:
            # Enforce identical hash and permissions across all lambdas
            if admin_user.password != ADMIN_HASH or not admin_user.is_staff or not admin_user.is_superuser:
                admin_user.password = ADMIN_HASH
                admin_user.is_staff = True
                admin_user.is_superuser = True
                admin_user.is_active = True
                admin_user.save()

        # 2. Ensure Demo Student User with deterministic hash
        student_user = User.objects.filter(username='student').first()
        if not student_user:
            student_user = User(
                username='student',
                email='student@example.com',
                password=STUDENT_HASH,
                first_name="Rahul",
                last_name="Sharma",
                is_active=True
            )
            student_user.save()
            StudentProfile.objects.get_or_create(
                user=student_user,
                defaults={
                    'phone_number': "+91 9876543210",
                    'college_name': "National Institute of Technology",
                    'degree': "B.Tech",
                    'department': "Computer Science & Engineering",
                    'bio': "Passionate computer science student preparing for full-stack and backend software engineering campus placements."
                }
            )

            # Pre-seed sample completed interview
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
        else:
            if student_user.password != STUDENT_HASH:
                student_user.password = STUDENT_HASH
                student_user.save()

    except Exception as exc:
        print("Vercel startup migration exception:", exc)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
app = application
