import os
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Avg

from .models import (
    StudentProfile, Resume, ResumeAnalysis, InterviewSession,
    InterviewQuestion, InterviewAnswer, CodingSubmission,
    AnswerEvaluation, InterviewReport
)
from .forms import StudentRegistrationForm, StudentProfileForm, ResumeUploadForm, InterviewSetupForm
from .resume_parser import parse_resume_complete
from .ai_service import generate_personalized_questions, evaluate_answer_with_ai, generate_session_report_summary
from .code_executor import run_code_against_test_cases
from .pdf_generator import build_interview_report_pdf
from .questions_bank import QUESTIONS_BANK, CODING_CHALLENGES

logger = logging.getLogger(__name__)


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            full_name = form.cleaned_data['full_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            phone_number = form.cleaned_data['phone_number']
            college_name = form.cleaned_data['college_name']
            degree = form.cleaned_data['degree']
            department = form.cleaned_data['department']

            # Split full name into first and last
            parts = full_name.strip().split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ''

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Create StudentProfile
            StudentProfile.objects.create(
                user=user,
                phone_number=phone_number,
                college_name=college_name,
                degree=degree,
                department=department
            )

            messages.success(request, "Registration successful! Please log in with your credentials.")
            return redirect('login')
    else:
        form = StudentRegistrationForm()

    return render(request, 'interview/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    next_url = request.GET.get('next') or request.POST.get('next') or 'dashboard'

    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Allow login via username or email
        user_obj = None
        if '@' in username_or_email:
            matched = User.objects.filter(email__iexact=username_or_email).first()
            if matched:
                user_obj = authenticate(request, username=matched.username, password=password)
        else:
            user_obj = authenticate(request, username=username_or_email, password=password)

        if user_obj is not None:
            login(request, user_obj)
            # Ensure profile exists
            StudentProfile.objects.get_or_create(user=user_obj)
            messages.success(request, f"Welcome back, {user_obj.first_name or user_obj.username}!")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username/email or password.")

    return render(request, 'interview/login.html', {'next_url': next_url})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


@login_required
def profile_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.save()
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = StudentProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })

    return render(request, 'interview/profile.html', {'form': form, 'profile': profile})


@login_required
def dashboard_view(request):
    user = request.user
    sessions = InterviewSession.objects.filter(user=user, status='completed').order_by('-completed_at')

    total_interviews = sessions.count()
    avg_score = sessions.aggregate(Avg('overall_score'))['overall_score__avg'] or 0.0
    avg_technical = sessions.aggregate(Avg('technical_score'))['technical_score__avg'] or 0.0
    avg_coding = sessions.aggregate(Avg('coding_score'))['coding_score__avg'] or 0.0
    avg_hr = sessions.aggregate(Avg('hr_score'))['hr_score__avg'] or 0.0

    # Calculate improvement percentage
    improvement_rate = 0.0
    if total_interviews >= 2:
        recent_two = list(sessions[:2])
        score_new = recent_two[0].overall_score or 0.0
        score_old = recent_two[1].overall_score or 0.0
        if score_old > 0:
            improvement_rate = round(((score_new - score_old) / score_old) * 100, 1)

    # Latest resumes
    resumes = Resume.objects.filter(user=user).order_by('-uploaded_at')[:3]
    recent_sessions = sessions[:5]

    context = {
        'total_interviews': total_interviews,
        'avg_score': round(avg_score, 1),
        'avg_technical': round(avg_technical, 1),
        'avg_coding': round(avg_coding, 1),
        'avg_hr': round(avg_hr, 1),
        'improvement_rate': improvement_rate,
        'recent_sessions': recent_sessions,
        'resumes': resumes,
        'user_profile': getattr(user, 'profile', None),
    }
    return render(request, 'interview/dashboard.html', context)


@login_required
def upload_resume_view(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['resume_file']
            target_role = form.cleaned_data['target_role']
            ext = 'pdf' if uploaded_file.name.lower().endswith('.pdf') else 'docx'

            # Parse resume content
            raw_text, extracted_data, ai_summary = parse_resume_complete(
                uploaded_file, uploaded_file.name, user=request.user
            )

            # Save Resume model
            resume = Resume.objects.create(
                user=request.user,
                file=uploaded_file,
                file_name=uploaded_file.name,
                file_type=ext,
                raw_text=raw_text
            )

            # Save ResumeAnalysis
            ResumeAnalysis.objects.create(
                resume=resume,
                extracted_data=extracted_data,
                ai_summary=ai_summary
            )

            messages.success(request, f"Resume '{uploaded_file.name}' analyzed successfully!")
            return redirect('resume_analysis', resume_id=resume.id)
    else:
        form = ResumeUploadForm()

    existing_resumes = Resume.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'interview/upload_resume.html', {'form': form, 'existing_resumes': existing_resumes})


