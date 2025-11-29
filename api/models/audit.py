"""
Audit-related database models.
"""

from django.db import models
from django.utils import timezone
from .document import Document


class AuditFinding(models.Model):
    """Risk findings from contract audits."""
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    RISK_TYPE_CHOICES = [
        ('auto_renewal', 'Auto-Renewal Risk'),
        ('unlimited_liability', 'Unlimited Liability'),
        ('broad_indemnity', 'Broad Indemnity'),
        ('termination_imbalance', 'Termination Imbalance'),
        ('unfavorable_payment', 'Unfavorable Payment Terms'),
        ('weak_confidentiality', 'Weak Confidentiality'),
        ('other', 'Other'),
    ]
    
    id = models.AutoField(primary_key=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='audit_findings')
    
    risk_type = models.CharField(max_length=50, choices=RISK_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, db_index=True)
    
    title = models.CharField(max_length=500)
    description = models.TextField()
    recommendation = models.TextField(blank=True, null=True)
    
    # Evidence from contract
    evidence_text = models.TextField()
    char_start = models.IntegerField(null=True, blank=True)
    char_end = models.IntegerField(null=True, blank=True)
    page_number = models.IntegerField(null=True, blank=True)
    
    # Detection metadata
    detection_method = models.CharField(max_length=50, default='hybrid')  # rules, llm, hybrid
    rule_matched = models.CharField(max_length=200, blank=True, null=True)
    confidence_score = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'audit_findings'
        ordering = ['-severity', '-created_at']
        indexes = [
            models.Index(fields=['document']),
            models.Index(fields=['severity']),
            models.Index(fields=['risk_type']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_severity_display()} - {self.risk_type} in {self.document.filename}"
    
    def to_dict(self):
        """Convert to API response format."""
        return {
            'id': self.id,
            'risk_type': self.risk_type,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'recommendation': self.recommendation,
            'evidence': {
                'text': self.evidence_text,
                'char_start': self.char_start,
                'char_end': self.char_end,
                'page_number': self.page_number,
            },
            'detection_method': self.detection_method,
        }
