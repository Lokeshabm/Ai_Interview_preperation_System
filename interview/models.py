from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True)
    college_name = models.CharField(max_length=255, blank=True)
    degree = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.college_name})"


class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(upload_to='resumes/%Y/%m/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)  # 'pdf' or 'docx'
    raw_text = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_name} - {self.user.username}"


class ResumeAnalysis(models.Model):
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name='analysis')
    extracted_data = models.JSONField(default=dict, blank=True)
    # Structure of extracted_data:
    # {
    #   "student_name": "", "email": "", "phone": "",
    #   "education": [], "technical_skills": [], "programming_languages": [],
    #   "frameworks": [], "projects": [], "internships": [],
    #   "certifications": [], "work_experience": [], "achievements": []
    # }
    ai_summary = models.TextField(blank=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for Resume {self.resume.id} ({self.resume.file_name})"


class InterviewSession(models.Model):
    TYPE_CHOICES = [
        ('technical', 'Technical Interview'),
        ('hr', 'HR Interview'),
        ('coding', 'Coding Interview'),
        ('project', 'Project-Based Interview'),
        ('mixed', 'Mixed Interview'),
    ]
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interview_sessions')
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True, related_name='interview_sessions')
    target_role = models.CharField(max_length=255, default='Software Engineer')
    interview_type = models.CharField(max_length=32, choices=TYPE_CHOICES, default='mixed')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate')
    total_questions_target = models.IntegerField(default=10)
    duration_minutes = models.IntegerField(default=30)
    current_question_index = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')

    # Aggregated Performance Scores (0-10)
    overall_score = models.FloatField(null=True, blank=True)
    technical_score = models.FloatField(null=True, blank=True)
    hr_score = models.FloatField(null=True, blank=True)
    coding_score = models.FloatField(null=True, blank=True)
    project_score = models.FloatField(null=True, blank=True)
    communication_score = models.FloatField(null=True, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_interview_type_display()} ({self.created_at:%Y-%m-%d})"


class InterviewQuestion(models.Model):
    CATEGORY_CHOICES = [
        ('technical', 'Technical'),
        ('coding', 'Programming/Coding'),
        ('hr', 'HR'),
        ('project', 'Project-Based'),
        ('skill', 'Skill-Based'),
        ('experience', 'Experience-Based'),
        ('cross', 'Resume Cross-Question'),
    ]

    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='questions')
    question_number = models.IntegerField(default=1)
    text = models.TextField()
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='technical')
    difficulty = models.CharField(max_length=20, default='intermediate')
    is_coding = models.BooleanField(default=False)
    coding_language = models.CharField(max_length=32, default='python', blank=True)
    starter_code = models.TextField(blank=True)
    test_cases = models.JSONField(default=list, blank=True)
    model_answer = models.TextField(blank=True)
    follow_up_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='follow_ups')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['question_number']

    def __str__(self):
        return f"Q{self.question_number} [{self.category}]: {self.text[:50]}..."


class InterviewAnswer(models.Model):
    question = models.OneToOneField(InterviewQuestion, on_delete=models.CASCADE, related_name='answer')
    answer_text = models.TextField(blank=True)
    is_audio = models.BooleanField(default=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer for Q{self.question.question_number} (Session {self.question.session_id})"


class CodingSubmission(models.Model):
    question = models.ForeignKey(InterviewQuestion, on_delete=models.CASCADE, related_name='coding_submissions')
    answer = models.ForeignKey(InterviewAnswer, on_delete=models.SET_NULL, null=True, blank=True, related_name='submissions')
    language = models.CharField(max_length=32, default='python')
    source_code = models.TextField()
    status = models.CharField(max_length=50, default='Submitted')  # Accepted, Wrong Answer, Compile Error, etc.
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    compile_output = models.TextField(blank=True)
    execution_time = models.FloatField(null=True, blank=True)  # in seconds
    memory_used = models.IntegerField(null=True, blank=True)   # in KB
    passed_test_cases = models.IntegerField(default=0)
    total_test_cases = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Submission for Q{self.question.question_number} - {self.status} ({self.language})"


class AnswerEvaluation(models.Model):
    answer = models.OneToOneField(InterviewAnswer, on_delete=models.CASCADE, related_name='evaluation')
    score = models.FloatField(default=0.0)  # out of 10
    technical_correctness = models.FloatField(default=0.0)
    relevance = models.FloatField(default=0.0)
    clarity = models.FloatField(default=0.0)
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    improvements = models.TextField(blank=True)
    recommended_topics = models.JSONField(default=list, blank=True)
    model_answer = models.TextField(blank=True)
    evaluated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evaluation for Q{self.answer.question.question_number}: {self.score}/10"


class InterviewReport(models.Model):
    session = models.OneToOneField(InterviewSession, on_delete=models.CASCADE, related_name='report')
    readiness_level = models.CharField(max_length=50, default='Placement Ready')
    summary_notes = models.TextField(blank=True)
    strengths_summary = models.TextField(blank=True)
    weaknesses_summary = models.TextField(blank=True)
    key_recommendations = models.JSONField(default=list, blank=True)
    pdf_file = models.FileField(upload_to='reports/%Y/%m/', null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for Session {self.session_id} - {self.readiness_level}"
