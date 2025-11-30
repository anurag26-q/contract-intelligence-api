"""
Tests for contract extraction task, verifying JSON serialization
and handling of duplicate creations.
"""

import pytest
from datetime import date

from api.tasks import extract_contract_fields_task
from api.services.extractor import ContractExtractor
from api.models import Document, DocumentPage, ContractExtraction


def setup_test_document():
    """Create a minimal test document with a single page and return the Document."""
    doc = Document.objects.create(
        filename='test_contract.pdf',
        file_path='contracts/test_contract.pdf',
        file_hash='testhash123',
        file_size=1234,
        status='completed',
    )
    DocumentPage.objects.create(document=doc, page_number=1, text_content='Dummy text', char_count=9)
    return doc


@pytest.mark.django_db
def test_raw_extraction_date_serialized(monkeypatch):
        # Monkeypatch extractor to return date objects nested inside data
        def fake_extract(self, text):
            return {
                'parties': ['Acme Corp', 'Beta Inc'],
                'effective_date': date(2024, 1, 1),
                'term': '2 years',
                'governing_law': 'New York',
                'payment_terms': 'Net 30',
                'termination': '30-day notice',
                'auto_renewal': {'enabled': False},
                'confidentiality': 'Standard NDA',
                'indemnity': 'Mutual',
                'liability_cap': {'amount': 1000000.0, 'currency': 'USD'},
                'signatories': [{'name': 'John Doe', 'title': 'CEO', 'signed_on': date(2024, 2, 1)}],
            }

        monkeypatch.setattr(ContractExtractor, 'extract_fields', fake_extract)

        # Run the task directly (call the wrapped function, pass None for self)
        doc = setup_test_document()
        extract_contract_fields_task.__wrapped__(None, doc.id)

        extraction = ContractExtraction.objects.get(document=doc)
        # Verify raw_extraction dates are strings
        assert isinstance(extraction.raw_extraction.get('effective_date'), str)
        assert isinstance(extraction.raw_extraction['signatories'][0].get('signed_on'), str)

@pytest.mark.django_db
def test_extract_task_create_or_update(monkeypatch):
        # Same fake extractor to ensure it creates the extraction
        def fake_extract2(self, text):
            return {'parties': ['A'], 'effective_date': date(2025, 1, 1)}

        monkeypatch.setattr(ContractExtractor, 'extract_fields', fake_extract2)

        # Create a new document for this test and ensure it runs twice without errors
        doc = setup_test_document()
        extract_contract_fields_task.__wrapped__(None, doc.id)
        extract_contract_fields_task.__wrapped__(None, doc.id)

        extractions = ContractExtraction.objects.filter(document=doc)
        assert extractions.count() == 1
