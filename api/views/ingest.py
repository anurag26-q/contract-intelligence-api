"""
Ingest endpoint - PDF upload and processing.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from api.serializers import DocumentUploadSerializer, DocumentSerializer
from api.models import Document
from api.tasks import process_document_task

logger = logging.getLogger('api')


class IngestView(APIView):
    """
    POST /api/ingest
    
    Upload 1 or more PDF files for processing.
    Returns document_ids immediately. Processing happens asynchronously.
    """
    
    @extend_schema(
        request=DocumentUploadSerializer,
        responses={201: DocumentSerializer(many=True)},
        description="Upload PDF contracts for ingestion and processing"
    )
    def post(self, request):
        """Handle PDF upload."""
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uploaded_files = request.FILES.getlist('files')
        document_ids = []
        documents_created = []
        
        for uploaded_file in uploaded_files:
            # Create document record
            document = Document(
                filename=uploaded_file.name,
                file_path=uploaded_file,
                file_size=uploaded_file.size,
            )
            
            # Calculate file hash to check for duplicates
            file_hash = document.calculate_file_hash(uploaded_file.file)
            document.file_hash = file_hash
            
            # Check if document already exists
            existing_doc = Document.objects.filter(file_hash=file_hash).first()
            if existing_doc:
                logger.info(f"Document with hash {file_hash} already exists (ID: {existing_doc.id})")
                document_ids.append(existing_doc.id)
                documents_created.append(existing_doc)
                continue
            
            # Save document
            document.save()
            document_ids.append(document.id)
            documents_created.append(document)
            
            # Trigger async processing
            process_document_task.delay(document.id)
            logger.info(f"Triggered processing for document {document.id}")
        
        serializer = DocumentSerializer(documents_created, many=True)
        
        return Response({
            'success': True,
            'document_ids': document_ids,
            'documents': serializer.data,
            'message': f'{len(document_ids)} document(s) queued for processing'
        }, status=status.HTTP_201_CREATED)
