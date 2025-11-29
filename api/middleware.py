"""
Custom middleware for the API.
"""

import re
import time
import logging
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('api')


class PIIRedactionMiddleware(MiddlewareMixin):
    """Middleware to redact PII from logs."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.pii_patterns = settings.PII_PATTERNS
        
    def redact_pii(self, text):
        """Redact PII from text using regex patterns."""
        if not isinstance(text, str):
            return text
        
        redacted = text
        for pii_type, pattern in self.pii_patterns.items():
            if pii_type == 'email':
                redacted = re.sub(pattern, '[REDACTED_EMAIL]', redacted)
            elif pii_type == 'phone':
                redacted = re.sub(pattern, '[REDACTED_PHONE]', redacted)
            elif pii_type == 'ssn':
                redacted = re.sub(pattern, '[REDACTED_SSN]', redacted)
            elif pii_type == 'credit_card':
                redacted = re.sub(pattern, '[REDACTED_CC]', redacted)
        
        return redacted
    
    def process_request(self, request):
        """Log incoming requests with PII redaction."""
        path = request.path
        method = request.method
        
        # Redact query parameters
        query_string = self.redact_pii(request.META.get('QUERY_STRING', ''))
        
        logger.info(f"Request: {method} {path} {query_string}")
        return None
    
    def process_response(self, request, response):
        """Log responses."""
        return response


class MetricsMiddleware(MiddlewareMixin):
    """Middleware to collect request metrics."""
    
    # Shared metrics storage (in-memory for simplicity, use Redis in production)
    metrics = {
        'requests_total': 0,
        'requests_by_endpoint': {},
        'requests_by_status': {},
        'avg_response_time': 0,
        'total_response_time': 0,
    }
    
    def process_request(self, request):
        """Record request start time."""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Record metrics for the request."""
        if hasattr(request, '_start_time'):
            response_time = time.time() - request._start_time
            
            # Update metrics
            self.metrics['requests_total'] += 1
            self.metrics['total_response_time'] += response_time
            self.metrics['avg_response_time'] = (
                self.metrics['total_response_time'] / self.metrics['requests_total']
            )
            
            # Track by endpoint
            endpoint = request.path
            if endpoint not in self.metrics['requests_by_endpoint']:
                self.metrics['requests_by_endpoint'][endpoint] = 0
            self.metrics['requests_by_endpoint'][endpoint] += 1
            
            # Track by status code
            status_code = response.status_code
            if status_code not in self.metrics['requests_by_status']:
                self.metrics['requests_by_status'][status_code] = 0
            self.metrics['requests_by_status'][status_code] += 1
        
        return response
    
    @classmethod
    def get_metrics(cls):
        """Get current metrics."""
        return cls.metrics
