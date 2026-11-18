from django.contrib import admin
from .models import (
    StudentProfile,
    Resume,
    ResumeAnalysis,
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
    CodingSubmission,
    AnswerEvaluation,
    InterviewReport,
)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'college_name', 'degree', 'department', 'phone_number', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'college_name')


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'file_name', 'file_type', 'uploaded_at')
    search_fields = ('user__username', 'file_name')
    list_filter = ('file_type', 'uploaded_at')


@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'resume', 'analyzed_at')
    search_fields = ('resume__user__username', 'resume__file_name')


class InterviewQuestionInline(admin.TabularInline):
    model = InterviewQuestion
    extra = 0
    fields = ('question_number', 'category', 'is_coding', 'text')


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'interview_type', 'difficulty', 'status', 'overall_score', 'created_at')
    list_filter = ('interview_type', 'difficulty', 'status', 'created_at')
    search_fields = ('user__username', 'target_role')
    inlines = [InterviewQuestionInline]


@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'question_number', 'category', 'is_coding')
    list_filter = ('category', 'is_coding', 'difficulty')
    search_fields = ('text', 'session__user__username')


@admin.register(InterviewAnswer)
class InterviewAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'is_audio', 'answered_at')
    search_fields = ('question__text', 'answer_text')


@admin.register(CodingSubmission)
class CodingSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'language', 'status', 'passed_test_cases', 'total_test_cases', 'submitted_at')
    list_filter = ('language', 'status')
    search_fields = ('question__text', 'source_code')


@admin.register(AnswerEvaluation)
class AnswerEvaluationAdmin(admin.ModelAdmin):
    list_display = ('id', 'answer', 'score', 'evaluated_at')
    list_filter = ('score',)


@admin.register(InterviewReport)
class InterviewReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'readiness_level', 'generated_at')
    list_filter = ('readiness_level',)
