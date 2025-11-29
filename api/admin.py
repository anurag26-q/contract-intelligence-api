"""
Admin configuration for API models.
"""

from django.contrib import admin
from api.models import Document, DocumentPage, DocumentChunk, ContractExtraction, AuditFinding


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'filename', 'status', 'uploaded_at', 'page_count']
    list_filter = ['status', 'uploaded_at']
    search_fields = ['filename', 'file_hash']
    readonly_fields = ['uploaded_at', 'processed_at', 'file_hash']


@admin.register(DocumentPage)
class DocumentPageAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'page_number', 'char_count']
    list_filter = ['document']
    search_fields = ['document__filename']


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'chunk_index', 'vector_id']
    list_filter = ['document']
    search_fields = ['document__filename', 'vector_id']


@admin.register(ContractExtraction)
class ContractExtractionAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'effective_date', 'governing_law', 'created_at']
    list_filter = ['created_at', 'effective_date']
    search_fields = ['document__filename']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AuditFinding)
class AuditFindingAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'risk_type', 'severity', 'detection_method', 'created_at']
    list_filter = ['severity', 'risk_type', 'detection_method', 'created_at']
    search_fields = ['document__filename', 'title', 'description']
    readonly_fields = ['created_at']
