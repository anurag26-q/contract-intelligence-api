"""
Extract endpoint - Structured field extraction from contracts.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from api.serializers import ExtractRequestSerializer, ContractExtractionSerializer
from api.models import Document, ContractExtraction

logger = logging.getLogger('api')


class ExtractView(APIView):
    """
    POST /api/extract
    
    Extract structured fields from a contract document.
    Returns JSON with parties, dates, terms, clauses, etc.
    """
    
    @extend_schema(
        request=ExtractRequestSerializer,
        responses={200: ContractExtractionSerializer},
        description="Extract structured fields from a contract document"
    )
    def post(self, request):
        """Extract contract fields."""
        serializer = ExtractRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        document_id = serializer.validated_data['document_id']
        
        # Get document
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response({
                'error': True,
                'message': f'Document {document_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if document is processed
        if document.status != 'completed':
            return Response({
                'error': True,
                'message': f'Document is not ready. Current status: {document.status}',
                'status': document.status
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or wait for extraction
        try:
            extraction = ContractExtraction.objects.get(document=document)
            extraction_data = extraction.to_dict()
            
            return Response({
                'success': True,
                'document_id': document_id,
                'extraction': extraction_data
            }, status=status.HTTP_200_OK)
            
        except ContractExtraction.DoesNotExist:
            return Response({
                'error': True,
                'message': 'Extraction not yet completed. Please try again in a few moments.',
                'status': 'processing'
            }, status=status.HTTP_202_ACCEPTED)
