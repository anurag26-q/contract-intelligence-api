"""
Ask endpoint - RAG-based question answering over contracts.
"""

import logging
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import StreamingHttpResponse
from drf_spectacular.utils import extend_schema
from api.serializers import AskRequestSerializer, AskResponseSerializer
from api.services.rag_engine import RAGEngine

logger = logging.getLogger('api')


class AskView(APIView):
    """
    POST /api/ask
    
    Ask questions about uploaded contracts.
    Returns answer grounded in documents with citations.
    """
    
    @extend_schema(
        request=AskRequestSerializer,
        responses={200: AskResponseSerializer},
        description="Ask questions about contracts using RAG"
    )
    def post(self, request):
        """Answer question using RAG."""
        serializer = AskRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        question = serializer.validated_data['question']
        document_ids = serializer.validated_data.get('document_ids')
        
        # Initialize RAG engine
        rag_engine = RAGEngine()
        
        # Retrieve relevant chunks
        chunks = rag_engine.retrieve(question, document_ids=document_ids, top_k=5)
        
        if not chunks:
            return Response({
                'success': False,
                'error': 'No relevant documents found for this question'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Generate answer
        answer, citations = rag_engine.generate_answer(question, chunks)
        
        return Response({
            'success': True,
            'question': question,
            'answer': answer,
            'citations': citations
        }, status=status.HTTP_200_OK)


class AskStreamView(APIView):
    """
    GET /api/ask/stream
    
    Ask questions with streaming response (Server-Sent Events).
    """
    
    def get(self, request):
        """Stream answer using SSE."""
        question = request.query_params.get('question')
        document_ids_str = request.query_params.get('document_ids')
        
        if not question:
            return Response({
                'error': True,
                'message': 'Question parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse document_ids
        document_ids = None
        if document_ids_str:
            try:
                document_ids = [int(x) for x in document_ids_str.split(',')]
            except ValueError:
                return Response({
                    'error': True,
                    'message': 'Invalid document_ids format'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize RAG engine
        rag_engine = RAGEngine()
        
        # Retrieve chunks
        chunks = rag_engine.retrieve(question, document_ids=document_ids, top_k=5)
        
        if not chunks:
            return Response({
                'error': True,
                'message': 'No relevant documents found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Stream generator
        def event_stream():
            """Generate SSE events."""
            yield 'data: {"type": "start"}\n\n'
            
            for content in rag_engine.generate_answer_stream(question, chunks):
                # Check if this is citations
                if '__CITATIONS__:' in content:
                    citations_str = content.split('__CITATIONS__:')[1]
                    yield f'data: {{"type": "citations", "data": {citations_str}}}\n\n'
                else:
                    # Regular content token
                    data = json.dumps({'type': 'token', 'content': content})
                    yield f'data: {data}\n\n'
            
            yield 'data: {"type": "end"}\n\n'
        
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        
        return response
