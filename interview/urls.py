from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('select-interview/', views.select_interview_view, name='select_interview'),
    path('upload-resume/', views.upload_resume_view, name='upload_resume'),
    path('resume/<int:resume_id>/analysis/', views.resume_analysis_view, name='resume_analysis'),
    path('interview/<int:session_id>/', views.interview_room_view, name='interview_room'),
    path('interview/<int:session_id>/report/', views.interview_report_view, name='interview_report'),
    path('interview/<int:session_id>/download-pdf/', views.download_report_pdf, name='download_report_pdf'),
    path('history/', views.interview_history_view, name='interview_history'),
    path('practice-questions/', views.practice_questions_view, name='practice_questions'),

    # AJAX & API Endpoints for Voice & Coding Interview
    path('api/interview/<int:session_id>/get-question/', views.get_question_api, name='api_get_question'),
    path('api/interview/<int:session_id>/submit-answer/', views.submit_answer_api, name='api_submit_answer'),
    path('api/interview/<int:session_id>/run-code/', views.run_code_api, name='api_run_code'),
    path('api/interview/<int:session_id>/submit-code/', views.submit_code_api, name='api_submit_code'),
    path('api/interview/<int:session_id>/finish/', views.finish_interview_api, name='api_finish_interview'),
]
