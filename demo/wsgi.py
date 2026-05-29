"""
WSGI config for tianai-captcha demo project.
"""
import os
import sys

from django.core.wsgi import get_wsgi_application

demo_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(demo_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if demo_dir not in sys.path:
    sys.path.insert(0, os.path.dirname(demo_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demo.settings')

application = get_wsgi_application()
