# Deployment Guide

This guide covers deploying the Company Researcher to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Deployment Options](#deployment-options)
  - [Docker](#docker-deployment)
  - [Docker Compose](#docker-compose)
  - [Kubernetes](#kubernetes)
  - [Cloud Platforms](#cloud-platforms)
- [Production Checklist](#production-checklist)
- [Monitoring & Logging](#monitoring--logging)
- [Scaling](#scaling)
- [Security Hardening](#security-hardening)

---

## Prerequisites

- Python 3.10+
- At least one AI provider API key
- 2GB RAM minimum (4GB recommended)
- PostgreSQL for production (SQLite for development only)

---

## Environment Configuration

### Required Environment Variables

```bash
# AI Provider (at least one required)
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
# or
GROQ_API_KEY=gsk_...

# API Authentication
API_KEY=your-secure-api-key-here

# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql://user:password@host:5432/company_researcher

# Environment Profile
APP_PROFILE=production
ENVIRONMENT=production
```

### Optional Environment Variables

```bash
# AI Configuration
AI__PRIMARY=openai
AI__FALLBACK=anthropic
AI__OPENAI__MODEL=gpt-4o
AI__OPENAI__TEMPERATURE=0.7
AI__OPENAI__MAX_TOKENS=4096

# Search Providers (optional, DuckDuckGo is free)
SERPER_API_KEY=your-key
TAVILY_API_KEY=your-key

# Cache Configuration
CACHE__ENABLED=true
CACHE__DEFAULT_TTL=3600
CACHE__AI_CACHE_ENABLED=true

# Runtime Configuration
RUNTIME__LOG_LEVEL=WARNING
RUNTIME__HEADLESS=true

# Research Configuration
MAX_SEARCH_RESULTS=10
CONCURRENT_SEARCHES=5
RESEARCH_TIMEOUT_SECONDS=1800

# API Configuration
CORS_ORIGINS=https://your-frontend.com
MAX_REQUEST_SIZE_BYTES=65536

# Browser Configuration
BROWSER_FETCH_TIMEOUT_SECONDS=60

# Observability (optional)
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## Deployment Options

### Docker Deployment

#### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Install Playwright browsers
RUN playwright install chromium

# Copy application code
COPY src/ src/
COPY main.py .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Build and Run

```bash
# Build image
docker build -t company-researcher:latest .

# Run container
docker run -d \
  --name company-researcher \
  -p 8000:8000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e API_KEY=$API_KEY \
  -e DATABASE_URL=$DATABASE_URL \
  -e APP_PROFILE=production \
  company-researcher:latest
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_PROFILE=production
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/company_researcher
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - API_KEY=${API_KEY}
      - CACHE__ENABLED=true
      - RUNTIME__LOG_LEVEL=WARNING
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=company_researcher
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Kubernetes

#### Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: company-researcher
  labels:
    app: company-researcher
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
        env:
        - name: APP_PROFILE
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: company-researcher-secrets
              key: database-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: company-researcher-secrets
              key: openai-api-key
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: company-researcher-secrets
              key: api-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/detailed
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service

```yaml
# k8s/service.yaml
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
  type: LoadBalancer
```

#### Secrets

```yaml
# k8s/secrets.yaml (apply separately, don't commit to git)
apiVersion: v1
kind: Secret
metadata:
  name: company-researcher-secrets
type: Opaque
stringData:
  database-url: postgresql://user:password@postgres:5432/company_researcher
  openai-api-key: sk-...
  api-key: your-secure-api-key
```

### Cloud Platforms

#### AWS (ECS/Fargate)

1. Push image to ECR:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
   docker tag company-researcher:latest $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/company-researcher:latest
   docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/company-researcher:latest
   ```

2. Create ECS Task Definition with secrets from AWS Secrets Manager

3. Create ECS Service with Application Load Balancer

#### Google Cloud (Cloud Run)

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/$PROJECT_ID/company-researcher

# Deploy to Cloud Run
gcloud run deploy company-researcher \
  --image gcr.io/$PROJECT_ID/company-researcher \
  --platform managed \
  --region us-central1 \
  --set-env-vars APP_PROFILE=production \
  --set-secrets OPENAI_API_KEY=openai-key:latest,API_KEY=api-key:latest \
  --memory 2Gi \
  --cpu 2 \
  --timeout 1800
```

#### Azure (Container Instances)

```bash
az container create \
  --resource-group myResourceGroup \
  --name company-researcher \
  --image company-researcher:latest \
  --dns-name-label company-researcher \
  --ports 8000 \
  --environment-variables APP_PROFILE=production \
  --secure-environment-variables OPENAI_API_KEY=$OPENAI_API_KEY API_KEY=$API_KEY
```

---

## Production Checklist

### Security
- [ ] Set strong `API_KEY` (32+ random characters)
- [ ] Configure `CORS_ORIGINS` to specific domains only
- [ ] Use HTTPS (terminate at load balancer)
- [ ] Use PostgreSQL instead of SQLite
- [ ] Store secrets in secret manager (AWS Secrets Manager, GCP Secret Manager, etc.)
- [ ] Enable rate limiting (default: 10 req/min)
- [ ] Review and restrict network access

### Performance
- [ ] Enable caching (`CACHE__ENABLED=true`)
- [ ] Enable AI response caching (`CACHE__AI_CACHE_ENABLED=true`)
- [ ] Configure appropriate timeouts
- [ ] Set `RUNTIME__HEADLESS=true`
- [ ] Use production log level (`RUNTIME__LOG_LEVEL=WARNING`)

### Reliability
- [ ] Configure health checks
- [ ] Set up database backups
- [ ] Configure auto-restart on failure
- [ ] Set resource limits (memory, CPU)
- [ ] Configure graceful shutdown

### Monitoring
- [ ] Set up log aggregation
- [ ] Configure error tracking (Langfuse, Sentry)
- [ ] Set up alerts for health check failures
- [ ] Monitor API response times
- [ ] Track AI token usage

---

## Monitoring & Logging

### Structured Logging

Logs are output in a structured format with request IDs for tracing:

```bash
# Set log level
export RUNTIME__LOG_LEVEL=INFO

# Enable file logging
export RUNTIME__LOG_TO_FILE=true
export RUNTIME__LOG_FILE_PATH=/var/log/company-researcher/app.log
```

### Metrics Endpoints

```bash
# Basic health
curl http://localhost:8000/health

# Detailed health with dependency checks
curl http://localhost:8000/health/detailed
```

### Langfuse Integration

For AI observability:

```bash
export LANGFUSE_PUBLIC_KEY=pk-...
export LANGFUSE_SECRET_KEY=sk-...
export LANGFUSE_HOST=https://cloud.langfuse.com
```

### Log Aggregation

Example Fluentd configuration:

```yaml
<source>
  @type tail
  path /var/log/company-researcher/*.log
  pos_file /var/log/td-agent/company-researcher.log.pos
  tag company-researcher
  <parse>
    @type json
  </parse>
</source>

<match company-researcher>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name company-researcher
</match>
```

---

## Scaling

### Horizontal Scaling

The API is stateless and can be scaled horizontally:

1. **Load Balancer**: Use nginx, HAProxy, or cloud LB
2. **Session Storage**: Not required (stateless)
3. **Database**: Use PostgreSQL with connection pooling
4. **Cache**: Consider Redis for shared caching (future)

### Resource Recommendations

| Scale | Instances | CPU | Memory | Database |
|-------|-----------|-----|--------|----------|
| Small | 1 | 1 vCPU | 2GB | SQLite/Small PG |
| Medium | 2-3 | 2 vCPU | 4GB | PostgreSQL |
| Large | 5+ | 4 vCPU | 8GB | PostgreSQL HA |

### Rate Limiting

Configure based on expected load:

```python
# In src/api/app.py
rate_limiter = RateLimiter(requests_per_minute=100)  # Increase for production
```

---

## Security Hardening

### Network Security

1. **Use private subnets** for database and internal services
2. **Configure security groups/firewall rules** to restrict access
3. **Use VPN or bastion host** for administrative access

### Secret Management

Never commit secrets to git. Use:
- AWS Secrets Manager
- GCP Secret Manager
- Azure Key Vault
- HashiCorp Vault
- Kubernetes Secrets (with encryption at rest)

### API Security

1. **Rotate API keys** regularly
2. **Use separate keys** for different environments
3. **Monitor for suspicious activity** (rate limit breaches, invalid keys)

### Container Security

```dockerfile
# Run as non-root
USER appuser

# Use minimal base image
FROM python:3.11-slim

# Don't store secrets in image
# Use runtime environment variables or mounted secrets
```

---

## Rollback Procedure

If a deployment fails:

1. **Docker/Docker Compose:**
   ```bash
   docker-compose down
   docker-compose up -d --build  # With previous image
   ```

2. **Kubernetes:**
   ```bash
   kubectl rollout undo deployment/company-researcher
   ```

3. **Cloud Run:**
   ```bash
   gcloud run services update-traffic company-researcher --to-revisions=REVISION_NAME=100
   ```

---

## Maintenance

### Database Maintenance

```sql
-- PostgreSQL: Analyze and vacuum
VACUUM ANALYZE tasks;

-- Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

### Cache Cleanup

Cache is automatically cleaned based on TTL. Manual cleanup:

```python
from src.core.cache import clear_cache
clear_cache()
```

### Log Rotation

Example logrotate configuration:

```
/var/log/company-researcher/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 appuser appuser
}
```
