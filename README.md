# Contract Intelligence API

A production-ready contract analysis system with PDF ingestion, structured field extraction, RAG-based Q&A, and automated risk auditing.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/anurag26-q/contract-intelligence-api.git
   cd contract-intelligence-api
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Add your Google Gemini API key to `.env`**
   
   Open `.env` file and update:
   ```env
   GOOGLE_API_KEY=your-gemini-api-key-here
   ```
   
   > **Note**: Get your free Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

4. **Start all services**
   ```bash
   make up
   ```
   
   Or using docker-compose directly:
   ```bash
   docker-compose up -d
   ```
   
   This will start:
   - **API Server** (Django) on port 8000
   - **Redis** for caching and task queue
   - **Celery Worker** for async PDF processing
   - **Celery Beat** for scheduled tasks

5. **Wait for services to be ready** (30-60 seconds)
   
   Check service health:
   ```bash
   curl http://localhost:8000/api/healthz
   ```
   
   Expected response:
   ```json
   {
     "status": "healthy",
     "services": {
       "database": "healthy",
       "redis": "healthy"
     }
   }
   ```

6. **View API documentation**
   
   Navigate to: **http://localhost:8000/api/docs**
   
   You'll see interactive Swagger documentation for all endpoints.

---

## 📝 How to Use This Project Locally

### Step-by-Step Usage Guide

#### Step 1: Upload Contract PDFs

Upload one or more PDF contracts for processing:

```bash
curl -X POST http://localhost:8000/api/ingest \
  -F "files=@path/to/your/contract.pdf"
```

**Response:**
```json
{
  "success": true,
  "document_ids": [1],
  "message": "1 document(s) queued for processing"
}
```

> ⚠️ **IMPORTANT**: After uploading, **wait 30-60 seconds** for the Celery worker to process the document. The worker performs:
> - PDF text extraction
> - Text chunking
> - Embedding generation with Gemini
> - Vector storage in ChromaDB
>
> Check processing status by monitoring Celery logs:
> ```bash
> docker-compose logs -f celery_worker
> ```

#### Step 2: Check Document Status

Before querying, verify the document is processed:

```bash
# Check if document exists and is ready
curl -X POST http://localhost:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"document_id": 1}'
```

If you get an error about document not being processed, **wait a bit longer** and try again.

#### Step 3: Extract Contract Fields

Once processed, extract structured information:

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
    "parties": ["Company A", "Company B"],
    "effective_date": "2024-01-15",
    "term": "12 months",
    "governing_law": "Delaware",
    "payment_terms": "Net 30 days",
    "auto_renewal": {"enabled": true, "notice_days": 30},
    "liability_cap": {"amount": 100000, "currency": "USD"},
    "signatories": [{"name": "John Doe", "title": "CEO"}]
  }
}
```

#### Step 4: Ask Questions (RAG)

Ask natural language questions about your contracts:

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the termination notice period?",
    "document_ids": [1]
  }'
```

**Response:**
```json
{
  "success": true,
  "answer": "The termination notice period is 30 days...",
  "citations": [
    {
      "document_id": 1,
      "page_number": 5,
      "char_start": 1234,
      "char_end": 1456
    }
  ]
}
```

> 💡 **Tip**: Omit `document_ids` to search across all uploaded contracts

#### Step 5: Audit for Risks

