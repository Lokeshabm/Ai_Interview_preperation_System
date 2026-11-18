import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_interview_system.settings')
django.setup()

from django.contrib.auth.models import User
from interview.models import StudentProfile

if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    admin.first_name = "System"
    admin.last_name = "Administrator"
    admin.save()
    StudentProfile.objects.create(
        user=admin,
        phone_number="+91 9999999999",
        college_name="Administration & Engineering Faculty",
        degree="Admin",
        department="Computer Science"
    )
    print("Superuser 'admin' with password 'admin123' created successfully.")
else:
    print("Superuser 'admin' already exists.")
