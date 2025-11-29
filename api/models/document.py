"""
Document-related database models.
"""

from django.db import models
from django.utils import timezone
import hashlib
import json


class Document(models.Model):
    """Main document model for uploaded PDFs."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.AutoField(primary_key=True)
    filename = models.CharField(max_length=500)
    file_path = models.FileField(upload_to='contracts/', max_length=500)
    file_hash = models.CharField(max_length=64, unique=True, db_index=True)
    file_size = models.BigIntegerField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    error_message = models.TextField(blank=True, null=True)
    
    uploaded_at = models.DateTimeField(default=timezone.now, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    page_count = models.IntegerField(null=True, blank=True)
    total_characters = models.IntegerField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['file_hash']),
            models.Index(fields=['status']),
            models.Index(fields=['-uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.filename} ({self.id})"
    
    def calculate_file_hash(self, file_obj):
        """Calculate SHA256 hash of the file."""
        sha256_hash = hashlib.sha256()
        for byte_block in iter(lambda: file_obj.read(4096), b""):
            sha256_hash.update(byte_block)
        file_obj.seek(0)  # Reset file pointer
        return sha256_hash.hexdigest()


class DocumentPage(models.Model):
    """Individual pages of a document."""
    
    id = models.AutoField(primary_key=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='pages')
    page_number = models.IntegerField()
    
    text_content = models.TextField()
    char_count = models.IntegerField()
    
    # Page metadata (bounding boxes, fonts, etc.)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'document_pages'
        ordering = ['document', 'page_number']
        unique_together = ['document', 'page_number']
        indexes = [
            models.Index(fields=['document', 'page_number']),
        ]
    
    def __str__(self):
        return f"{self.document.filename} - Page {self.page_number}"


class DocumentChunk(models.Model):
    """Chunked text from documents for RAG."""
    
    id = models.AutoField(primary_key=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    page = models.ForeignKey(DocumentPage, on_delete=models.CASCADE, related_name='chunks', null=True, blank=True)
    
    chunk_index = models.IntegerField()
    text_content = models.TextField()
    char_start = models.IntegerField()  # Start position in document
    char_end = models.IntegerField()    # End position in document
    
    # Vector database reference
    vector_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Chunk metadata (section headers, etc.)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'document_chunks'
        ordering = ['document', 'chunk_index']
        unique_together = ['document', 'chunk_index']
        indexes = [
            models.Index(fields=['document', 'chunk_index']),
            models.Index(fields=['vector_id']),
        ]
    
    def __str__(self):
        return f"{self.document.filename} - Chunk {self.chunk_index}"
