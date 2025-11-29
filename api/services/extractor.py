"""
Contract field extraction service using LLM.
"""

import logging
import json
import openai
from django.conf import settings
from typing import Dict, Any
from datetime import datetime
import re

logger = logging.getLogger('api')

# Initialize OpenAI
openai.api_key = settings.OPENAI_API_KEY


class ContractExtractor:
    """Service for extracting structured fields from contracts."""
    
    def __init__(self):
        self.model = settings.OPENAI_MODEL
    
    def extract_fields(self, document_text: str) -> Dict[str, Any]:
        """Extract all contract fields using LLM."""
        try:
            logger.info("Starting contract field extraction")
            
            # System prompt for extraction
            system_prompt = self._get_extraction_prompt()
            
            # Call OpenAI with function calling
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract contract fields from:\n\n{document_text[:15000]}"}  # Limit context
                ],
                functions=[self._get_extraction_schema()],
                function_call={"name": "extract_contract_fields"},
                temperature=0.1,
            )
            
            # Parse function call response
            function_call = response.choices[0].message.function_call
            extracted_data = json.loads(function_call.arguments)
            
            # Post-process and validate
            processed_data = self._post_process_extraction(extracted_data)
            
            logger.info("Contract field extraction completed successfully")
            return processed_data
            
        except Exception as e:
            logger.error(f"Contract extraction failed: {e}")
            # Return fallback extraction using regex
            return self._fallback_extraction(document_text)
    
    def _get_extraction_prompt(self) -> str:
        """Get system prompt for extraction."""
        return """You are a legal contract analyst. Extract the following fields from the contract:
        
- parties: Array of company/entity names mentioned as parties to the agreement
- effective_date: Effective date in ISO format (YYYY-MM-DD)
- term: Contract duration/term
- governing_law: Jurisdiction governing the contract
- payment_terms: Payment schedule and amounts
- termination: Termination conditions
- auto_renewal: Auto-renewal information including enabled status, notice days, and terms
- confidentiality: Key confidentiality obligations
- indemnity: Indemnification scope and details
- liability_cap: Liability cap with amount and currency
- signatories: Array of signatories with name and title

Return structured JSON. If a field is not found, use null."""
    
    def _get_extraction_schema(self) -> Dict:
        """Get OpenAI function schema for extraction."""
        return {
            "name": "extract_contract_fields",
            "description": "Extract structured fields from a legal contract",
            "parameters": {
                "type": "object",
                "properties": {
                    "parties": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of party names"
                    },
                    "effective_date": {
                        "type": "string",
                        "description": "Effective date in YYYY-MM-DD format"
                    },
                    "term": {
                        "type": "string",
                        "description": "Contract term/duration"
                    },
                    "governing_law": {
                        "type": "string",
                        "description": "Governing law jurisdiction"
                    },
                    "payment_terms": {
                        "type": "string",
                        "description": "Payment terms and schedule"
                    },
                    "termination": {
                        "type": "string",
                        "description": "Termination conditions"
                    },
                    "auto_renewal": {
                        "type": "object",
                        "properties": {
                            "enabled": {"type": "boolean"},
                            "notice_days": {"type": "integer"},
                            "terms": {"type": "string"}
                        }
                    },
                    "confidentiality": {
                        "type": "string",
                        "description": "Confidentiality obligations"
                    },
                    "indemnity": {
                        "type": "string",
                        "description": "Indemnification provisions"
                    },
                    "liability_cap": {
                        "type": "object",
                        "properties": {
                            "amount": {"type": "number"},
                            "currency": {"type": "string"}
                        }
                    },
                    "signatories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "title": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    
    def _post_process_extraction(self, data: Dict) -> Dict:
        """Post-process and validate extracted data."""
        processed = data.copy()
        
        # Convert date string to date object
        if processed.get('effective_date'):
            try:
                processed['effective_date'] = datetime.fromisoformat(processed['effective_date']).date()
            except (ValueError, TypeError):
                processed['effective_date'] = None
        
        # Ensure arrays are not None
        if not processed.get('parties'):
            processed['parties'] = []
        if not processed.get('signatories'):
            processed['signatories'] = []
        
        # Ensure objects have defaults
        if not processed.get('auto_renewal'):
            processed['auto_renewal'] = {}
        if not processed.get('liability_cap'):
            processed['liability_cap'] = {}
        
        return processed
    
    def _fallback_extraction(self, text: str) -> Dict:
        """Fallback extraction using regex patterns."""
        logger.info("Using fallback regex extraction")
        
        extracted = {
            'parties': [],
            'effective_date': None,
            'term': None,
            'governing_law': None,
            'payment_terms': None,
            'termination': None,
            'auto_renewal': {},
            'confidentiality': None,
            'indemnity': None,
            'liability_cap': {},
            'signatories': [],
        }
        
        # Try to extract dates
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(\d{4}-\d{2}-\d{2})'
        dates = re.findall(date_pattern, text)
        if dates:
            # Take first date as effective date
            date_str = dates[0][0] or dates[0][1]
            try:
                # Attempt to parse
                extracted['effective_date'] = datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                pass
        
        # Try to extract governing law
        gov_law_pattern = r'governed?\s+by\s+the\s+laws?\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        gov_law_match = re.search(gov_law_pattern, text, re.IGNORECASE)
        if gov_law_match:
            extracted['governing_law'] = gov_law_match.group(1)
        
        return extracted