Run automated risk detection:

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
      "title": "Short Auto-Renewal Notice Period",
      "description": "Contract auto-renews with insufficient notice",
      "evidence": "...automatically renew with 15 days notice...",
      "recommendation": "Negotiate for 30-60 days notice period"
    }
  ]
}
```

#### Step 6: Stream Responses (Optional)

For real-time streaming answers:

```bash
curl "http://localhost:8000/api/ask/stream?question=What%20are%20the%20payment%20terms&document_ids=1"
```

This returns Server-Sent Events (SSE) for progressive response display.

---

## ⏱️ Important Timing Notes

### Celery Worker Processing

After uploading documents via `/api/ingest`, the system uses **asynchronous processing** with Celery workers:

| Operation | Estimated Time | What's Happening |
|-----------|---------------|------------------|
| **Small PDF (1-5 pages)** | 10-30 seconds | Text extraction, chunking, embedding |
| **Medium PDF (10-20 pages)** | 30-60 seconds | Same as above, more chunks |
| **Large PDF (50+ pages)** | 1-3 minutes | Processing many chunks, API rate limits |

**Why the wait?**
- PDF text extraction with pdfplumber
- Text chunking (800 tokens with 100 overlap)
- Generating embeddings via Gemini API (768 dimensions)
- Storing vectors in ChromaDB
- Saving metadata to SQLite database

**How to monitor:**
```bash
# Watch Celery worker logs in real-time
docker-compose logs -f celery_worker

# Check document status in database
docker-compose exec api python manage.py shell
>>> from api.models import Document
>>> Document.objects.all().values('id', 'filename', 'status')
```

**Document Status Values:**
- `pending` - Just uploaded, waiting for processing
- `processing` - Currently being processed by Celery
- `completed` - Ready for extraction/queries
- `failed` - Processing error (check logs)

> ⚠️ **Common Mistake**: Trying to query a document immediately after upload will fail. Always wait for `status='completed'` before calling `/extract`, `/ask`, or `/audit`.

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
| `GOOGLE_API_KEY` | Google Gemini API key | **Required** |
| `GEMINI_MODEL` | Gemini model for extraction/QA | `gemini-2.0-flash-exp` |
| `GEMINI_EMBEDDING_MODEL` | Embedding model | `models/embedding-001` |
| `GEMINI_TEMPERATURE` | LLM temperature | `0.1` |
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
- **SQLite**: Document & extraction storage (lightweight, file-based)
- **ChromaDB**: Vector database for RAG (file-based, no separate service needed)
- **Redis + Celery**: Async task processing
- **Google Gemini**: LLM for extraction, RAG, and audit

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

### 1. **SQLite + ChromaDB vs. PostgreSQL + Qdrant**
- **Choice**: Lightweight file-based databases
- **Rationale**: Easier local development, no separate database services needed, perfect for demo/assignment
- **Trade-off**: Not suitable for high-concurrency production, but excellent for single-user/demo scenarios

### 2. **Hybrid Audit (Rules + LLM)**
- **Choice**: Both approaches
- **Rationale**: Rules are fast/deterministic, LLM catches nuanced risks
- **Trade-off**: Higher API cost, but comprehensive coverage

### 3. **Async Processing**
- **Choice**: Celery tasks for PDF processing
- **Rationale**: Don't block API responses, handle large PDFs gracefully
- **Trade-off**: Need to wait 30-60s for processing, requires monitoring

### 4. **Chunking Strategy**
- **Choice**: Recursive 800-token chunks with 100-token overlap
- **Rationale**: Balances context preservation with retrieval precision
- **Trade-off**: Some storage overhead from overlapping chunks

### 5. **Google Gemini vs. OpenAI**
- **Choice**: Google Gemini API
- **Rationale**: Free tier available, good performance, 768-dim embeddings
- **Trade-off**: Slightly different API patterns, but well-supported by LangChain

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
docker-compose logs -f celery_worker

# Look for errors in the worker output
# Common causes: Invalid Gemini API key, network issues, PDF corruption
```

**Issue**: ChromaDB errors or vector search not working
```bash
# Check if ChromaDB directory exists and has data
ls -la chroma_db/

# Restart services to reinitialize ChromaDB
docker-compose restart api celery_worker
```

**Issue**: "Invalid API key" or Gemini API errors
- Verify your `GOOGLE_API_KEY` in `.env` file
- Check your API key is active at https://makersuite.google.com/app/apikey
- Ensure you have API quota remaining (free tier has limits)

**Issue**: "No relevant documents found" when asking questions
- Wait for document processing to complete (check status)
- Verify documents were successfully ingested
- Check Celery worker logs for embedding errors

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
