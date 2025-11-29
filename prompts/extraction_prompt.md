# Contract Extraction Prompt

This prompt is used for structured field extraction from legal contracts using OpenAI's function calling API.

## Prompt

```
You are a legal contract analyst. Extract the following fields from the contract:

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

Return structured JSON. If a field is not found, use null.
```

## Rationale

**Function Calling**: We use OpenAI's function calling feature to ensure structured JSON output, which reduces parsing errors and ensures consistency. The schema is strictly defined with types and descriptions.

**Field Selection**: These fields represent the most critical contract elements:
- **Parties & Signatories**: Essential for understanding who is bound by the agreement
- **Dates & Term**: Critical for understanding contract timeline and obligations
- **Payment Terms**: Financial commitments
- **Termination & Auto-Renewal**: Exit conditions and automatic renewals (often risky)
- **Liability Cap**: Financial risk limitation
- **Indemnity & Confidentiality**: Legal protections

**Temperature (0.1)**: We use a very low temperature for extraction to ensure deterministic, factually grounded outputs without hallucinations.

**Fallback Strategy**: If LLM extraction fails, we fall back to regex-based extraction for dates and governing law, providing resilience.

## Example Function Schema

```json
{
  "name": "extract_contract_fields",
  "parameters": {
    "type": "object",
    "properties": {
      "parties": {"type": "array", "items": {"type": "string"}},
      "effective_date": {"type": "string"},
      "term": {"type": "string"},
      "governing_law": {"type": "string"},
      "payment_terms": {"type": "string"},
      "termination": {"type": "string"},
      "auto_renewal": {
        "type": "object",
        "properties": {
          "enabled": {"type": "boolean"},
          "notice_days": {"type": "integer"},
          "terms": {"type": "string"}
        }
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
```

## Model: `gpt-4-turbo-preview`

We use GPT-4 Turbo for extraction due to its:
- Strong instruction following
- Large context window (128k tokens)
- Better understanding of legal terminology
- Reliable function calling support
