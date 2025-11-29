"""
Celery tasks for async document processing.
"""

import logging
from celery import shared_task
from django.utils import timezone
from api.models import Document, DocumentPage, DocumentChunk, ContractExtraction
from api.services.pdf_processor import PDFProcessor
from api.services.extractor import ContractExtractor

logger = logging.getLogger('api')


@shared_task(bind=True, max_retries=3)
def process_document_task(self, document_id: int):
    """Process uploaded PDF document asynchronously."""
    try:
        logger.info(f"Starting processing for document {document_id}")
        
        # Get document
        document = Document.objects.get(id=document_id)
        document.status = 'processing'
        document.save()
        
        # Initialize processor
        processor = PDFProcessor()
        
        # Extract text and pages using LangChain PyPDFLoader
        pdf_path = document.file_path.path
        pages_data = processor.extract_pages_with_langchain(pdf_path)
        
        # Save pages to database
        for page_data in pages_data:
            DocumentPage.objects.create(
                document=document,
                page_number=page_data['page_number'],
                text_content=page_data['text'],
                char_count=page_data['char_count'],
                metadata=page_data['metadata'],
            )
        
        # Get full text for chunking
        full_text = '\n\n'.join([p['text'] for p in pages_data])
        document.page_count = len(pages_data)
        document.total_characters = len(full_text)
        
        # Chunk text using LangChain RecursiveCharacterTextSplitter
        chunks = processor.chunk_text_with_langchain(full_text)
        
        # Store vectors in Qdrant and save chunks to DB
        vector_ids = processor.store_vectors(chunks, document_id)
        
        for chunk, vector_id in zip(chunks, vector_ids):
            DocumentChunk.objects.create(
                document=document,
                chunk_index=chunk['chunk_index'],
                text_content=chunk['text'],
                char_start=chunk['char_start'],
                char_end=chunk['char_end'],
                vector_id=vector_id,
                metadata=chunk.get('metadata', {}),
            )
        
        # Mark as completed
        document.status = 'completed'
        document.processed_at = timezone.now()
        document.save()
        
        logger.info(f"Successfully processed document {document_id}")
        
        # Trigger extraction task
        extract_contract_fields_task.delay(document_id)
        
        return {
            'document_id': document_id,
            'status': 'completed',
            'pages': len(pages_data),
            'chunks': len(chunks),
        }
        
    except Exception as e:
        logger.error(f"Document processing failed for {document_id}: {e}", exc_info=True)
        
        # Update document status
        try:
            document = Document.objects.get(id=document_id)
            document.status = 'failed'
            document.error_message = str(e)
            document.save()
        except:
            pass
        
        # Retry
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=2)
def extract_contract_fields_task(self, document_id: int):
    """Extract contract fields asynchronously."""
    try:
        logger.info(f"Starting field extraction for document {document_id}")
        
        # Get document
        document = Document.objects.get(id=document_id)
        
        # Get document text
        pages = document.pages.all().order_by('page_number')
        full_text = '\n\n'.join([page.text_content for page in pages])
        
        # Extract fields
        extractor = ContractExtractor()
        extracted_data = extractor.extract_fields(full_text)
        
        # Save extraction
        ContractExtraction.objects.create(
            document=document,
            parties=extracted_data.get('parties', []),
            effective_date=extracted_data.get('effective_date'),
            term=extracted_data.get('term'),
            governing_law=extracted_data.get('governing_law'),
            payment_terms=extracted_data.get('payment_terms'),
            termination=extracted_data.get('termination'),
            auto_renewal=extracted_data.get('auto_renewal', {}),
            confidentiality=extracted_data.get('confidentiality'),
            indemnity=extracted_data.get('indemnity'),
            liability_cap=extracted_data.get('liability_cap', {}),
            signatories=extracted_data.get('signatories', []),
            raw_extraction=extracted_data,
        )
        
        logger.info(f"Successfully extracted fields for document {document_id}")
        
        return {
            'document_id': document_id,
            'extraction': 'completed'
        }
        
    except Exception as e:
        logger.error(f"Field extraction failed for {document_id}: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=30 * (self.request.retries + 1))
