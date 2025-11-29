"""
Contract extraction-related database models.
"""

from django.db import models
from django.utils import timezone
from .document import Document


class ContractExtraction(models.Model):
    """Structured field extraction from contracts."""
    
    id = models.AutoField(primary_key=True)
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='extraction')
    
    # Extracted fields stored as JSON
    parties = models.JSONField(default=list, blank=True)  # List of party names
    effective_date = models.DateField(null=True, blank=True)
    term = models.CharField(max_length=500, blank=True, null=True)
    governing_law = models.CharField(max_length=500, blank=True, null=True)
    payment_terms = models.TextField(blank=True, null=True)
    termination = models.TextField(blank=True, null=True)
    auto_renewal = models.JSONField(default=dict, blank=True)  # {enabled: bool, notice_days: int, terms: str}
    confidentiality = models.TextField(blank=True, null=True)
    indemnity = models.TextField(blank=True, null=True)
    liability_cap = models.JSONField(default=dict, blank=True)  # {amount: float, currency: str}
    signatories = models.JSONField(default=list, blank=True)  # List of {name: str, title: str}
    
    # Raw extraction data (full LLM response)
    raw_extraction = models.JSONField(default=dict, blank=True)
    
    # Extraction metadata
    model_used = models.CharField(max_length=100, blank=True, null=True)
    extraction_method = models.CharField(max_length=50, default='llm')  # llm, regex, hybrid
    confidence_score = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contract_extractions'
        indexes = [
            models.Index(fields=['document']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Extraction for {self.document.filename}"
    
    def to_dict(self):
        """Convert to API response format."""
        return {
            'document_id': self.document.id,
            'parties': self.parties,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'term': self.term,
            'governing_law': self.governing_law,
            'payment_terms': self.payment_terms,
            'termination': self.termination,
            'auto_renewal': self.auto_renewal,
            'confidentiality': self.confidentiality,
            'indemnity': self.indemnity,
            'liability_cap': self.liability_cap,
            'signatories': self.signatories,
        }
