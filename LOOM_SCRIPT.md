# Loom Recording Script

## Pre-recording Checklist
- [ ] All services running (`make up`)
- [ ] Sample PDFs ready in `sample_contracts/`
- [ ] .env configured with OpenAI API key
- [ ] Browser open to `localhost:8000/api/docs`
- [ ] Terminal ready with pre-typed commands

---

## Recording Outline (8-10 minutes)

### 1. Introduction & Startup (1 min)
- "Hi, this is the Contract Intelligence API demo"
- Show project structure briefly
- Run `make up` in terminal
- Show all containers starting (api, postgres, qdrant, redis, celery)
- Quick overview: "Django REST API with vector RAG and risk auditing"

### 2. Swagger Documentation (1 min)
- Navigate to `http://localhost:8000/api/docs`
- Highlight all 7 endpoints:
  - `/api/ingest` - PDF upload
  - `/api/extract` - Field extraction
  - `/api/ask` - Q&A
  - `/api/ask/stream` - Streaming
  - `/api/audit` - Risk detection
  - `/api/healthz` - Health check
  - `/api/metrics` - Stats
- Open one endpoint (e.g., /ingest) to show auto-generated schema

### 3. Live Ingestion (2 min)
- Open terminal
- Show curl command OR use Swagger UI
```bash
curl -X POST http://localhost:8000/api/ingest \
  -F "files=@sample_contracts/nda.pdf" \
  -F "files=@sample_contracts/msa.pdf"
```
- Show response with document_ids: [1, 2]
- "Documents are now processing asynchronously via Celery"
- Show logs: `docker-compose logs -f celery_worker --tail=20`
- Point out: "PDF extraction, chunking, embedding generation, vector storage"

### 4. Field Extraction (1.5 min)
- Wait a few seconds for processing
- Call `/api/extract`:
```bash
curl -X POST http://localhost:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"document_id": 1}'
```
- Show extracted JSON output:
  - Parties
  - Effective date
  - Term
  - Governing law  
  - Auto-renewal (highlight this)
  - Liability cap
  - Signatories
- "This uses OpenAI GPT-4 with function calling for structured extraction"

### 5. RAG Q&A (1.5 min)
- Ask a question:
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the auto-renewal notice period?", "document_ids": [1]}'
```
- Show response with:
  - Answer text
  - Citations with document_id, page, char ranges
- "RAG pipeline: semantic search in Qdrant, then LLM answer with grounding"
- Ask another question to show it works

### 6. Contract Audit (2 min)
- Run audit on first document:
```bash
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"document_id": 1}'
```
- Show findings:
  - Risk type
  - Severity (highlight critical/high)
  - Evidence text
  - Recommendations
- "This uses hybrid audit: rules for patterns + LLM for nuanced risks"

### 7. Toggle Rule Engine & Show Different Output (1 min)
- Edit `.env`: Change `AUDIT_MODE=hybrid` to `AUDIT_MODE=rules_only`
- Restart API: `docker-compose restart api`
- Run audit again on same document
- Show different/fewer findings
- "Rules are fast and deterministic, LLM catches subtle issues, hybrid gives best coverage"
- Change back to `hybrid`

### 8. PII Redaction & Logs (0.5 min)
- Show logs: `docker-compose logs api --tail=30`
- Point out redacted entries:
  - `[REDACTED_EMAIL]` instead of actual email
  - `[REDACTED_PHONE]` for phone numbers
- "Middleware automatically redacts PII patterns in logs for compliance"

### 9. Metrics Endpoint (0.5 min)
- Call `/api/metrics`:
```bash
curl http://localhost:8000/api/metrics
```
- Show:
  - Total requests
  - Requests by endpoint
  - Avg response time
  - Documents ingested
  - Extraction success rate
- "Useful for monitoring and observability"

### 10. Tests & Edge Case (1 min)
- Open `tests/test_ingest.py` in editor
- Scroll through test cases:
  - Valid PDF
  - **Non-PDF rejection** (edge case)
  - **Duplicate detection** (edge case - same file hash returns same ID)
  - Multiple files
- Run tests:
```bash
docker-compose exec api python manage.py test tests.test_ingest
```
- Show passing tests
- Explain edge case: "We hash files to detect duplicates, preventing redundant processing and storage"

### 11. Wrap-up (0.5 min)
- "Full system demonstrated:"
  - ✓ PDF ingestion with async processing
  - ✓ Structured extraction
  - ✓ RAG Q&A with citations
  - ✓ Hybrid risk audit
  - ✓ Streaming, health, metrics
  - ✓ PII redaction
  - ✓ Comprehensive tests
- "See README.md and DESIGN.md for architecture details"
- "Repository includes eval/ for Q&A evaluation and prompts/ for LLM rationale"
- Thank you!

---

## Backup Commands (if something doesn't work live)

**If document processing takes too long:**
- Pre-ingest documents before recording
- Show already-processed document IDs

**If OpenAI API fails:**
- Have a backup `.env` with backup API key
- Or show cached extraction results

**If Qdrant connection fails:**
- Check health: `curl http://localhost:6333/health`
- Restart: `docker-compose restart qdrant`

---

## Key Points to Emphasize

1. **Production-ready patterns**: Async processing, error handling, caching
2. **Hybrid approach**: Rules + LLM for comprehensive coverage
3. **Grounded RAG**: Citations prevent hallucination
4. **Security**: PII redaction, file validation, hash-based dedup
5. **Observability**: Health checks, metrics, structured logging
6. **Testing**: Edge cases like duplicate detection
7. **Complete documentation**: README, DESIGN, prompts with rationale

---

## Technical Details to Mention

- Django REST Framework + Qdrant + PostgreSQL + Celery
- OpenAI GPT-4 for extraction/RAG/audit
- 800-token chunks with 100-token overlap
- Vector embeddings with cosine similarity
- HMAC webhook signatures (if time permits)
- Configurable audit modes (rules/llm/hybrid)
