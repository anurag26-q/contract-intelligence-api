"""
Webhooks service for sending event notifications.
"""

import logging
import json
import requests
from django.conf import settings
from celery import shared_task
import hmac
import hashlib

logger = logging.getLogger('api')


class WebhookService:
    """Service for sending webhook notifications."""
    
    def __init__(self):
        self.enabled = settings.WEBHOOK_ENABLED
        self.secret = settings.WEBHOOK_SECRET
    
    def send_event(self, webhook_url: str, event_type: str, data: dict):
        """
        Send webhook event via Celery task.
        
        Args:
            webhook_url: Target URL for webhook
            event_type: Type of event (document.ingested, extraction.complete, etc.)
            data: Event payload
        """
        if not self.enabled:
            logger.debug("Webhooks disabled, skipping")
            return
        
        send_webhook_task.delay(webhook_url, event_type, data, self.secret)
    
    def generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook verification."""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()


@shared_task(bind=True, max_retries=3)
def send_webhook_task(self, webhook_url: str, event_type: str, data: dict, secret: str):
    """
    Celery task to send webhook with retry logic.
    """
    try:
        payload = {
            'event': event_type,
            'data': data,
            'timestamp': data.get('timestamp', '')
        }
        
        payload_str = json.dumps(payload)
        
        # Generate signature
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature,
            'X-Event-Type': event_type,
        }
        
        response = requests.post(
            webhook_url,
            data=payload_str,
            headers=headers,
            timeout=10
        )
        
        response.raise_for_status()
        logger.info(f"Webhook sent successfully to {webhook_url}: {event_type}")
        
        return {
            'success': True,
            'status_code': response.status_code
        }
        
    except Exception as e:
        logger.error(f"Webhook failed for {webhook_url}: {e}")
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
