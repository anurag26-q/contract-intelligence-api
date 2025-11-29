"""
Test configuration for pytest-django.
"""

import os
import django
from django.conf import settings

# Configure Django settings for tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contract_intelligence.settings')

def pytest_configure():
    settings.DEBUG = False
    settings.TESTING = True
    django.setup()
