"""
Audit engine for detecting risky clauses using LangChain with Google Gemini.
Hybrid approach: rule-based patterns + LLM analysis.
"""

import logging
import json
import re
from django.conf import settings
from typing import List, Dict

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

logger = logging.getLogger('api')


class AuditEngine:
    """Service for auditing contracts and detecting risks with LangChain Gemini."""
    
    def __init__(self):
        """Initialize audit engine with Gemini LLM."""
        self.audit_mode = settings.AUDIT_MODE
        
        # Initialize Gemini for LLM-based analysis
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.2,  # Slightly higher for creative risk detection
        )
        
        # Create audit prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a legal contract auditor. Analyze the contract for potential risks.

Identify risks in these categories:
1. Auto-renewal with inadequate notice period (<30 days)
2. Unlimited or uncapped liability
3. Overly broad indemnification
4. One-sided termination rights
5. Unfavorable payment terms
6. Weak confidentiality protections

For each risk, return JSON object with:
- risk_type: (auto_renewal|unlimited_liability|broad_indemnity|termination_imbalance|unfavorable_payment|weak_confidentiality|other)
- severity: (low|medium|high|critical)
- title: Brief title
- description: Concise explanation
- evidence: Exact quote from contract (max 200 chars)
- recommendation: Mitigation suggestion

Return ONLY valid JSON array of risk objects, no additional text."""),
            ("human", "Analyze this contract for risks:\\n\\n{contract_text}")
        ])
    
    def audit_contract(self, document_text: str, extracted_data: Dict = None) -> List[Dict]:
        """Audit contract for risks using hybrid approach."""
        findings = []
        
        if self.audit_mode in ['rules_only', 'hybrid']:
            # Run rule-based detection
            rule_findings = self._rule_based_audit(document_text, extracted_data)
            findings.extend(rule_findings)
            logger.info(f"Rule-based audit found {len(rule_findings)} issues")
        
        if self.audit_mode in ['llm_only', 'hybrid']:
            # Run LLM-based analysis
            llm_findings = self._llm_based_audit(document_text, extracted_data)
            findings.extend(llm_findings)
            logger.info(f"LLM-based audit found {len(llm_findings)} issues")
        
        # Deduplicate and sort by severity
        findings = self._deduplicate_findings(findings)
        findings = sorted(findings, key=lambda x: self._severity_rank(x['severity']), reverse=True)
        
        return findings
    
    def _rule_based_audit(self, text: str, extracted_data: Dict = None) -> List[Dict]:
        """Rule-based risk detection using patterns."""
        findings = []
        
        # Rule 1: Auto-renewal with < 30 day notice
        if extracted_data and extracted_data.get('auto_renewal', {}).get('enabled'):
            notice_days = extracted_data['auto_renewal'].get('notice_days', 0)
            if notice_days and notice_days < 30:
                findings.append({
                    'risk_type': 'auto_renewal',
                    'severity': 'high',
                    'title': 'Inadequate Auto-Renewal Notice Period',
                    'description': f'Contract auto-renews with only {notice_days} days notice.',
                    'evidence': extracted_data['auto_renewal'].get('terms', 'Auto-renewal clause detected'),
                    'recommendation': 'Negotiate for at least 30-60 days notice period.',
                    'detection_method': 'rules',
                    'rule_matched': 'auto_renewal_notice_period',
                })
        
        # Rule 2: Unlimited liability
        unlimited_liability_patterns = [
            r'unlimited\s+liability',
            r'without\s+limitation\s+of\s+liability',
            r'no\s+cap\s+on\s+liability',
        ]
        
        for pattern in unlimited_liability_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                match = re.search(pattern, text, re.IGNORECASE)
                evidence = text[max(0, match.start()-100):min(len(text), match.end()+100)]
                findings.append({
                    'risk_type': 'unlimited_liability',
                    'severity': 'critical',
                    'title': 'Unlimited Liability Exposure',
                    'description': 'Contract contains unlimited liability provisions.',
                    'evidence': evidence,
                    'recommendation': 'Negotiate for a liability cap (typically 12-24 months of fees).',
                    'detection_method': 'rules',
                    'rule_matched': 'unlimited_liability_pattern',
                })
                break
        
        # Rule 3: Broad indemnity
        broad_indemnity_patterns = [
            r'indemnify.*from\s+and\s+against\s+any\s+and\s+all',
            r'hold\s+harmless.*all\s+claims',
            r'indemnify.*without\s+limitation',
        ]
        
        for pattern in broad_indemnity_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                match = re.search(pattern, text, re.IGNORECASE)
                evidence = text[max(0, match.start()-100):min(len(text), match.end()+100)]
                findings.append({
                    'risk_type': 'broad_indemnity',
                    'severity': 'high',
                    'title': 'Overly Broad Indemnification',
                    'description': 'Indemnification clause may be too broad.',
                    'evidence': evidence,
                    'recommendation': 'Negotiate for mutual indemnification or limit scope.',
                    'detection_method': 'rules',
                    'rule_matched': 'broad_indemnity_pattern',
                })
                break
        
        return findings
    
    def _llm_based_audit(self, text: str, extracted_data: Dict = None) -> List[Dict]:
        """LLM-based comprehensive risk analysis using LangChain Gemini."""
        try:
            # Build LCEL chain
            audit_chain = self.prompt_template | self.llm | StrOutputParser()
            
            # Invoke with truncated text
            result = audit_chain.invoke({
                "contract_text": text[:10000]  # Limit to 10k chars
            })
            
            # Parse JSON from result
            cleaned_result = result.replace("```json", "").replace("```", "").strip()
            findings = json.loads(cleaned_result)
            
            # Ensure it's a list
            if isinstance(findings, dict) and 'findings' in findings:
                findings = findings['findings']
            elif not isinstance(findings, list):
                findings = [findings]
            
            # Add detection method
            for finding in findings:
                finding['detection_method'] = 'llm'
            
            logger.info(f"LLM audit completed with {len(findings)} findings")
            return findings
            
        except Exception as e:
            logger.error(f"LLM-based audit failed: {e}", exc_info=True)
            return []
    
    def _deduplicate_findings(self, findings: List[Dict]) -> List[Dict]:
        """Remove duplicate findings based on risk type and evidence similarity."""
        seen = {}
        unique_findings = []
        
        for finding in findings:
            key = (finding['risk_type'], finding.get('evidence', '')[:50])
            if key not in seen:
                seen[key] = True
                unique_findings.append(finding)
        
        return unique_findings
    
    def _severity_rank(self, severity: str) -> int:
        """Convert severity to numeric rank for sorting."""
        ranks = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1,
        }
        return ranks.get(severity, 0)
