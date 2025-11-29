"""
API URL routing.
"""

from django.urls import path
from api.views.ingest import IngestView
from api.views.extract import ExtractView
from api.views.ask import AskView, AskStreamView
from api.views.audit import AuditView
from api.views.admin import HealthCheckView, MetricsView

urlpatterns = [
    # Document ingestion
    path('ingest', IngestView.as_view(), name='ingest'),
    
    # Field extraction
    path('extract', ExtractView.as_view(), name='extract'),
    
    # RAG Q&A
    path('ask', AskView.as_view(), name='ask'),
    path('ask/stream', AskStreamView.as_view(), name='ask-stream'),
    
    # Audit
    path('audit', AuditView.as_view(), name='audit'),
    
    # Admin endpoints
    path('healthz', HealthCheckView.as_view(), name='healthz'),
    path('metrics', MetricsView.as_view(), name='metrics'),
]
