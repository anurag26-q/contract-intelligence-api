"""
Audit endpoint - Contract risk analysis.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from api.serializers import AuditRequestSerializer, AuditFindingSerializer
from api.models import Document, ContractExtraction, AuditFinding
from api.services.audit_engine import AuditEngine

logger = logging.getLogger('api')


class AuditView(APIView):
    """
    POST /api/audit
    
    Audit contract for risky clauses.
    Returns list of findings with severity, evidence, and recommendations.
    """
    
    @extend_schema(
        request=AuditRequestSerializer,
        responses={200: AuditFindingSerializer(many=True)},
        description="Audit contract for risky clauses and compliance issues"
    )
    def post(self, request):
        """Audit contract for risks."""
        serializer = AuditRequestSerializer(data=request.data)
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
                'message': f'Document is not ready. Current status: {document.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if audit already exists
        existing_findings = AuditFinding.objects.filter(document=document)
        if existing_findings.exists():
            logger.info(f"Returning cached audit findings for document {document_id}")
            findings_data = [f.to_dict() for f in existing_findings]
            return Response({
                'success': True,
                'document_id': document_id,
                'findings_count': len(findings_data),
                'findings': findings_data
            }, status=status.HTTP_200_OK)
        
        # Get document text
        pages = document.pages.all().order_by('page_number')
        full_text = '\n\n'.join([page.text_content for page in pages])
        
        # Get extraction data if available
        extracted_data = None
        try:
            extraction = ContractExtraction.objects.get(document=document)
            extracted_data = extraction.raw_extraction
        except ContractExtraction.DoesNotExist:
            pass
        
        # Run audit
        audit_engine = AuditEngine()
        findings = audit_engine.audit_contract(full_text, extracted_data)
        
        # Save findings to database
        saved_findings = []
        for finding in findings:
            audit_finding = AuditFinding.objects.create(
                document=document,
                risk_type=finding.get('risk_type', 'other'),
                severity=finding.get('severity', 'medium'),
                title=finding.get('title', ''),
                description=finding.get('description', ''),
                recommendation=finding.get('recommendation', ''),
                evidence_text=finding.get('evidence', '')[:1000],  # Truncate if too long
                detection_method=finding.get('detection_method', 'hybrid'),
                rule_matched=finding.get('rule_matched'),
            )
            saved_findings.append(audit_finding)
        
        # Return findings
        findings_data = [f.to_dict() for f in saved_findings]
        
        return Response({
            'success': True,
            'document_id': document_id,
            'findings_count': len(findings_data),
            'findings': findings_data
        }, status=status.HTTP_200_OK)
