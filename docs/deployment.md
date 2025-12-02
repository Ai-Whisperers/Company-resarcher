# Deployment Guide

This guide covers deploying Company Researcher in various environments.

## Quick Start

### Local Development

```bash
# Clone and setup
git clone https://github.com/ai-whisperers/Company-researcher.git
cd Company-researcher

# Install dependencies
pip install -e .
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run API server
uvicorn src.api.app:app --reload --port 8000

# Or run CLI
python main.py --name "Company Name" --url "https://company.com"
```

### Docker Deployment

```bash
# Build image
docker build -t company-researcher .

# Run with environment file
docker run -p 8000:8000 --env-file .env company-researcher

# Or use docker-compose
docker-compose up -d
```

## Environment Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_KEY` | API authentication key | `your-secure-key` |
| `OPENAI_API_KEY` | OpenAI API key (or other AI provider) | `sk-...` |

### AI Provider Keys (at least one required)

```bash
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=gsk_your-key
```

### Optional Configuration

```bash
# Application
OUTPUT_DIR=outputs
DB_PATH=tasks.db
LOG_DIR=.

# Performance
SEARCH_TIMEOUT_SECONDS=30
LLM_TIMEOUT_SECONDS=120
AGENT_MAX_CONCURRENT_QUERIES=5

# Security
SECURITY_BLOCK_INJECTION=true
SECURITY_MIN_BLOCK_LEVEL=medium

# Observability
PROMETHEUS_ENABLED=true
OTEL_ENABLED=true
```

## Docker Deployment

### Single Container

```bash
# Build
docker build -t company-researcher:latest .

# Run API
docker run -d \
  --name company-researcher \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/data:/app/data \
  company-researcher:latest
```

### Docker Compose

```bash
# Standard deployment
docker-compose up -d

# With Redis cache
docker-compose --profile cache up -d

# With monitoring (Prometheus)
docker-compose --profile monitoring up -d

# Run CLI for batch research
docker-compose run cli --batch research_targets/my_market/
```

### Resource Requirements

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| API Server | 2 cores | 4GB | 1GB |
| CLI Runner | 2 cores | 4GB | 1GB |
| Redis (optional) | 0.5 cores | 512MB | 100MB |

## Kubernetes Deployment

### Basic Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: company-researcher
spec:
  replicas: 2
  selector:
    matchLabels:
      app: company-researcher
  template:
    metadata:
      labels:
        app: company-researcher
    spec:
      containers:
      - name: api
        image: company-researcher:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: company-researcher-secrets
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
          requests:
            cpu: "500m"
            memory: "1Gi"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        volumeMounts:
        - name: outputs
          mountPath: /app/outputs
      volumes:
      - name: outputs
        persistentVolumeClaim:
          claimName: researcher-outputs
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: company-researcher
spec:
  selector:
    app: company-researcher
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: company-researcher-secrets
type: Opaque
stringData:
  API_KEY: "your-api-key"
  OPENAI_API_KEY: "sk-..."
```

## Health Checks

The API exposes several health endpoints:

| Endpoint | Purpose | Use Case |
|----------|---------|----------|
| `GET /health` | Basic health | Load balancers |
| `GET /health/live` | Liveness probe | K8s liveness |
| `GET /health/ready` | Readiness probe | K8s readiness |
| `GET /health/detailed` | Full diagnostics | Debugging |
| `GET /metrics` | Prometheus metrics | Monitoring |

### Health Check Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-01T12:00:00Z",
  "uptime_seconds": 3600.5
}
```

## Security Hardening

### Production Checklist

- [ ] Generate secure `API_KEY` with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] Enable HTTPS via reverse proxy (nginx, traefik)
- [ ] Set `SECURITY_BLOCK_INJECTION=true`
- [ ] Configure CORS origins appropriately
- [ ] Use non-root container user (default in Dockerfile)
- [ ] Enable vault encryption for sensitive data
- [ ] Set up network policies in Kubernetes
- [ ] Enable rate limiting at load balancer

### Reverse Proxy (nginx)

```nginx
server {
    listen 443 ssl;
    server_name api.yourcompany.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    location / {
        proxy_pass http://company-researcher:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running research
        proxy_read_timeout 1800s;
        proxy_connect_timeout 60s;
    }
}
```

## Monitoring Setup

### Prometheus

The `/metrics` endpoint exposes Prometheus metrics:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'company-researcher'
    static_configs:
      - targets: ['api:8000']
    metrics_path: /metrics
    scrape_interval: 10s
```

### Key Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `research_requests_total` | Counter | Total research requests |
| `research_duration_seconds` | Histogram | Research duration |
| `ai_requests_total` | Counter | AI provider requests |
| `circuit_breaker_state` | Gauge | Circuit breaker status |

### Alerting (example)

```yaml
groups:
- name: company-researcher
  rules:
  - alert: HighErrorRate
    expr: rate(research_requests_total{status="error"}[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High research error rate

  - alert: CircuitBreakerOpen
    expr: circuit_breaker_state{state="open"} == 1
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: Circuit breaker {{ $labels.name }} is open
```

## Scaling Considerations

### Horizontal Scaling

- API is stateless - scale horizontally with load balancer
- Use Redis for shared caching across instances
- Database (SQLite) should be migrated to PostgreSQL for multi-instance

### Vertical Scaling

- Increase `AGENT_MAX_CONCURRENT_QUERIES` for faster research
- Increase memory for processing large documents
- More CPU cores for parallel AI requests

### Rate Limiting

External services have rate limits:
- OpenAI: Varies by tier
- DuckDuckGo: ~20 requests/minute
- Playwright: 3-5 concurrent browsers recommended

Configure via:
```bash
AGENT_MAX_CONCURRENT_QUERIES=5
SEARCH_TIMEOUT_SECONDS=30
```

## Backup and Recovery

### Data to Backup

| Path | Content | Frequency |
|------|---------|-----------|
| `/app/outputs` | Research reports | After each run |
| `/app/data/tasks.db` | Task history | Daily |
| `/app/data/vault/` | Cached data | Weekly |

### Backup Script

```bash
#!/bin/bash
BACKUP_DIR=/backups/$(date +%Y%m%d)
mkdir -p $BACKUP_DIR

# Backup outputs
tar -czf $BACKUP_DIR/outputs.tar.gz /app/outputs

# Backup database
cp /app/data/tasks.db $BACKUP_DIR/

# Backup vault
tar -czf $BACKUP_DIR/vault.tar.gz /app/data/vault
```

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for common issues.

### Quick Diagnostics

```bash
# Check health
curl http://localhost:8000/health/detailed

# View logs
docker logs company-researcher-api

# Check circuit breakers
curl http://localhost:8000/health/detailed | jq '.components'
```
