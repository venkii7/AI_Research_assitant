# Lens API Reference

**Complete endpoint documentation with examples.**

---

## Base URL

```
http://localhost:8000    (development)
https://api.lens.dev     (production)
```

## Authentication

All endpoints except `/api/health` require a Supabase JWT token:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" ...
```

---

## Health & Status

### Check Service Health

```http
GET /api/health
```

**No auth required.**

**Response (200 OK):**
```json
{
  "status": "ok",
  "environment": "development",
  "redis": "ok",
  "supabase": "ok",
  "version": "1.0.0"
}
```

Possible values:
- `status`: "ok" | "degraded"
- `redis`: "ok" | "error: connection refused" | etc.
- `supabase`: "ok" | "error: ..." | etc.

---

## Papers — CRUD & Submission

### Submit a Paper (ArXiv ID or URL)

```http
POST /api/papers/process
Authorization: Bearer JWT_TOKEN
Content-Type: application/json

{
  "source": "1706.03762",
  "user_preferences": {
    "audience": "researcher",
    "depth": "expert",
    "explain_concepts": true,
    "max_concepts": 10
  }
}
```

**Query Parameters:** None

**Request Body:**
- `source` (required): ArXiv ID (e.g., "1706.03762"), URL (e.g., "https://arxiv.org/abs/1706.03762"), doi, or "upload"
- `user_preferences` (optional): Dict of user preferences

**Response (202 Accepted):**
```json
{
  "job_id": "8a7b4c5d-1e2f-4a9b-8c3d-2e1f4a9b8c3d",
  "paper_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "stream_url": "/api/stream/8a7b4c5d-1e2f-4a9b-8c3d-2e1f4a9b8c3d"
}
```

**Errors:**
- `400` — Invalid source format
- `402` — Free plan limit reached (5 papers/month)
- `401` — Unauthorized
- `415` — Unsupported format

**Rate Limit:** Free: 5/month, Pro: 200/day

---

### Upload a PDF

```http
POST /api/papers/upload
Authorization: Bearer JWT_TOKEN
Content-Type: multipart/form-data

[binary PDF file]
```

**Request:**
- `file` (required): PDF file (max 50MB)

**Response (202 Accepted):**
```json
{
  "job_id": "...",
  "paper_id": "...",
  "status": "queued",
  "stream_url": "/api/stream/..."
}
```

**Errors:**
- `413` — File too large (>50MB)
- `415` — Not a PDF

---

### List User's Papers

```http
GET /api/papers?status=done&limit=20&offset=0
Authorization: Bearer JWT_TOKEN
```

**Query Parameters:**
- `status` (optional): "queued" | "processing" | "done" | "failed"
- `limit` (optional, default 20): 1-100 results per page
- `offset` (optional, default 0): Pagination offset

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "auth-user-id",
    "arxiv_id": "1706.03762",
    "title": "Attention Is All You Need",
    "authors": "Vaswani et al.",
    "status": "done",
    "smart_brief": {
      "title": "Attention Is All You Need",
      "authors": "Vaswani et al.",
      "year": "2017",
      "paper_category": "ML",
      "tldr": "Introduced the Transformer architecture using self-attention, improving seq2seq models by 28.4 BLEU on WMT14.",
      "stat_cards": [
        {"label": "Test BLEU", "value": "28.4", "sub": "WMT14 En-De"},
        {"label": "Parameters", "value": "65M", "sub": "Base model"}
      ],
      "story": {
        "problem": "RNNs suffer from long-range dependencies due to sequential processing.",
        "method": "Replace RNNs entirely with multi-head self-attention and positional encoding.",
        "results": "Achieved 28.4 BLEU on WMT14 En-De with 6x faster training speed.",
        "significance": "Enabled transformer-based models that became the foundation of modern LLMs."
      },
      "concepts": ["attention", "transformer", "self-attention", "encoder-decoder"],
      "concept_explanations": {
        "attention": "A mechanism that weights input representations..."
      },
      "removed_sections": ["related work", "appendix"]
    },
    "processing_time_ms": 45000,
    "created_at": "2024-03-26T12:00:00Z",
    "updated_at": "2024-03-26T12:00:45Z"
  }
]
```

---

### Get Paper Details

```http
GET /api/papers/{paper_id}
Authorization: Bearer JWT_TOKEN
```

**Path Parameters:**
- `paper_id` (required): UUID of the paper

**Response (200 OK):** (Same format as list, single item)

**Errors:**
- `404` — Paper not found
- `401` — Unauthorized

---

### Delete a Paper

```http
DELETE /api/papers/{paper_id}
Authorization: Bearer JWT_TOKEN
```

**Response (204 No Content)** (Empty body)

**Errors:**
- `404` — Paper not found
- `401` — Unauthorized

---

## Streaming — Real-time Progress

### Stream Job Progress (SSE)

