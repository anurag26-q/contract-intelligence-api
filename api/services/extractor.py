"""
Contract field extraction service using LangChain with Google Gemini.
Uses structured output prompting instead of function calling.
"""

import logging
import json
from django.conf import settings
from typing import Dict, Any
from datetime import datetime
import re

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

logger = logging.getLogger('api')


class ContractExtractor:
    """Service for extracting structured fields from contracts using LangChain Gemini."""
    
    def __init__(self):
        """Initialize extractor with Gemini LLM."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.GEMINI_TEMPERATURE,
        )
        
        # Create extraction prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a legal contract analyst. Extract the following fields from the contract and return them as valid JSON:

{{
  "parties": ["list of company/entity names"],
  "effective_date": "YYYY-MM-DD or null",
  "term": "contract duration or null",
  "governing_law": "jurisdiction or null",
  "payment_terms": "payment schedule or null",
  "termination": "termination conditions or null",
  "auto_renewal": {{"enabled": true/false, "notice_days": number or null, "terms": "text or null"}},
  "confidentiality": "confidentiality obligations or null",
  "indemnity": "indemnification scope or null",
  "liability_cap": {{"amount": number or null, "currency": "currency code or null"}},
  "signatories": [{{"name": "name", "title": "title"}}]
}}

Return ONLY valid JSON, no additional text."""),
            ("human", "Extract contract fields from:\\n\\n{contract_text}")
        ])
    
    def extract_fields(self, document_text: str) -> Dict[str, Any]:
        """Extract all contract fields using LangChain Gemini."""
        try:
            logger.info("Starting contract field extraction via Gemini")
            
            # Build and invoke LCEL chain
            extraction_chain = self.prompt_template | self.llm | StrOutputParser()
            
            # Invoke with truncated text
            result = extraction_chain.invoke({
                "contract_text": document_text[:15000]  # Limit to first 15k chars
            })
            
            # Parse JSON from result
            # Clean potential markdown code blocks
            cleaned_result = result.replace("```json", "").replace("```", "").strip()
            extracted_data = json.loads(cleaned_result)
            
            # Post-process and validate
            processed_data = self._post_process_extraction(extracted_data)
            
            logger.info("Contract field extraction completed successfully")
            return processed_data
            
        except Exception as e:
            logger.error(f"Contract extraction failed: {e}", exc_info=True)
            # Return fallback extraction using regex
            return self._fallback_extraction(document_text)
    
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
            date_str = dates[0][0] or dates[0][1]
            try:
                extracted['effective_date'] = datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                pass
        
        # Try to extract governing law
        gov_law_pattern = r'governed?\s+by\s+the\s+laws?\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        gov_law_match = re.search(gov_law_pattern, text, re.IGNORECASE)
        if gov_law_match:
            extracted['governing_law'] = gov_law_match.group(1)
        
        return extracted