@login_required
def resume_analysis_view(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    analysis = getattr(resume, 'analysis', None)

    if not analysis:
        # Generate analysis if missing
        raw_text, extracted_data, ai_summary = parse_resume_complete(resume.file, resume.file_name, user=request.user)
        analysis = ResumeAnalysis.objects.create(
            resume=resume,
            extracted_data=extracted_data,
            ai_summary=ai_summary
        )

    return render(request, 'interview/resume_analysis.html', {
        'resume': resume,
        'analysis': analysis,
        'data': analysis.extracted_data
    })


@login_required
def select_interview_view(request):
    resumes = Resume.objects.filter(user=request.user).order_by('-uploaded_at')

    if request.method == 'POST':
        form = InterviewSetupForm(request.POST)
        if form.is_valid():
            target_role = form.cleaned_data['target_role']
            interview_type = form.cleaned_data['interview_type']
            difficulty = form.cleaned_data['difficulty']
            total_questions = int(form.cleaned_data['total_questions'])
            duration_minutes = int(form.cleaned_data['duration_minutes'])
            resume_id = form.cleaned_data.get('resume_id')

            resume = None
            extracted_data = {}
            if resume_id:
                resume = Resume.objects.filter(id=resume_id, user=request.user).first()
                if resume and hasattr(resume, 'analysis'):
                    extracted_data = resume.analysis.extracted_data
            elif resumes.exists():
                resume = resumes.first()
                if hasattr(resume, 'analysis'):
                    extracted_data = resume.analysis.extracted_data

            # Generate questions grounded in resume
            questions_payload = generate_personalized_questions(
                resume_data=extracted_data,
                interview_type=interview_type,
                difficulty=difficulty,
                count=total_questions,
                target_role=target_role
            )

            # Create InterviewSession
            session = InterviewSession.objects.create(
                user=request.user,
                resume=resume,
                target_role=target_role,
                interview_type=interview_type,
                difficulty=difficulty,
                total_questions_target=len(questions_payload),
                duration_minutes=duration_minutes,
                status='in_progress',
                started_at=timezone.now()
            )

            # Save InterviewQuestion objects
            for q_data in questions_payload:
                InterviewQuestion.objects.create(
                    session=session,
                    question_number=q_data.get('question_number', 1),
                    text=q_data.get('text', ''),
                    category=q_data.get('category', 'technical'),
                    difficulty=q_data.get('difficulty', difficulty),
                    is_coding=q_data.get('is_coding', False),
                    coding_language=q_data.get('coding_language', 'python'),
                    starter_code=q_data.get('starter_code', ''),
                    test_cases=q_data.get('test_cases', []),
                    model_answer=q_data.get('model_answer', '')
                )

            messages.success(request, f"Interview session prepared with {len(questions_payload)} questions!")
            return redirect('interview_room', session_id=session.id)
    else:
        initial_resume_id = request.GET.get('resume_id')
        form = InterviewSetupForm(initial={'resume_id': initial_resume_id} if initial_resume_id else None)

    return render(request, 'interview/select_interview.html', {
        'form': form,
        'resumes': resumes
    })


@login_required
def interview_room_view(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    if session.status == 'completed':
        messages.info(request, "This interview is already completed. Viewing report.")
        return redirect('interview_report', session_id=session.id)

    questions = list(session.questions.all().order_by('question_number'))
    if not questions:
        messages.warning(request, "No questions found for this session.")
        return redirect('select_interview')

    # Convert questions to JSON for frontend
    questions_data = []
    for q in questions:
        has_ans = hasattr(q, 'answer')
        questions_data.append({
            'id': q.id,
            'question_number': q.question_number,
            'text': q.text,
            'category': q.category,
            'category_display': q.get_category_display(),
            'difficulty': q.difficulty,
            'is_coding': q.is_coding,
            'coding_language': q.coding_language or 'python',
            'starter_code': q.starter_code,
            'test_cases': q.test_cases,
            'answered': has_ans,
            'answer_text': q.answer.answer_text if has_ans else ''
        })

    return render(request, 'interview/interview_room.html', {
        'session': session,
        'questions_json': json.dumps(questions_data),
        'total_questions': len(questions),
        'duration_seconds': session.duration_minutes * 60,
    })


# ================= AJAX API ENDPOINTS =================

@login_required
def get_question_api(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    idx = int(request.GET.get('index', 0))
    questions = list(session.questions.all().order_by('question_number'))

    if idx < 0 or idx >= len(questions):
        return JsonResponse({'error': 'Index out of bounds'}, status=400)

    q = questions[idx]
    has_ans = hasattr(q, 'answer')
    return JsonResponse({
        'id': q.id,
        'question_number': q.question_number,
        'text': q.text,
        'category': q.category,
        'category_display': q.get_category_display(),
        'is_coding': q.is_coding,
        'coding_language': q.coding_language or 'python',
        'starter_code': q.starter_code,
        'test_cases': q.test_cases,
        'answered': has_ans,
        'answer_text': q.answer.answer_text if has_ans else ''
    })


@login_required
@require_POST
def submit_answer_api(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        body = request.POST

    question_id = body.get('question_id')
    answer_text = body.get('answer_text', '').strip()
    is_audio = bool(body.get('is_audio', True))

    question = get_object_or_404(InterviewQuestion, id=question_id, session=session)

    # AI Evaluation
    eval_data = evaluate_answer_with_ai(
        question_text=question.text,
        category=question.category,
        answer_text=answer_text,
        is_coding=False
    )

    # Save or update answer
    answer, _ = InterviewAnswer.objects.update_or_create(
        question=question,
        defaults={'answer_text': answer_text, 'is_audio': is_audio}
    )

    # Save or update evaluation
    AnswerEvaluation.objects.update_or_create(
        answer=answer,
        defaults={
            'score': eval_data['score'],
            'technical_correctness': eval_data['technical_correctness'],
            'relevance': eval_data['relevance'],
            'clarity': eval_data['clarity'],
            'strengths': eval_data['strengths'],
            'weaknesses': eval_data['weaknesses'],
            'improvements': eval_data['improvements'],
            'recommended_topics': eval_data['recommended_topics'],
            'model_answer': eval_data['model_answer'],
        }
    )

    return JsonResponse({
        'status': 'success',
        'score': eval_data['score'],
        'strengths': eval_data['strengths'],
        'weaknesses': eval_data['weaknesses'],
        'improvements': eval_data['improvements'],
        'follow_up': eval_data.get('follow_up_question', '')
    })


@login_required
@require_POST
def run_code_api(request, session_id):
    """Run code in isolated sandbox/Judge0 against sample test cases without submitting."""
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        body = request.POST

    source_code = body.get('source_code', '')
    language = body.get('language', 'python')
    question_id = body.get('question_id')

    test_cases = []
    if question_id:
        q = InterviewQuestion.objects.filter(id=question_id, session=session).first()
        if q and q.test_cases:
            test_cases = q.test_cases[:2]  # sample test cases

    results = run_code_against_test_cases(source_code, language, test_cases)
    return JsonResponse(results)


@login_required
@require_POST
def submit_code_api(request, session_id):
    """Submit code solution for evaluation and scoring."""
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        body = request.POST

    question_id = body.get('question_id')
    source_code = body.get('source_code', '')
    language = body.get('language', 'python')

    question = get_object_or_404(InterviewQuestion, id=question_id, session=session)

    # Run against test cases
    exec_res = run_code_against_test_cases(source_code, language, question.test_cases)

    # Create answer record
    answer, _ = InterviewAnswer.objects.update_or_create(
        question=question,
        defaults={'answer_text': f"[{language.upper()} Code Submission]\n{source_code}", 'is_audio': False}
    )

    # Save CodingSubmission
    submission = CodingSubmission.objects.create(
        question=question,
        answer=answer,
        language=language,
        source_code=source_code,
        status=exec_res['status'],
        stdout=exec_res['stdout'],
        stderr=exec_res['stderr'],
        compile_output=exec_res['compile_output'],
        execution_time=exec_res['execution_time'],
        memory_used=exec_res['memory_used'],
        passed_test_cases=exec_res['passed_test_cases'],
        total_test_cases=exec_res['total_test_cases']
    )

    # AI Evaluation for Code
    eval_data = evaluate_answer_with_ai(
        question_text=question.text,
        category='coding',
        answer_text=source_code,
        is_coding=True,
        code_meta=exec_res
    )

    AnswerEvaluation.objects.update_or_create(
        answer=answer,
        defaults={
            'score': eval_data['score'],
            'technical_correctness': eval_data['technical_correctness'],
            'relevance': eval_data['relevance'],
            'clarity': eval_data['clarity'],
            'strengths': eval_data['strengths'],
            'weaknesses': eval_data['weaknesses'],
            'improvements': eval_data['improvements'],
            'recommended_topics': eval_data['recommended_topics'],
            'model_answer': eval_data['model_answer'],
        }
    )

    return JsonResponse({
        'status': 'success',
        'exec_status': exec_res['status'],
        'passed': exec_res['passed_test_cases'],
        'total': exec_res['total_test_cases'],
        'stdout': exec_res['stdout'],
        'stderr': exec_res['stderr'],
        'score': eval_data['score'],
        'feedback': eval_data['strengths'],
        'follow_up': eval_data.get('follow_up_question', '')
    })


@login_required
@require_POST
def finish_interview_api(request, session_id):
    """Calculate overall scores, create report, and mark interview completed."""
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)

    questions = session.questions.all()
    evaluations = [q.answer.evaluation for q in questions if hasattr(q, 'answer') and hasattr(q.answer, 'evaluation')]

    if evaluations:
        session.overall_score = round(sum(e.score for e in evaluations) / len(evaluations), 1)

        tech_evals = [e.score for q, e in [(q, q.answer.evaluation) for q in questions if hasattr(q, 'answer') and hasattr(q.answer, 'evaluation')] if q.category in ['technical', 'skill']]
        coding_evals = [e.score for q, e in [(q, q.answer.evaluation) for q in questions if hasattr(q, 'answer') and hasattr(q.answer, 'evaluation')] if q.category == 'coding']
        hr_evals = [e.score for q, e in [(q, q.answer.evaluation) for q in questions if hasattr(q, 'answer') and hasattr(q.answer, 'evaluation')] if q.category == 'hr']
        proj_evals = [e.score for q, e in [(q, q.answer.evaluation) for q in questions if hasattr(q, 'answer') and hasattr(q.answer, 'evaluation')] if q.category in ['project', 'cross']]

        session.technical_score = round(sum(tech_evals) / len(tech_evals), 1) if tech_evals else session.overall_score
        session.coding_score = round(sum(coding_evals) / len(coding_evals), 1) if coding_evals else session.overall_score
        session.hr_score = round(sum(hr_evals) / len(hr_evals), 1) if hr_evals else session.overall_score
        session.project_score = round(sum(proj_evals) / len(proj_evals), 1) if proj_evals else session.overall_score
        session.communication_score = round(sum(e.clarity for e in evaluations) / len(evaluations), 1)
    else:
        session.overall_score = 0.0

    session.status = 'completed'
    session.completed_at = timezone.now()
    session.save()

    # Generate or update report
    summary_data = generate_session_report_summary(session)
    report, _ = InterviewReport.objects.update_or_create(
        session=session,
        defaults={
            'readiness_level': summary_data['readiness'],
            'summary_notes': summary_data['summary_notes'],
            'strengths_summary': summary_data['strengths_summary'],
            'weaknesses_summary': summary_data['weaknesses_summary'],
            'key_recommendations': summary_data['key_recommendations']
        }
    )

    return JsonResponse({
        'status': 'completed',
        'report_url': f"/interview/{session.id}/report/"
    })


@login_required
def interview_report_view(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    report, _ = InterviewReport.objects.get_or_create(session=session)
    questions = session.questions.all().order_by('question_number')

    # Prepare score data for Chart.js
    radar_labels = ['Technical', 'Coding', 'HR / Soft Skills', 'Project Knowledge', 'Communication']
    radar_scores = [
        session.technical_score or session.overall_score or 0.0,
        session.coding_score or session.overall_score or 0.0,
        session.hr_score or session.overall_score or 0.0,
        session.project_score or session.overall_score or 0.0,
        session.communication_score or session.overall_score or 0.0,
    ]

    q_labels = [f"Q{q.question_number}" for q in questions]
    q_scores = []
    for q in questions:
        if hasattr(q, 'answer') and hasattr(q.answer, 'evaluation'):
            q_scores.append(q.answer.evaluation.score)
        else:
            q_scores.append(0.0)

    context = {
        'session': session,
        'report': report,
        'questions': questions,
        'radar_labels_json': json.dumps(radar_labels),
        'radar_scores_json': json.dumps(radar_scores),
        'q_labels_json': json.dumps(q_labels),
        'q_scores_json': json.dumps(q_scores),
    }
    return render(request, 'interview/interview_report.html', context)


@login_required
def download_report_pdf(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    report, _ = InterviewReport.objects.get_or_create(session=session)

    pdf_buffer = build_interview_report_pdf(session, report)
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    filename = f"Performance_Report_{request.user.username}_INT{session.id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def interview_history_view(request):
    sessions = InterviewSession.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'interview/history.html', {'sessions': sessions})


@login_required
def practice_questions_view(request):
    return render(request, 'interview/practice_questions.html', {
        'questions_bank': QUESTIONS_BANK,
        'coding_challenges': CODING_CHALLENGES
    })