```http
GET /api/stream/{job_id}
Authorization: Bearer JWT_TOKEN
```

**Path Parameters:**
- `job_id` (required): Job ID from `/papers/process` response

**Response (200 OK):** Server-Sent Events stream

**Events:**

```
event: data
data: {"type": "connected", "job_id": "..."}

event: data
data: {"type": "thought", "content": "Reading paper structure...", "step": 1}

event: data
data: {"type": "tool_call", "tool": "read_pdf", "query": "arxiv:1706.03762"}

event: data
data: {"type": "progress", "pct": 25, "stage": "extracting text"}

event: data
data: {"type": "quality_check", "score": 0.82, "verdict": "PASS", "issues": []}

event: data
data: {"type": "done", "paper_id": "...", "brief": {...full SmartBrief...}}
```

**Event Types:**
- `connected` — SSE established
- `thought` — Agent reasoning trace
- `tool_call` — Agent called a tool
- `progress` — Stage update with percentage
- `quality_check` — Self-evaluation result
- `done` — Processing complete
- `failed` — Processing failed

**Stream closes after `done` or `failed`.**

**Keep-alive:** Heartbeat every 20 seconds (`: heartbeat\n\n`)

---

## Q&A — Chat on Papers

### Ask a Question

```http
POST /api/query
Authorization: Bearer JWT_TOKEN
Content-Type: application/json

{
  "paper_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "What is the main contribution of this paper?",
  "conversation_history": []
}
```

**Request Body:**
- `paper_id` (required): UUID of the paper
- `question` (required): 5-1000 character question
- `conversation_history` (optional, default []): Array of {role, content} for multi-turn

**Response (200 OK):** Server-Sent Events stream

**Events:**
```
event: data
data: {"type": "token", "content": "The main contribution"}

event: data
data: {"type": "token", "content": " is the introduction"}

...

event: data
data: {"type": "done"}
```

**Errors:**
- `404` — Paper doesn't exist
- `409` — Paper still processing (status != "done")
- `401` — Unauthorized

**Rate Limit:** Free: 20/day, Pro: 500/day

**Notes:**
- Streams answer token-by-token
- Uses paper's Smart Brief + full text as context
- Only works on completed papers

---

## Exports — Format Generation (Pro Only)

### Generate Alternative Format

```http
POST /api/exports
Authorization: Bearer JWT_TOKEN
Content-Type: application/json

{
  "paper_id": "550e8400-e29b-41d4-a716-446655440000",
  "format": "podcast_script"
}
```

**Request Body:**
- `paper_id` (required): UUID of the paper
- `format` (required): "podcast_script" | "tweet_thread" | "slide_deck" | "eli12" | "investor_memo"

**Response (200 OK):**
```json
{
  "paper_id": "550e8400-e29b-41d4-a716-446655440000",
  "format": "podcast_script",
  "content": "HOST: Welcome to Research Brief. Today we're discussing the Transformer model...",
  "word_count": 2847,
  "created_at": "2024-03-26T12:05:00Z"
}
```

**Errors:**
- `403` — Free plan (exports require Pro)
- `404` — Paper not found
- `409` — Paper not done processing

**Rate Limit:** Pro: 50/day

**Formats:**
- `podcast_script` — 5-minute episode (conversational)
- `tweet_thread` — 10-12 tweets (hook first)
- `slide_deck` — 8-10 slides with speaker notes
- `eli12` — Explain Like I'm 12 (no jargon)
- `investor_memo` — 1-pager (problem, market, solution, traction)

---

## Concepts — Explanations

### Get Concept Explanation

```http
POST /api/concepts
Authorization: Bearer JWT_TOKEN
Content-Type: application/json

{
  "paper_id": "550e8400-e29b-41d4-a716-446655440000",
  "concept": "attention mechanism",
  "depth": "standard"
}
```

**Request Body:**
- `paper_id` (required): UUID of the paper
- `concept` (required): Concept name
- `depth` (optional, default "standard"): "simple" | "standard" | "expert"

**Response (200 OK):**
```json
{
  "concept": "attention mechanism",
  "depth": "standard",
  "explanation": "A neural network technique where outputs are weighted combinations of inputs, allowing models to focus on relevant parts...",
  "analogy": "Like a person reading a sentence focusing on key words rather than each word equally.",
  "sources": ["https://example.com/attention", "..."],
  "cached": true
}
```

**Errors:**
- `403` — Free plan requesting non-standard depth
- `404` — Paper not found
- `401` — Unauthorized

**Notes:**
- Free users: `depth="standard"` only
- Pro users: all three depths
- Results cached for 30 days

---

## Memory — Agent Knowledge

### Get Memory Statistics

```http
GET /api/memory
Authorization: Bearer JWT_TOKEN
```

