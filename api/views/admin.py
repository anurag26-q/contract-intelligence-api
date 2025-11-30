"""
Admin endpoints - Health check, metrics, etc.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from drf_spectacular.utils import extend_schema
from api.serializers import HealthCheckSerializer, MetricsSerializer
from api.middleware import MetricsMiddleware
from api.models import Document, ContractExtraction
from django.conf import settings
import redis

logger = logging.getLogger('api')


class HealthCheckView(APIView):
    """
    GET /api/healthz
    
    Health check endpoint to verify all services are running.
    """
    
    @extend_schema(
        responses={200: HealthCheckSerializer},
        description="Health check for all services"
    )
    def get(self, request):
        """Check health of all services."""
        services = {}
        overall_status = 'healthy'
        
        # Check Database (SQLite)
        try:
            connection.ensure_connection()
            services['database'] = 'healthy'
        except Exception as e:
            services['database'] = f'unhealthy: {str(e)}'
            overall_status = 'unhealthy'
        
        # Check Redis
        try:
            redis_client = redis.from_url(settings.REDIS_URL)
            redis_client.ping()
            services['redis'] = 'healthy'
        except Exception as e:
            services['redis'] = f'unhealthy: {str(e)}'
            overall_status = 'unhealthy'
        
        status_code = status.HTTP_200_OK if overall_status == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response({
            'status': overall_status,
            'services': services
        }, status=status_code)


class MetricsView(APIView):
    """
    GET /api/metrics
    
    Get API metrics and statistics.
    """
    
    @extend_schema(
        responses={200: MetricsSerializer},
        description="Get API metrics and usage statistics"
    )
    def get(self, request):
        """Get metrics."""
        # Get middleware metrics
        middleware_metrics = MetricsMiddleware.get_metrics()
        
        # Get document stats
        total_documents = Document.objects.count()
        completed_documents = Document.objects.filter(status='completed').count()
        failed_documents = Document.objects.filter(status='failed').count()
        
        # Get extraction stats
        total_extractions = ContractExtraction.objects.count()
        extraction_success_rate = (total_extractions / total_documents * 100) if total_documents > 0 else 0
        
        return Response({
            'requests_total': middleware_metrics['requests_total'],
            'requests_by_endpoint': middleware_metrics['requests_by_endpoint'],
            'requests_by_status': middleware_metrics['requests_by_status'],
            'avg_response_time': middleware_metrics['avg_response_time'],
            'documents_ingested': total_documents,
            'documents_completed': completed_documents,
            'documents_failed': failed_documents,
            'extraction_success_rate': round(extraction_success_rate, 2),
        }, status=status.HTTP_200_OK)
