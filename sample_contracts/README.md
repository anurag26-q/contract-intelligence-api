# Sample Contracts

This directory contains publicly available contract samples used for testing and demonstration.

## Contracts Included

All contracts are sourced from public repositories and contain no proprietary information.

### Planned Sources

1. **Non-Disclosure Agreement (NDA)**
   - Source: [GitHub Legal Templates](https://github.com/github/legal-forms)
   - Type: Mutual NDA
   - Purpose: Test confidentiality clause extraction

2. ** Master Service Agreement (MSA)**
   - Source: SEC EDGAR filings or open-source templates
   - Type: B2B service agreement
   - Purpose: Test complex clause extraction (payment, termination, liability)

3. **SaaS Subscription Agreement**
   - Source: Open-source legal template repositories
   - Type: Software subscription
   - Purpose: Test auto-renewal detection and audit

4. **Employment Agreement**
   - Source: Public domain templates
   - Type: Standard employment contract
   - Purpose: Test party/signatory extraction

5. **License Agreement**
   - Source: Open-source software licenses
   - Type: Software or IP license
   - Purpose: Test governing law and indemnity clauses

## How to Add Contracts

Place PDF files in this directory. Ensure they are:
- Publicly available (no proprietary data)
- In PDF format
- Readable (not scanned images without OCR)
- Under 50MB

## Attribution

Each contract should be properly attributed to its source. See `ATTRIBUTIONS.md` for details.

## Usage in Tests

These contracts are used in:
- Integration tests (`tests/` directory)
- Q&A evaluation dataset (`eval/qa_eval_dataset.json`)
- Demo recordings (Loom video)

## Download Script

Run `python scripts/download_samples.py` to automatically download sample contracts from verified public sources.

---

**Note**: Due to this being a demonstration/assignment, we recommend using 3-5 simple, publicly available contracts. Complex proprietary agreements should never be used.
