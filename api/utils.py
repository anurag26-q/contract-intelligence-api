"""
Utility functions for the API.
"""

import logging
from rest_framework.response import Response
from rest_framework.views import exception_handler

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


def make_json_serializable(obj):
    """Recursively convert objects into JSON-serializable types.

    - datetime.date / datetime.datetime -> ISO string
    - Decimal -> float
    - bytes -> decoded string (utf-8)
    - Recursively process dicts and lists/tuples
    """
    from datetime import date, datetime
    try:
        from decimal import Decimal
    except Exception:
        Decimal = None

    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if Decimal and isinstance(obj, Decimal):
        try:
            return float(obj)
        except Exception:
            return str(obj)
    if isinstance(obj, bytes):
        try:
            return obj.decode('utf-8')
        except Exception:
            return str(obj)
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [make_json_serializable(v) for v in obj]
    # Fallback: string representation
    return str(obj)
