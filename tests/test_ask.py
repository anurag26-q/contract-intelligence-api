"""
Tests for the ask endpoint to verify helpful error messages when no documents are found or when the document isn't ready.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from api.models import Document, DocumentChunk


class AskEndpointTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_ask_document_not_found(self):
        resp = self.client.post('/api/ask', {'question': 'Hello', 'document_ids': [999]}, format='json')
        assert resp.status_code == 404
        assert 'missing_document_ids' in resp.data

    def test_ask_not_processed(self):
        doc = Document.objects.create(filename='pending.pdf', file_path='contracts/pending.pdf', file_hash='hashp', file_size=10, status='pending')
        resp = self.client.post('/api/ask', {'question': 'Question?', 'document_ids': [doc.id]}, format='json')
        assert resp.status_code == 400
        assert 'documents_not_processed' in resp.data

    def test_ask_processed_no_vectors(self):
        doc = Document.objects.create(filename='completed.pdf', file_path='contracts/completed.pdf', file_hash='hashc', file_size=10, status='completed')
        # No DocumentChunk created
        resp = self.client.post('/api/ask', {'question': 'Question?', 'document_ids': [doc.id]}, format='json')
        assert resp.status_code == 404
        assert resp.data.get('error') == 'Requested documents are processed but no vectors are indexed'
