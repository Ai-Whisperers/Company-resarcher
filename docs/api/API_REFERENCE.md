# API Reference

**Version**: 1.0.0
**Base URL**: `http://localhost:8000`

## Overview

The Company Researcher API provides a REST interface for initiating and monitoring company research tasks. Research is performed asynchronously, allowing you to start a task and poll for results.

## Quick Start

```bash
# Start a research task
curl -X POST http://localhost:8000/api/v1/research \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Adidas", "url": "https://adidas.com"}'

# Response: {"task_id": "abc-123", "status": "pending", "message": "..."}

# Check status
curl http://localhost:8000/api/v1/research/abc-123
```

## Authentication

Currently, the API does not require authentication. For production deployments, consider adding:
- API key authentication
- OAuth 2.0
- JWT tokens

## Rate Limiting

| Limit | Value |
|-------|-------|
| Requests per minute | 10 per IP |
| Max request body size | 1 MB |

When rate limited, you'll receive a `429 Too Many Requests` response.

## Endpoints

### Start Research

Start a new company research task.

```
POST /api/v1/research
```

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `company_name` | string | Yes | Name of the company to research (1-200 chars) |
| `url` | string | No | Company website URL |
| `industry` | string | No | Industry sector (max 100 chars) |
| `country` | string | No | Headquarters country (default: "USA") |

#### Example Request

```json
{
  "company_name": "Tesla",
  "url": "https://tesla.com",
  "industry": "Automotive",
  "country": "USA"
}
```

#### Response

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Research task started successfully."
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | Task created successfully |
| 400 | Invalid request (validation error) |
| 413 | Request body too large |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

---

### Get Task Status

Check the status of a research task.

```
GET /api/v1/research/{task_id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | string | UUID of the research task |

#### Response

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "company_name": "Tesla",
    "reports": [...],
    "sources": [...]
  },
  "error": null
}
```

#### Task Status Values

| Status | Description |
|--------|-------------|
| `pending` | Task queued, not yet started |
| `in_progress` | Research is running |
| `completed` | Research finished successfully |
| `failed` | Research failed (check `error` field) |

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | Task found |
| 404 | Task not found |
| 429 | Rate limit exceeded |

---

### Health Check

Basic health check endpoint.

```
GET /health
```

#### Response

```json
{
  "status": "healthy"
}
```

---

### Detailed Health Check

Comprehensive health check that verifies dependencies.

```
GET /health/detailed
```

#### Response

```json
{
  "status": "healthy",
  "checks": {
    "database": {"status": "ok"},
    "config": {"status": "ok"},
    "ai_provider": {"status": "ok"}
  }
}
```

#### Health Status Values

| Status | Description |
|--------|-------------|
| `healthy` | All systems operational |
| `degraded` | Some components have issues |
| `unhealthy` | Critical components failing |

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

### Common Errors

| Code | Error | Description |
|------|-------|-------------|
| 400 | Validation Error | Invalid request body |
| 404 | Task not found | Invalid task_id |
| 413 | Payload Too Large | Request body exceeds 1MB |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |

---

## Python Client Example

```python
import requests
import time

BASE_URL = "http://localhost:8000"

def research_company(company_name: str, url: str = None) -> dict:
    """
    Research a company and wait for results.

    Args:
        company_name: Name of the company
        url: Company website URL (optional)

    Returns:
        Research results dictionary
    """
    # Start research
    payload = {"company_name": company_name}
    if url:
        payload["url"] = url

    response = requests.post(
        f"{BASE_URL}/api/v1/research",
        json=payload
    )
    response.raise_for_status()
    task_id = response.json()["task_id"]

    print(f"Started task: {task_id}")

    # Poll for results
    while True:
        status_response = requests.get(
            f"{BASE_URL}/api/v1/research/{task_id}"
        )
        status_response.raise_for_status()

        status_data = status_response.json()
        status = status_data["status"]

        if status == "completed":
            return status_data["result"]
        elif status == "failed":
            raise Exception(f"Research failed: {status_data['error']}")

        print(f"Status: {status}, waiting...")
        time.sleep(10)


# Usage
if __name__ == "__main__":
    result = research_company("Apple", "https://apple.com")
    print(f"Research completed: {len(result.get('reports', []))} reports")
```

---

## JavaScript/TypeScript Client Example

```typescript
const BASE_URL = 'http://localhost:8000';

interface ResearchResult {
  task_id: string;
  status: string;
  result?: object;
  error?: string;
}

async function researchCompany(
  companyName: string,
  url?: string
): Promise<object> {
  // Start research
  const response = await fetch(`${BASE_URL}/api/v1/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      company_name: companyName,
      url
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to start research: ${response.status}`);
  }

  const { task_id } = await response.json();
  console.log(`Started task: ${task_id}`);

  // Poll for results
  while (true) {
    const statusResponse = await fetch(
      `${BASE_URL}/api/v1/research/${task_id}`
    );
    const statusData: ResearchResult = await statusResponse.json();

    if (statusData.status === 'completed') {
      return statusData.result!;
    } else if (statusData.status === 'failed') {
      throw new Error(`Research failed: ${statusData.error}`);
    }

    console.log(`Status: ${statusData.status}, waiting...`);
    await new Promise(resolve => setTimeout(resolve, 10000));
  }
}

// Usage
researchCompany('Microsoft', 'https://microsoft.com')
  .then(result => console.log('Research completed:', result))
  .catch(err => console.error('Error:', err));
```

---

## OpenAPI/Swagger Documentation

The API provides auto-generated interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## Configuration

The API can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `localhost:3000,localhost:8000` | Allowed CORS origins |
| `MAX_REQUEST_SIZE_BYTES` | `1000000` | Maximum request body size |
| `RESEARCH_TIMEOUT_SECONDS` | `1800` | Task timeout (30 min) |

---

## Running the API

```bash
# Development
uvicorn src.api.app:app --reload

# Production
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```
