from django import forms
from django.contrib.auth.models import User
from .models import StudentProfile, Resume, InterviewSession


class StudentRegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. lokesh_dev'})
    )
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Lokesh Sharma'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 9876543210'})
    )
    college_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. National Institute of Technology'})
    )
    degree = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. B.Tech / B.E / M.Tech / MCA'})
    )
    department = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Science & Engineering'})
    )
    password = forms.CharField(
        required=True,
        min_length=6,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Minimum 6 characters'})
    )
    confirm_password = forms.CharField(
        required=True,
        min_length=6,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Re-enter your password'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


class StudentProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))

    class Meta:
        model = StudentProfile
        fields = ['phone_number', 'college_name', 'degree', 'department', 'bio']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'college_name': forms.TextInput(attrs={'class': 'form-control'}),
            'degree': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'A brief bio...'}),
        }


class ResumeUploadForm(forms.Form):
    target_role = forms.CharField(
        max_length=255,
        required=True,
        initial='Software Engineer',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python Full Stack Developer'})
    )
    resume_file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.docx'})
    )

    def clean_resume_file(self):
        file = self.cleaned_data.get('resume_file')
        if not file:
            raise forms.ValidationError("Please select a resume file.")
        
        name = file.name.lower()
        if not (name.endswith('.pdf') or name.endswith('.docx')):
            raise forms.ValidationError("Only PDF (.pdf) and Word (.docx) files are supported.")
        
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Resume file size must not exceed 5 MB.")
        return file


class InterviewSetupForm(forms.Form):
    target_role = forms.CharField(
        max_length=255,
        required=True,
        initial='Full Stack Developer',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    interview_type = forms.ChoiceField(
        choices=InterviewSession.TYPE_CHOICES,
        initial='mixed',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    difficulty = forms.ChoiceField(
        choices=InterviewSession.DIFFICULTY_CHOICES,
        initial='intermediate',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    total_questions = forms.ChoiceField(
        choices=[(5, '5 Questions (Quick Test)'), (10, '10 Questions (Standard)'), (20, '20 Questions (In-Depth)'), (30, '30 Questions (Full Assessment)')],
        initial=10,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    duration_minutes = forms.ChoiceField(
        choices=[(15, '15 Minutes'), (30, '30 Minutes'), (45, '45 Minutes'), (60, '60 Minutes')],
        initial=30,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    resume_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )
