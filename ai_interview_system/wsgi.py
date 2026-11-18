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

            # Auto-seed admin superuser
            from django.contrib.auth.models import User
            from interview.models import StudentProfile

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
    except Exception as exc:
        print("Vercel startup migration exception:", exc)
