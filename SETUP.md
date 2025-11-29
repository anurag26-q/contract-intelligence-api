# Project Setup Instructions

## Step 1: Prerequisites

Ensure you have installed:
- Docker Desktop (for Windows)
- Docker Compose
- Git
- An OpenAI API key

## Step 2: Clone and Configure

1. Navigate to the project directory:
   ```bash
   cd f:\Assignment
   ```

2. Copy the environment template:
   ```bash
   copy .env.example .env
   ```

3. Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

## Step 3: Start Services

Run the following command to start all services:
```bash
make up
```

This will start:
- PostgreSQL database
- Qdrant vector database
- Redis cache
- Django API server
- Celery worker
- Celery beat scheduler

## Step 4: Verify Installation

1. Check that all containers are running:
   ```bash
   docker-compose ps
   ```

2. Visit the API documentation:
   ```
   http://localhost:8000/api/docs
   ```

3. Check health status:
   ```bash
   curl http://localhost:8000/api/healthz
   ```

## Step 5: Add Sample Contracts

Place 3-5 public PDF contracts in the `sample_contracts/` directory. You can:
- Use the provided README for suggestions
- Find public contracts from SEC EDGAR
- Use open-source legal templates

## Step 6: Test the System

Run the test suite:
```bash
make test
```

## Step 7: Try the API

Follow the examples in README.md to:
1. Upload PDFs (`/api/ingest`)
2. Extract fields (`/api/extract`)
3. Ask questions (`/api/ask`)
4. Run audit (`/api/audit`)

## Troubleshooting

**Docker not starting:**
- Ensure Docker Desktop is running
- Check for port conflicts (5432, 6333, 6379, 8000)

**Database migrations:**
- If you see migration errors, run:
  ```bash
  make migrate
  ```

**Celery not processing:**
- Check logs: `docker-compose logs celery_worker`
- Verify Redis is running: `docker-compose ps redis`

**OpenAI errors:**
- Verify your API key in `.env`
- Check your OpenAI account has credits
- Try reducing `AUDIT_MODE` to `rules_only` to save API calls

## Next Steps

1. Review DESIGN.md for architecture details
2. Read prompts/ directory for LLM rationale
3. Run eval/run_eval.py for Q&A evaluation
4. Create Loom recording following LOOM_SCRIPT.md
