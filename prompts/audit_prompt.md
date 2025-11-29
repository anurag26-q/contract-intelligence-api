# Contract Audit Prompt

This prompt is used for LLM-based contract risk analysis as part of the hybrid audit engine.

## Prompt

```
Analyze the following contract for potential risks:

{contract_text}

Identify risks in these categories:
1. Auto-renewal with inadequate notice period (<30 days)
2. Unlimited or uncapped liability
3. Overly broad indemnification
4. One-sided termination rights
5. Unfavorable payment terms
6. Weak confidentiality protections

For each risk found, provide:
- risk_type: category name (use: auto_renewal, unlimited_liability, broad_indemnity, termination_imbalance, unfavorable_payment, weak_confidentiality, other)
- severity: low/medium/high/critical
- title: Brief title
- description: Concise explanation
- evidence: Exact text from contract (up to 200 chars)
- recommendation: Mitigation suggestion

Return as JSON array.
```

## Rationale

**Hybrid Approach**: This LLM-based audit complements rule-based detection:
- Rules are fast and deterministic for obvious patterns
- LLM catches nuanced risks that patterns might miss
- Together they provide comprehensive coverage

**Specific Categories**: We define 6 common contract risk categories based on legal best practices. This focuses the LLM's attention on actionable risks.

**Severity Levels**: Four-tier severity (low/medium/high/critical) helps prioritize review efforts.

**Evidence Requirement**: Requiring exact contract text evidence:
- Ensures the risk is real, not hallucinated
- Provides auditability
- Helps users locate the problematic clause

**Actionable Recommendations**: Each finding includes a mitigation suggestion, making the audit immediately useful for contract refinement.

**Temperature (0.2)**: Low temperature for consistency while allowing some reasoning flexibility.

## Example Output

```json
{
  "findings": [
    {
      "risk_type": "auto_renewal",
      "severity": "high",
      "title": "Inadequate Auto-Renewal Notice Period",
      "description": "Contract auto-renews with only 15 days notice",
      "evidence": "This Agreement shall automatically renew for successive one-year terms unless either party provides written notice of non-renewal at least 15 days before...",
      "recommendation": "Negotiate for at least 30-60 days notice period"
    }
  ]
}
```

## Configurable Audit Modes

The audit engine supports three modes via `AUDIT_MODE` environment variable:

1. **`rules_only`**: Fast, deterministic pattern matching only
2. **`llm_only`**: Comprehensive LLM analysis only
3. **`hybrid`** (default): Both approaches, deduplicated

**Trade-offs**:
- Rules: Fast, cheap, deterministic, but may miss nuanced risks
- LLM: Comprehensive, nuanced, but slower and costs API calls
- Hybrid: Best coverage, slightly slower, recommended for production

## Model: `gpt-4-turbo-preview`

We use GPT-4 Turbo for audit because:
- Better legal reasoning and risk assessment
- More reliable detection of subtle/implicit risks
- Higher quality recommendations
- Better adherence to structured output format
