# Contract Intelligence API

A production-ready contract analysis system with PDF ingestion, structured field extraction, RAG-based Q&A, and automated risk auditing.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API Key

### Setup

1. **Clone and navigate to directory**
   ```bash
   cd contract-intelligence
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Add your OpenAI API key to `.env`**
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```

4. **Start all services**
   ```bash
   make up
   ```

5. **View API documentation**
   Navigate to: `http://localhost:8000/api/docs`

 That's it! The API is now running at `http://localhost:8000`

---

## 📋 API Endpoints

### 1. **POST /api/ingest** 
Upload 1 or more PDF contracts for processing.

```bash
curl -X POST http://localhost:8000/api/ingest \
  -F "files=@contract1.pdf" \
  -F "files=@contract2.pdf"
```

**Response:**
```json
{
  "success": true,
  "document_ids": [1, 2],
  "message": "2 document(s) queued for processing"
}
```

### 2. **POST /api/extract**
Extract structured fields from a contract.

```bash
curl -X POST http://localhost:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"document_id": 1}'
```

**Response:**
```json
{
  "success": true,
  "document_id": 1,
  "extraction": {
    "parties": ["Acme Corp", "Beta LLC"],
    "effective_date": "2024-01-15",
    "term": "12 months",
    "governing_law": "Delaware",
    "payment_terms": "Net 30",
    "auto_renewal": {"enabled": true, "notice_days": 30},
    "liability_cap": {"amount": 100000, "currency": "USD"},
    "signatories": [
      {"name": "John Doe", "title": "CEO"}
    ]
  }
}
```

### 3. **POST /api/ask**
Ask questions about uploaded contracts using RAG.

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the termination notice period?", "document_ids": [1]}'
```

**Response:**
```json
{
  "success": true,
  "answer": "The termination notice period is 30 days as stated in Section 8.2...",
  "citations": [
    {"document_id": 1, "page_number": 5, "char_start": 1234, "char_end": 1456}
  ]
}
```

### 4. **GET /api/ask/stream**
Stream answers using Server-Sent Events.

```bash
curl "http://localhost:8000/api/ask/stream?question=What%20are%20the%20payment%20terms&document_ids=1"
```

### 5. **POST /api/audit**
Audit contract for risky clauses.

```bash
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"document_id": 1}'
```

**Response:**
```json
{
  "success": true,
  "document_id": 1,
  "findings_count": 2,
  "findings": [
    {
      "risk_type": "auto_renewal",
      "severity": "high",
      "title": "Inadequate Auto-Renewal Notice Period",
      "description": "Contract auto-renews with only 15 days notice",
      "evidence": "...automatically renew with 15 days written notice...",
      "recommendation": "Negotiate for at least 30-60 days notice period"
    }
  ]
}
```

### 6. **GET /api/healthz**
Health check for all services.

```bash
curl http://localhost:8000/api/healthz
```

### 7. **GET /api/metrics**
Get API metrics and statistics.

```bash
curl http://localhost:8000/api/metrics
```

---

## 🔧 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | Model for extraction/QA | `gpt-4-turbo-preview` |
| `AUDIT_MODE` | Audit strategy | `hybrid` |
| `CHUNK_SIZE` | Token chunk size | `800` |
| `CHUNK_OVERLAP` | Token overlap | `100` |

**Audit Modes:**
- `rules_only`: Fast pattern matching
- `llm_only`: Comprehensive LLM analysis
- `hybrid`: Both (recommended)

---

## 🧪 Testing

### Run All Tests
```bash
make test
```

### Run Specific Tests
```bash
docker-compose exec api python manage.py test tests.test_ingest
```

### Run Q&A Evaluation
```bash
docker-compose exec api python eval/run_eval.py
```

---

## 🏗️ Architecture

See [DESIGN.md](DESIGN.md) for detailed architecture documentation.

**Key Components:**
- **Django REST Framework**: API layer
- **PostgreSQL**: Document & extraction storage
- **Qdrant**: Vector database for RAG
- **Redis + Celery**: Async task processing
- **OpenAI**: LLM for extraction, RAG, and audit

---

## 📁 Project Structure

```
contract-intelligence/
├── api/                    # Main API app
│   ├── models/            # Database models
│   ├── views/             # API endpoints
│   ├── services/          # Business logic
│   ├── serializers.py     # Request/response schemas
│   └── tasks.py           # Celery tasks
├── contract_intelligence/ # Django project
├── prompts/              # LLM prompts with rationale
├── eval/                 # Evaluation dataset & scripts
├── sample_contracts/     # Public contract samples
├── tests/                # Test suite
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 🎯 Design Trade-offs

### 1. **PostgreSQL + Qdrant vs. Single Vector DB**
- **Choice**: Separate databases
- **Rationale**: PostgreSQL for transactional data, Qdrant optimized for vector search
- **Trade-off**: Slightly more complex, but better performance

### 2. **Hybrid Audit (Rules + LLM)**
- **Choice**: Both approaches
- **Rationale**: Rules are fast/deterministic, LLM catches nuanced risks
- **Trade-off**: Higher cost, but comprehensive coverage

### 3. **Async Processing**
- **Choice**: Celery tasks for PDF processing
- **Rationale**: Don't block API responses
- **Trade-off**: Need webhook/polling for completion status

### 4. **Chunking Strategy**
- **Choice**: Recursive 800-token chunks with 100-token overlap
- **Rationale**: Balances context preservation with retrieval precision
- **Trade-off**: Some storage overhead

### 5. **OpenAI vs. Local Models**
- **Choice**: OpenAI GPT-4
- **Rationale**: Better accuracy out-of-the-box
- **Trade-off**: External dependency + API costs

---

##  🔒 Security

- **PII Redaction**: Automatic redaction in logs (emails, SSNs, phone numbers)
- **File Validation**: PDF format and size checks
- **Duplicate Detection**: SHA-256 hash to prevent re-processing
- **Non-root Container**: Docker runs as non-root user

---

## 🐛 Troubleshooting

**Issue**: Document stuck in "processing" status
```bash
# Check Celery logs
docker-compose logs celery_worker
```

**Issue**: Qdrant connection error
```bash
# Verify Qdrant is running
docker-compose ps qdrant
curl http://localhost:6333/health
```

**Issue**: Out of OpenAI credits
- Check your OpenAI account billing
- Consider using `AUDIT_MODE=rules_only` to reduce API calls

---

## 📊 Sample Contracts

See `sample_contracts/README.md` for information about the publicly available contracts used for testing.

---

## 🎬 Demo

See the Loom recording for a complete walkthrough:
- `make up` and service startup
- Swagger docs
- Live PDF ingestion
- Field extraction
- Q&A with citations
- Risk audit
- Audit mode toggle
- PII redaction in logs
- Metrics endpoint
- Running tests

---

## 🤝 Contributing

This is an assignment project. For a real production system, consider:
- Authentication/authorization
- Rate limiting
- Webhook system for completion notifications
- Document versioning
- Batch processing optimizations
- Cost tracking per document

---

## 📄 License

This is an assignment/demo project. Sample contracts are from public sources.

---

## 📞 Support

For questions about this implementation, see:
- [DESIGN.md](DESIGN.md) - Architecture details
- `prompts/` - LLM prompt rationale
- `eval/` - Evaluation methodology
- Swagger docs at `/api/docs`
