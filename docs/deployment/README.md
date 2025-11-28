# Deployment Guide

This guide covers deploying Company Researcher to various environments.

## Deployment Options

| Method | Best For | Complexity |
|--------|----------|------------|
| [Local Development](#local-development) | Development, testing | Low |
| [Docker](#docker-deployment) | Consistent environments | Medium |
| [Docker Compose](#docker-compose) | Full stack deployment | Medium |
| [Cloud Platforms](#cloud-deployment) | Production | High |

---

## Local Development

### Quick Start

```bash
# Clone and setup
git clone https://github.com/Ai-Whisperers/Company-resarcher.git
cd Company-resarcher

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run CLI
python main.py --name "Apple" --industry "Technology"

# Or run API
uvicorn src.api.app:app --reload
```

### Development Server

```bash
# API with hot reload
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

# Streamlit UI
streamlit run src/ui/app.py
```

---

## Docker Deployment

### Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the API
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and Run

```bash
# Build image
docker build -t company-researcher:latest .

# Run container
docker run -d \
    --name researcher \
    -p 8000:8000 \
    -e OPENAI_API_KEY=${OPENAI_API_KEY} \
    -e TAVILY_API_KEY=${TAVILY_API_KEY} \
    -v $(pwd)/output:/app/output \
    company-researcher:latest

# View logs
docker logs -f researcher

# Stop
docker stop researcher
```

---

## Docker Compose

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/researcher
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./output:/app/output
      - ./logs:/app/logs
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
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
      - POSTGRES_DB=researcher
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
    command: redis-server --appendonly yes

  ui:
    build: .
    command: streamlit run src/ui/app.py --server.port 8501
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://api:8000
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
```

### Usage

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Cloud Deployment

### AWS (ECS/Fargate)

1. **Push to ECR**:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker tag company-researcher:latest <account>.dkr.ecr.us-east-1.amazonaws.com/company-researcher:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/company-researcher:latest
```

2. **Create ECS Task Definition** with:
   - Container image from ECR
   - Environment variables from Secrets Manager
   - 2 vCPU, 4GB memory minimum
   - Port 8000 exposed

3. **Create ECS Service** with:
   - Application Load Balancer
   - Auto-scaling based on CPU/memory
   - Health check on `/health`

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/company-researcher

# Deploy
gcloud run deploy company-researcher \
    --image gcr.io/PROJECT_ID/company-researcher \
    --platform managed \
    --region us-central1 \
    --memory 4Gi \
    --cpu 2 \
    --timeout 1800 \
    --set-env-vars "OPENAI_API_KEY=..." \
    --allow-unauthenticated
```

### Railway / Render (Simple PaaS)

1. Connect GitHub repository
2. Set environment variables in dashboard
3. Deploy automatically on push

**Railway Configuration** (`railway.toml`):
```toml
[build]
builder = "dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
```

---

## Production Configuration

### Environment Variables

```env
# Required
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...

# Database (use PostgreSQL in production)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Security
CORS_ORIGINS=https://your-frontend.com
MAX_REQUEST_SIZE_BYTES=2000000

# Performance
RESEARCH_TIMEOUT_SECONDS=3600
CONCURRENT_SEARCHES=5

# Observability (recommended)
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
```

### Resource Requirements

| Component | Minimum | Recommended | High Volume |
|-----------|---------|-------------|-------------|
| CPU | 2 cores | 4 cores | 8+ cores |
| Memory | 2 GB | 4 GB | 8+ GB |
| Storage | 5 GB | 20 GB | 50+ GB |

### Scaling Considerations

- **Horizontal scaling**: Run multiple API instances behind load balancer
- **Database**: Use connection pooling (PgBouncer)
- **Caching**: Redis for response caching across instances
- **Queue**: Consider Celery/RabbitMQ for high volume

---

## Production Checklist

### Security

- [ ] API keys stored in secrets manager (not env files)
- [ ] HTTPS enabled (SSL/TLS termination)
- [ ] CORS origins restricted
- [ ] Rate limiting configured
- [ ] Non-root container user
- [ ] Network policies configured

### Reliability

- [ ] Health checks configured
- [ ] Auto-restart on failure
- [ ] Database backups scheduled
- [ ] Log aggregation setup
- [ ] Monitoring/alerting configured

### Performance

- [ ] Response caching enabled
- [ ] Connection pooling configured
- [ ] Appropriate resource limits set
- [ ] Auto-scaling configured

### Observability

- [ ] Structured logging
- [ ] Metrics collection
- [ ] Distributed tracing (Langfuse)
- [ ] Error tracking (Sentry)

---

## Monitoring

### Health Endpoints

```bash
# Basic health
curl http://localhost:8000/health
# {"status": "healthy"}

# Detailed health (checks DB, AI providers)
curl http://localhost:8000/health/detailed
# {"status": "healthy", "checks": {...}}
```

### Logs

```bash
# Docker logs
docker logs -f researcher

# Log file (if configured)
tail -f logs/research.log
```

### Metrics to Monitor

- Request latency (P50, P95, P99)
- Error rate
- Task completion rate
- API provider errors/rate limits
- Memory/CPU usage
- Database connection pool

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs researcher

# Common issues:
# - Missing environment variables
# - Database connection failed
# - Port already in use
```

### High Memory Usage

- Playwright browsers consume memory
- Increase container memory limit
- Consider browser pooling

### Slow Performance

- Check LLM provider latency
- Enable response caching
- Use faster models (Groq) for simple tasks
- Increase concurrent searches

See [Troubleshooting Guide](../guides/TROUBLESHOOTING.md) for more.
