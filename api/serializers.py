"""
DRF Serializers for API requests and responses.
"""

from rest_framework import serializers
from api.models import Document, ContractExtraction, AuditFinding


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""
    
    class Meta:
        model = Document
        fields = ['id', 'filename', 'file_size', 'status', 'uploaded_at', 'processed_at', 'page_count']
        read_only_fields = ['id', 'status', 'uploaded_at', 'processed_at', 'page_count']


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for PDF upload."""
    files = serializers.ListField(
        child=serializers.FileField(allow_empty_file=False),
        allow_empty=False,
        max_length=10,  # Max 10 files at once
    )
    
    def validate_files(self, files):
        """Validate uploaded files."""
        for file in files:
            # Check file extension
            if not file.name.lower().endswith('.pdf'):
                raise serializers.ValidationError(f"{file.name} is not a PDF file")
            
            # Check file size (max 50MB per file)
            if file.size > 50 * 1024 * 1024:
                raise serializers.ValidationError(f"{file.name} exceeds 50MB size limit")
        
        return files


class ContractExtractionSerializer(serializers.ModelSerializer):
    """Serializer for Contract Extraction."""
    
    class Meta:
        model = ContractExtraction
        fields = [
            'document', 'parties', 'effective_date', 'term', 'governing_law',
            'payment_terms', 'termination', 'auto_renewal', 'confidentiality',
            'indemnity', 'liability_cap', 'signatories', 'created_at'
        ]
        read_only_fields = ['created_at']


class ExtractRequestSerializer(serializers.Serializer):
    """Serializer for extract endpoint request."""
    document_id = serializers.IntegerField()


class AskRequestSerializer(serializers.Serializer):
    """Serializer for ask endpoint request."""
    question = serializers.CharField(max_length=1000)
    document_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
    )


class CitationSerializer(serializers.Serializer):
    """Serializer for citation data."""
    document_id = serializers.IntegerField()
    page_number = serializers.IntegerField(required=False, allow_null=True)
    char_start = serializers.IntegerField(required=False, allow_null=True)
    char_end = serializers.IntegerField(required=False, allow_null=True)


class AskResponseSerializer(serializers.Serializer):
    """Serializer for ask endpoint response."""
    answer = serializers.CharField()
    citations = CitationSerializer(many=True)


class AuditRequestSerializer(serializers.Serializer):
    """Serializer for audit endpoint request."""
    document_id = serializers.IntegerField()


class AuditFindingSerializer(serializers.ModelSerializer):
    """Serializer for Audit Finding."""
    
    class Meta:
        model = AuditFinding
        fields = [
            'id', 'risk_type', 'severity', 'title', 'description',
            'recommendation', 'evidence_text', 'char_start', 'char_end',
            'page_number', 'detection_method', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check response."""
    status = serializers.CharField()
    services = serializers.DictField()


class MetricsSerializer(serializers.Serializer):
    """Serializer for metrics response."""
    requests_total = serializers.IntegerField()
    requests_by_endpoint = serializers.DictField()
    requests_by_status = serializers.DictField()
    avg_response_time = serializers.FloatField()
    documents_ingested = serializers.IntegerField()
    extraction_success_rate = serializers.FloatField()
