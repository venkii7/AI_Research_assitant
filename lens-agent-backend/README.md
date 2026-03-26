# Lens FastAPI Backend

A production-ready async REST API that serves as the interface between the frontend and the Lens AI research agent pipeline.

## Overview

The Lens backend handles:
- **Paper Ingestion** — Submit papers via ArXiv ID, URL, or PDF upload
- **Job Queuing** — Async paper processing via Redis-backed job queue
- **Real-time Streaming** — Server-Sent Events for agent progress updates
- **Q&A Chat** — Ask questions about processed papers
- **Export Generation** — Convert briefs to podcast scripts, tweet threads, etc.
- **Rate Limiting** — Per-plan request limits (free/pro)
- **Authentication** — Supabase JWT verification

## Quick Start

### Prerequisites
- Python 3.11+
- Redis (Upstash Redis)
- PostgreSQL (Supabase)
- Cloudflare R2 bucket

### Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in values
3. Install dependencies:
```bash
make install
```

4. Run the development server:
```bash
make dev
```

Server runs on `http://localhost:8000` with docs at `/docs`.

### Running Tests

```bash
make test
```

### Health Check

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "environment": "development",
  "redis": "ok",
  "supabase": "ok",
  "version": "1.0.0"
}
```

## API Endpoints

### Papers

- **POST /api/papers/process** — Submit paper (ArXiv ID or URL)
- **POST /api/papers/upload** — Upload PDF file
- **GET /api/papers** — List user's papers
- **GET /api/papers/{id}** — Get paper details
- **DELETE /api/papers/{id}** — Delete a paper

### Streaming

- **GET /api/stream/{job_id}** — Server-Sent Events for job progress

### Q&A

- **POST /api/query** — Ask a question about a paper

### Exports

- **POST /api/exports** — Generate alternative format (pro users only)

### Concepts

- **POST /api/concepts** — Get concept explanation

### Memory

- **GET /api/memory** — Agent memory stats
- **GET /api/memory/search** — Semantic search over agent memories

## Architecture

```
main.py                    ← FastAPI app entrypoint
├── api/
│   ├── middleware.py      ← CORS, logging, error handling
│   ├── dependencies.py    ← Auth, rate limiting, user checks
│   └── routes/            ← All endpoint handlers
├── services/              ← External service integrations
│   ├── supabase_client.py ← Database operations
│   ├── redis_client.py    ← Redis pub/sub
│   ├── storage.py         ← R2 file storage
│   └── job_queue.py       ← Job queue operations
├── models/                ← Pydantic request/response models
├── core/                  ← Configuration, security, auth
└── workers/               ← Background job processors
```

## Environment Variables

See `.env.example` for complete list. Key variables:

- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` — Database and auth
- `UPSTASH_REDIS_URL` — Redis connection
- `R2_*` — Cloudflare R2 storage credentials
- `GROQ_API_KEY`, `GEMINI_API_KEY` — LLM APIs

## Development

### Code Style
```bash
make lint    # Ruff format + check
```

### Database Setup
```bash
make db-setup
```

### Clean
```bash
make clean   # Remove cache, pycache, etc
```

## Deployment

### Docker

```bash
docker-compose up -d
```

### Production Checklist
- [ ] `.env` filled with production values
- [ ] `ENVIRONMENT=production` in `.env`
- [ ] All LLM API keys configured
- [ ] Redis and Postgres backups enabled
- [ ] SSL/TLS certificates (via reverse proxy)
- [ ] Rate limiting configured per tier
- [ ] Monitoring/logging setup (structured JSON)

## Testing

Run full test suite:
```bash
pytest tests/ -v --asyncio-mode=auto
```

Test specific endpoint:
```bash
pytest tests/test_papers.py -v
```

## Integration with Agent

The backend is designed to integrate with the Lens agent pipeline. The `workers/paper_worker.py` processes jobs from Redis queue and invokes the agent core. See `lens-agent/` repo for agent implementation.

## License

MIT
