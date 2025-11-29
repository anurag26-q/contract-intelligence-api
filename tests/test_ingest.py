"""
Tests for the ingest endpoint.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient
from api.models import Document


class IngestEndpointTest(TestCase):
    """Test PDF ingestion endpoint."""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_ingest_valid_pdf(self):
        """Test uploading a valid PDF file."""
        # Create a fake PDF file
        pdf_content = b'%PDF-1.4 fake pdf content'
        pdf_file = SimpleUploadedFile("test_contract.pdf", pdf_content, content_type="application/pdf")
        
        response = self.client.post('/api/ingest', {'files': [pdf_file]}, format='multipart')
        
        assert response.status_code == 201
        assert 'document_ids' in response.data
        assert len(response.data['document_ids']) == 1
    
    def test_ingest_non_pdf_file(self):
        """Test uploading a non-PDF file should fail."""
        txt_file = SimpleUploadedFile("test.txt", b"not a pdf", content_type="text/plain")
        
        response = self.client.post('/api/ingest', {'files': [txt_file]}, format='multipart')
        
        assert response.status_code == 400
    
    def test_ingest_duplicate_file(self):
        """Test uploading the same file twice should detect duplicate."""
        pdf_content = b'%PDF-1.4 same content'
        pdf_file1 = SimpleUploadedFile("contract.pdf", pdf_content, content_type="application/pdf")
        pdf_file2 = SimpleUploadedFile("contract_copy.pdf", pdf_content, content_type="application/pdf")
        
        # First upload
        response1 = self.client.post('/api/ingest', {'files': [pdf_file1]}, format='multipart')
        doc_id_1 = response1.data['document_ids'][0]
        
        # Second upload (same content, different name)
        response2 = self.client.post('/api/ingest', {'files': [pdf_file2]}, format='multipart')
        doc_id_2 = response2.data['document_ids'][0]
        
        # Should return same document ID
        assert doc_id_1 == doc_id_2
    
    def test_ingest_multiple_files(self):
        """Test uploading multiple PDF files at once."""
        pdf1 = SimpleUploadedFile("doc1.pdf", b'%PDF-1.4 content1', content_type="application/pdf")
        pdf2 = SimpleUploadedFile("doc2.pdf", b'%PDF-1.4 content2', content_type="application/pdf")
        
        response = self.client.post('/api/ingest', {'files': [pdf1, pdf2]}, format='multipart')
        
        assert response.status_code == 201
        assert len(response.data['document_ids']) == 2
