# Lens Backend — Development Guide

**Quick-start guide for local development.**

---

## Prerequisites

- **Python 3.11+** (check with `python --version`)
- **Upstash Redis** (free tier available at upstash.com)
- **Supabase** (free tier at supabase.com)
- **Cloudflare R2** bucket (optional, mock in dev)
- **Git** for version control

---

## Setup

### Step 1: Clone & Install

```bash
cd lens-agent-backend
pip install -r requirements.txt
```

### Step 2: Create `.env` File

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

**Minimal working `.env` for local dev:**

```env
ENVIRONMENT=development
LOG_LEVEL=INFO

# Get these from Supabase dashboard
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5...
SUPABASE_JWT_SECRET=your-super-secret-jwt-key

# Create a bucket in Supabase Storage (or use R2)
R2_ACCOUNT_ID=mock-account-id
R2_BUCKET_NAME=lens-papers
R2_ACCESS_KEY_ID=mock-access-key
R2_SECRET_ACCESS_KEY=mock-secret-key
R2_PUBLIC_URL=https://mock.example.com

# Get Upstash Redis URL (free tier at upstash.com)
UPSTASH_REDIS_URL=rediss://default:YOUR-PASSWORD@YOUR-HOST:6379
```

**For local testing with mocks (if you don't have external services):**
- Mock Supabase with `unittest.mock`
- Mock Redis with fakeredis
- Mock R2 with local file storage

---

## Running the Server

### Development Mode (with auto-reload)

```bash
make dev
```

Output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

Visit:
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Health Check:** http://localhost:8000/api/health

### Production Mode (single process)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

### Production Mode (multiple workers)

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## Testing the API

### Health Check

```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "ok",
  "environment": "development",
  "redis": "ok",
  "supabase": "ok",
  "version": "1.0.0"
}
```

### Submit a Paper

First, you need a valid JWT token. In development, you can use a test token, or get one from Supabase Auth.

```bash
curl -X POST http://localhost:8000/api/papers/process \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "1706.03762",
    "user_preferences": {}
  }'
```

Response (202 Accepted):
```json
{
  "job_id": "8a7b4c5d-1e2f-4a9b-8c3d-2e1f4a9b8c3d",
  "paper_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "stream_url": "/api/stream/8a7b4c5d-1e2f-4a9b-8c3d-2e1f4a9b8c3d"
}
```

### Stream Progress

In another terminal:

```bash
curl -N http://localhost:8000/api/stream/8a7b4c5d-1e2f-4a9b-8c3d-2e1f4a9b8c3d \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Output (SSE format):
```
data: {"type": "connected", "job_id": "..."}

data: {"type": "progress", "step": 1, "status": "initializing", "message": "Paper job initialized"}

data: {"type": "done", "paper_id": "...", "brief": {...}}
```

### List Papers

```bash
curl http://localhost:8000/api/papers \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Getting a Test JWT Token

### Option 1: Use Supabase Auth

Sign up at supabase.com, create a project, then:

```bash
curl -X POST https://YOUR-PROJECT.supabase.co/auth/v1/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#"
  }'
```

Extract the `access_token` from the response.

### Option 2: Create a Mock Token (for testing)

```python
import jwt
from datetime import datetime, timedelta

secret = "your-super-secret-jwt-key"
payload = {
    "sub": "test-user-id",
    "email": "test@example.com",
    "iat": datetime.utcnow(),
    "exp": datetime.utcnow() + timedelta(hours=24),
    "aud": "authenticated",
}
token = jwt.encode(payload, secret, algorithm="HS256")
print(token)  # Use this in Authorization header
```

---

## Running Tests

### All Tests

```bash
make test
```

### Specific Test File

```bash
pytest tests/test_papers.py -v
```

### Specific Test Function

```bash
pytest tests/test_papers.py::test_health_check -v
```

### With Coverage

```bash
pytest tests/ --cov=. --cov-report=html
# Open htmlcov/index.html
```

---

## Code Style & Linting

### Format Code

```bash
make lint
```

Uses Ruff for formatting and linting.

### Check (without fixing)

```bash
ruff check .
```

---

## Database Schema

The backend expects these tables in PostgreSQL (Supabase):

```sql
-- Papers table
CREATE TABLE papers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  arxiv_id TEXT,
  title TEXT,
  status TEXT NOT NULL DEFAULT 'queued',
  smart_brief JSONB,
  pdf_path TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  supabase_auth_id TEXT UNIQUE,
  email TEXT,
  plan TEXT DEFAULT 'free',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Exports table (optional)
CREATE TABLE exports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  paper_id UUID NOT NULL REFERENCES papers(id),
  format TEXT NOT NULL,
  output_text TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

See [Supabase SQL Editor](https://app.supabase.com) to run these queries.

---

## Debugging

### Enable Debug Logging

In `.env`:
```env
LOG_LEVEL=DEBUG
```

### Print Request/Response in Route

```python
@router.get("/debug")
async def debug():
    import logging
    logger = logging.getLogger("lens.api")
    logger.debug("This is a debug message")
    return {"debug": True}
```

### Use FastAPI Docs

Visit http://localhost:8000/docs to:
- See all endpoints
- Try endpoints with "Try it out" button
- View request/response schemas

### Inspect Redis

If using Upstash:
1. Go to https://console.upstash.com/redis
2. Click your database
3. Use Redis CLI or REST API to inspect keys

Example:
```bash
curl https://YOUR-UPSTASH-URL/get/job:abc-123 \
  -u default:YOUR-PASSWORD
```

### Inspect Supabase

1. Go to https://app.supabase.com
2. Select your project
3. Go to SQL Editor
4. Query tables directly

```sql
SELECT * FROM papers WHERE user_id = 'test-user-id';
SELECT * FROM users LIMIT 10;
```

---

## Common Development Tasks

### Task: Add a New Endpoint

1. Create route in a new file or existing `api/routes/` file
2. Define request model in `models/requests.py`
3. Define response model in `models/responses.py`
4. Add tests in `tests/test_*.py`
5. Register router in `main.py`

Example:

```python
# api/routes/new_feature.py
from fastapi import APIRouter
from models.requests import MyRequest
from models.responses import MyResponse

router = APIRouter(prefix="/api/feature", tags=["feature"])

@router.post("", response_model=MyResponse)
async def my_feature(request: MyRequest):
    return {"result": "done"}

# main.py - add:
from api.routes import new_feature
app.include_router(new_feature.router)
```

### Task: Add a Database Query

```python
# services/supabase_client.py
async def get_my_data(user_id: str) -> dict:
    result = supabase.table("my_table")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    return result.data[0] if result.data else None

# Use in route:
from services.supabase_client import get_my_data

@router.get("/{id}")
async def get_item(id: str):
    data = await get_my_data(id)
    return data
```

### Task: Add a Dependency

```python
# api/dependencies.py
async def my_custom_check(user: dict = Depends(require_user_record)) -> dict:
    if user.get("plan") != "pro":
        raise HTTPException(status_code=403, detail="Needs pro plan")
    return user

# Use in route:
@router.post("/pro-only")
async def pro_feature(checked_user: dict = Depends(my_custom_check)):
    return {"status": "ok"}
```

---

## Environment Variables Reference

| Variable | Required | Example |
|----------|----------|---------|
| `ENVIRONMENT` | No | development or production |
| `LOG_LEVEL` | No | INFO, DEBUG, WARNING |
| `SUPABASE_URL` | Yes | https://xxx.supabase.co |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | eyJ... (long JWT) |
| `SUPABASE_JWT_SECRET` | Yes | your-secret-key |
| `UPSTASH_REDIS_URL` | Yes | rediss://default:pass@host:6379 |
| `R2_ACCOUNT_ID` | Yes | xxx (Cloudflare account) |
| `R2_BUCKET_NAME` | Yes | lens-papers |
| `R2_ACCESS_KEY_ID` | Yes | xxx |
| `R2_SECRET_ACCESS_KEY` | Yes | xxx |
| `R2_PUBLIC_URL` | Yes | https://pub-xxx.r2.dev |
| `GROQ_API_KEY` | No | gsk_xxx (for workers) |
| `GEMINI_API_KEY` | No | AIzaSy... (for workers) |
| `MAX_PDF_SIZE_MB` | No | 50 |
| `MAX_FREE_PAPERS_PER_MONTH` | No | 5 |

---

## Troubleshooting

### "Import 'fastapi' could not be resolved"

Run `pip install -r requirements.txt`. VS Code Pylance may need a restart after installing.

### "ConnectionError: Cannot connect to Redis"

- Check `UPSTASH_REDIS_URL` in `.env`
- Verify Redis instance is running at that URL
- Test: `redis-cli -u rediss://... ping`

### "AuthApiError: Invalid credentials"

- Check `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
- Verify your Supabase project is active
- Generate a new service role key if needed

### Tests fail with "module not found"

```bash
pip install -r requirements.txt
pytest tests/ -v
```

### "TypeError: object is not awaitable"

Make sure route handler is `async def` and uses `await` on async functions like:
```python
# ❌ Wrong
result = supabase_client.get_paper(...)

# ✅ Correct
result = await supabase_client.get_paper(...)
```

---

## Performance Tips

1. **Enable query caching** in Redis for frequently accessed papers
2. **Use connection pooling** for Supabase (already configured)
3. **Compress SSE responses** with gzip middleware
4. **Index frequently queried columns** in PostgreSQL (`user_id`, `status`)
5. **Monitor request latency** via structured JSON logs

---

## Production Deployment

When ready to deploy:

1. Set `ENVIRONMENT=production` in `.env`
2. Disable Swagger docs: set `docs_url=None` in `main.py`
3. Use a WSGI server (Gunicorn) with multiple workers
4. Set up SSL/TLS via reverse proxy (nginx, Caddy)
5. Enable CORS with production domain
6. Run `make test` — all tests passing
7. Set up monitoring and alerting
8. Enable database backups

Example Gunicorn command:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Getting Help

- **FastAPI docs:** https://fastapi.tiangolo.com
- **Pydantic docs:** https://docs.pydantic.dev
- **Supabase docs:** https://supabase.com/docs
- **Upstash Redis docs:** https://upstash.com/docs/redis/overview
- **Pytest docs:** https://docs.pytest.org
