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


def pytest_ignore_collect(path, config):
    """Ignore root-level test output files which are not Python tests."""
    # ignore files that start with 'test_output' but are not .py
    if str(path).lower().endswith('.txt') and path.name.startswith('test_output'):
        return True
    return False
