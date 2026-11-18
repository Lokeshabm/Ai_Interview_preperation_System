import os
import sys

# Ensure root workspace is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_interview_system.wsgi import application

# Vercel Serverless Function entry point
app = application
