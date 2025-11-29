"""
API app configuration.
"""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        # Import Celery app to ensure it's loaded
        from contract_intelligence import celery as celery_app  # noqa
        # Import signals if any
        import api.signals  # noqa
