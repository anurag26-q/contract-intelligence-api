"""
Utility functions for the API.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging

logger = logging.getLogger('api')


def custom_exception_handler(exc, context):
    """Custom exception handler for DRF."""
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the exception
        logger.error(f"API Exception: {exc}", exc_info=True)
        
        # Customize the response format
        custom_response_data = {
            'error': True,
            'message': str(exc),
            'details': response.data if response else None,
        }
        response.data = custom_response_data
    else:
        # Handle non-DRF exceptions
        logger.error(f"Unhandled Exception: {exc}", exc_info=True)
        response = Response({
            'error': True,
            'message': 'An unexpected error occurred.',
            'details': str(exc),
        }, status=500)
    
    return response


def calculate_token_count(text: str) -> int:
    """Estimate token count (rough approximation)."""
    # Rough estimate: 1 token ≈ 4 characters
    return len(text) // 4


def get_char_positions(full_text: str, excerpt: str) -> tuple:
    """Find character start and end positions of excerpt in full text."""
    try:
        start = full_text.index(excerpt)
        end = start + len(excerpt)
        return (start, end)
    except ValueError:
        return (None, None)