**Response (200 OK):**
```json
{
  "total_episodes": 342,
  "top_concepts": ["attention", "transformer", "BLEU score"],
  "recent_insights": [
    "CS papers usually have methods before results"
  ],
  "memory_types": {
    "paper_pattern": 89,
    "concept": 156,
    "domain_insight": 45,
    "failure_pattern": 52
  }
}
```

---

### Search Agent Memory

```http
GET /api/memory/search?query=transformer&memory_type=concept&top_k=5
Authorization: Bearer JWT_TOKEN
```

**Query Parameters:**
- `query` (required): Semantic search query
- `memory_type` (optional): "paper_pattern" | "concept" | "domain_insight" | "failure_pattern"
- `top_k` (optional, default 5): 1-20 results

**Response (200 OK):**
```json
{
  "results": [
    {
      "id": "...",
      "memory_type": "concept",
      "content": {
        "concept": "attention mechanism",
        "explanation": "..."
      },
      "relevance": 0.92
    }
  ],
  "query": "transformer"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "Human-readable error message",
  "code": "error_code",
  "details": {
    "field": "value"
  }
}
```

**Common Errors:**

| Status | Code | Message |
|--------|------|---------|
| 400 | validation_error | Invalid request format |
| 401 | unauthorized | Missing or invalid JWT |
| 402 | plan_limit_reached | Free plan limit exceeded |
| 403 | forbidden | Feature requires Pro plan |
| 404 | not_found | Paper/resource doesn't exist |
| 409 | processing_failed | Paper status invalid for operation |
| 413 | file_too_large | PDF exceeds 50MB |
| 415 | unsupported_format | Must be PDF or valid source |
| 429 | rate_limit | Too many requests, wait and retry |
| 500 | internal_error | Server error |

**Example Error Response:**

```json
{
  "error": "You have used 5 of 5 free papers this month",
  "code": "plan_limit_reached",
  "details": {
    "used": 5,
    "limit": 5,
    "plan": "free",
    "resets_at": "2024-04-01T00:00:00Z"
  }
}
```

---

## Rate Limits

**Free Plan:**
- Papers: 5/month
- Queries: 20/day
- Exports: 0/day (blocked)
- Concepts: unlimited (standard depth only)

**Pro Plan:**
- Papers: 200/day
- Queries: 500/day
- Exports: 50/day
- Concepts: unlimited (all depths)

**Headers Returned:**
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 2
X-RateLimit-Reset: 2024-04-01T00:00:00Z
```

When limit exceeded:
```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 2024-04-01T00:00:00Z

{
  "error": "Rate limit exceeded. Monthly limit: 5 papers. Resets 2024-04-01.",
  "code": "rate_limit"
}
```

---

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `limit` (default 20, max 100): Results per page
- `offset` (default 0): Starting position

**Example:**
```
GET /api/papers?limit=10&offset=20
```

Returns items 20-29.

---

## Content Types

### Request Content-Type
- `application/json` — JSON bodies
- `multipart/form-data` — File uploads

### Response Content-Type
- `application/json` — JSON responses
- `text/event-stream` — SSE streams

---

## Examples with cURL

### 1. Health Check
```bash
curl http://localhost:8000/api/health
```

### 2. Submit Paper
```bash
curl -X POST http://localhost:8000/api/papers/process \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source": "1706.03762"}'
```

### 3. Stream Progress
```bash
curl -N http://localhost:8000/api/stream/$JOB_ID \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Query Paper (WebSocket-like)
```bash
curl -N -X POST http://localhost:8000/api/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_id": "'$PAPER_ID'",
    "question": "What is the novelty?"
  }'
```

### 5. Generate Export
```bash
curl -X POST http://localhost:8000/api/exports \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_id": "'$PAPER_ID'",
    "format": "podcast_script"
  }'
```

---

## SDK Examples

### Python
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/papers/process",
        headers={"Authorization": f"Bearer {token}"},
        json={"source": "1706.03762"}
    )
    job_id = response.json()["job_id"]

    # Stream progress
    async with client.stream("GET", f"http://localhost:8000/api/stream/{job_id}",
        headers={"Authorization": f"Bearer {token}"}) as r:
        async for line in r.aiter_lines():
            print(line)
```

### JavaScript
```javascript
const token = "YOUR_JWT_TOKEN";

// Submit paper
const response = await fetch("http://localhost:8000/api/papers/process", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({ source: "1706.03762" })
});
const { job_id } = await response.json();

// Stream progress
const eventSource = new EventSource(
  `http://localhost:8000/api/stream/${job_id}`,
  { headers: { "Authorization": `Bearer ${token}` } }
);

eventSource.onmessage = (event) => {
  const event_data = JSON.parse(event.data);
  console.log(event_data);
};
```

---

## OpenAPI/Swagger

Visit `/docs` (development mode) to interact with API via Swagger UI.

Example:
```
http://localhost:8000/docs
```

All endpoints documented with request/response schemas.
