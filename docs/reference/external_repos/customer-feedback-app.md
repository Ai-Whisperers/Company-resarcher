# customer-feedback-app

**Description:** 
**URL:** https://github.com/Ai-Whisperers/customer-feedback-app
**Visibility:** PRIVATE

---

# 📊 Customer Feedback Analyzer - Análisis Inteligente con IA

[![Version](https://img.shields.io/badge/version-3.9.0-blue.svg)](https://github.com/Ai-Whisperers/customer-feedback-app)
[![Cost Reduction](https://img.shields.io/badge/cost%20reduction-87%25-success.svg)](https://github.com/Ai-Whisperers/customer-feedback-app)
[![Status](https://img.shields.io/badge/status-production-success.svg)](https://customer-feedback-app.onrender.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991.svg)](https://openai.com/)
[![codecov](https://codecov.io/gh/Ai-Whisperers/customer-feedback-app/branch/main/graph/badge.svg)](https://codecov.io/gh/Ai-Whisperers/customer-feedback-app)
[![Tests](https://img.shields.io/github/actions/workflow/status/Ai-Whisperers/customer-feedback-app/coverage.yml?label=tests)](https://github.com/Ai-Whisperers/customer-feedback-app/actions/workflows/coverage.yml)

Analiza automáticamente los comentarios de tus clientes y obtén insights valiosos usando Inteligencia Artificial de última generación con **87% menos costo** que soluciones tradicionales.

## 🚀 ¿Qué hace esta herramienta?

Transforma comentarios de clientes en datos accionables:

- **Detecta 7 emociones principales** en cada comentario
- **Identifica pain points** y problemas recurrentes
- **Calcula riesgo de churn** para cada cliente
- **Clasifica NPS** (Promotor, Pasivo, Detractor)
- **Genera visualizaciones interactivas** de los resultados
- **NEW: Mejoras visuales avanzadas** (data bars, icon sets, gradient scales)
- **NEW: Integración con Google Sheets** (upload automático y apertura en navegador)

## 📖 Guía de Uso Rápido

### 1️⃣ Prepara tu archivo

Crea o toma un archivo Excel (.xlsx), CSV o Parquet que contenga los comentarios que quieres analizar para obtener retroalimentación, el archivo debe tener estas columnas necesariamente:

| Nota | Comentario Final                                   |
| ---- | -------------------------------------------------- |
| 8    | Excelente servicio, muy satisfecho con la atención |
| 5    | El precio es alto pero la calidad es buena         |
| 3    | Muy lento el servicio, esperé demasiado            |

**Requisitos del archivo:**

- ✅ Columna `Nota`: números del 0 al 10
- ✅ Columna `Comentario Final`: texto del cliente (mínimo 3 caracteres)
- ✅ Máximo 3000 filas
- ✅ Tamaño máximo: 20MB
- ✅ **Formatos soportados**: Excel (.xlsx, .xls), CSV (.csv), Parquet (.parquet)

### 2️⃣ Sube tu archivo

1. Abre la aplicación en tu navegador: [https://customer-feedback-app.onrender.com](https://customer-feedback-app.onrender.com)
2. Haz clic en **"Seleccionar archivo"** o arrastra tu archivo
3. Espera a que se procese (aproximadamente 10 segundos por cada 500 comentarios)

### 3️⃣ Explora los resultados

Una vez procesado, verás:

- **📈 Dashboard General**: Resumen de métricas clave
- **😊 Distribución de Emociones**: Gráfico de las emociones detectadas
- **⚠️ Pain Points**: Problemas más mencionados por tus clientes
- **📊 Análisis NPS**: Distribución de promotores, pasivos y detractores
- **🔥 Mapa de Calor**: Visualización de riesgo de churn por cliente

### 4️⃣ Exporta los resultados

Puedes descargar:

- **Excel detallado** con todas las métricas por comentario
- **CSV** para análisis adicional
- **Reporte PDF** (próximamente)

## 💡 Casos de Uso

### Para Servicio al Cliente

- Identifica clientes insatisfechos que necesitan atención inmediata
- Detecta problemas recurrentes en el servicio
- Prioriza casos según riesgo de churn

### Para Producto

- Descubre qué features generan más frustración
- Identifica oportunidades de mejora basadas en feedback real
- Valida hipótesis con datos cuantitativos de emociones

### Para Marketing

- Identifica promotores para programas de referidos
- Comprende mejor el sentimiento hacia tu marca
- Crea campañas targeted basadas en pain points

## 🎯 Métricas que Obtendrás

### Por cada comentario:

- **7 Emociones** (0-100%): Satisfacción, Frustración, Enojo, Confianza, Decepción, Confusión, Anticipación
- **Riesgo de Churn** (0-100%): Probabilidad de perder al cliente
- **Categoría NPS**: Promotor (9-10), Pasivo (7-8), Detractor (0-6)
- **Pain Points**: Palabras clave de problemas identificados (máximo 5 por comentario)
- **Sentiment Score** (-1 a 1): Sentimiento general

### Resumen global:

- **NPS Score**: Métrica estándar de satisfacción (-100 a 100)
- **Distribución de Emociones**: Promedio por emoción
- **Top 10 Pain Points**: Los problemas más mencionados
- **Tasa de Riesgo**: Porcentaje de clientes en riesgo alto

## ⚡ Rendimiento y Costos

| Cantidad de Comentarios | Tiempo Estimado | Costo Aproximado | Estado       |
| ----------------------- | --------------- | ---------------- | ------------ |
| 100                     | 2-3 segundos    | $0.002 USD       | ✓ Óptimo     |
| 500                     | 5-8 segundos    | $0.01 USD        | ✓ Óptimo     |
| 850                     | 8-10 segundos   | $0.017 USD       | ✓ Óptimo     |
| 1800                    | 18-20 segundos  | $0.036 USD       | ⚠ Mejorable |
| 3000                    | 30-35 segundos  | $0.06 USD        | ✓ Óptimo     |

**✨ Optimización del 87%**: Procesamos tus datos de manera ultra-eficiente, reduciendo costos sin sacrificar calidad.

## 🔒 Privacidad y Seguridad

- ✅ Tus datos se procesan de forma segura y privada
- ✅ No almacenamos información personal identificable
- ✅ Los resultados se eliminan automáticamente después de 24 horas
- ✅ Cumplimiento con GDPR y estándares de privacidad
- ✅ Toda la comunicación es encriptada (HTTPS)

## 🤔 Preguntas Frecuentes

**¿Qué idiomas soporta?**

> Actualmente español e inglés. El sistema detecta automáticamente el idioma.

**¿Puedo procesar múltiples archivos?**

> Sí, puedes procesar tantos archivos como necesites, uno a la vez.

**¿Qué pasa si mi archivo tiene más columnas?**

> No hay problema, el sistema solo usará las columnas requeridas (Nota y Comentario Final).

**¿Los resultados son precisos?**

> Utilizamos GPT-4o-mini de OpenAI con una precisión del 92% en detección de emociones y 88% en identificación de pain points.

**¿Cuánto tiempo se guardan los resultados?**

> Los resultados se mantienen disponibles por 24 horas, después se eliminan automáticamente.

**¿Puedo integrar esto con mi CRM?**

> Próximamente tendremos API REST para integraciones. Contáctanos para más información.

**¿Hay límites de uso?**

> El límite es 3000 comentarios por archivo y 20MB de tamaño máximo.

---

## 🛠️ Información Técnica

<details>
<summary><b>Para Desarrolladores y Equipos Técnicos (Click para expandir)</b></summary>

### Arquitectura del Sistema

**Stack Tecnológico:**

- Frontend: React 18.3 + TypeScript + Tailwind CSS
- Backend: FastAPI + Celery + Redis
- AI: OpenAI GPT-4o-mini (87% optimizado)
- Deployment: Render.com con 4 servicios distribuidos

### Características Técnicas Destacadas

#### 🚀 Optimización Ultra-Eficiente

- **87% reducción en costos** de OpenAI API con análisis híbrido
- **Análisis local gratuito**: Sentiment (VADER/TextBlob) sin costo
- **OpenAI selectivo**: Solo para churn risk y pain points complejos
- Procesamiento de **25-30 tokens/comentario** (antes: 250)
- Sistema de **deduplicación inteligente SHA256** (15-20% ahorro)
- **Cache de comentarios** en Redis (7 días TTL)
- **Batching dinámico** de 50-100 comentarios con gestión de memoria

#### 🎨 Funcionalidades Clave v3.2

- **Excel profesional** con hojas formateadas, gráficos y formato condicional
- **Parser flexible** con detección dinámica de columnas (Nota, Comentario Final, NPS)
- **Monitor de event loops** para debugging de procesamiento asíncrono
- **Hybrid Analyzer**: Combina análisis local + IA para máxima eficiencia
- **Gestión de memoria**: Batch sizing adaptativo según recursos disponibles

#### 🔧 Arquitectura Robusta

```
Usuario → React → BFF Proxy → FastAPI → Celery → OpenAI
                                ↓
                            Redis Cache
```

#### ☁️ Deployment Options

- **Render.com** - Simple push-to-deploy (current production)
- **AWS EKS** - Enterprise Kubernetes with auto-scaling
- **Docker Compose** - Local development and testing

**AWS Infrastructure Features** (NEW):

- Terraform IaC for complete infrastructure provisioning
- Kubernetes (EKS 1.28) with multi-AZ high availability
- Auto-scaling pods (2-10 replicas) and nodes (2-10 instances)
- Managed Redis (ElastiCache) for production
- ECR for container registry
- ALB for load balancing
- Complete monitoring with CloudWatch
- Cost: ~$200-400/month for production

See [infrastructure/README.md](infrastructure/README.md) for complete AWS setup guide.

#### 🤖 AI Integration Features (NEW)

- **MCP (Model Context Protocol)** support for AI assistants
- Compatible with Claude Desktop, Cursor, VSCode, Docker AI (Gordon)
- Filesystem, fetch, and time server tools included
- Enables AI-powered code exploration and API testing

See [.mcp/README.md](.mcp/README.md) for MCP integration details.

#### 📊 Métricas de Performance

- Success rate: >99%
- Throughput: 40 comentarios/segundo
- Latencia API: <100ms p99
- Disponibilidad: 99.9% SLA
- Deduplicación: 25-35% ahorro en llamadas API

### Instalación Local

#### Requisitos

- Python 3.11+
- Node.js 18+
- Redis 7.0+
- 4GB RAM mínimo

#### Setup Rápido

```bash
# Clonar repositorio
git clone https://github.com/yourusername/customer-feedback-app.git
cd customer-feedback-app

# Backend
cd api/
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Worker (en otra terminal)
celery -A app.workers.celery_app worker --loglevel=INFO --concurrency=1

# Frontend (en otra terminal)
cd web/
npm install
npm run dev
```

#### Variables de Entorno Críticas

```bash
# .env para desarrollo local
OPENAI_API_KEY=sk-xxxxx
REDIS_URL=redis://localhost:6379
AI_MODEL=gpt-4o-mini
BATCH_SIZE_OPTIMAL=120
CELERY_WORKER_CONCURRENCY=1
NPS_CALCULATION_METHOD=shifted  # Nuevo: NPS siempre positivo
EXCEL_FORMATTING_ENABLED=true   # Excel profesional con gráficos
ENABLE_COMMENT_CACHE=true       # Cache de comentarios (7 días TTL)
PARSER_TYPE=flexible             # Parser dinámico de columnas
ENABLE_PARALLEL_PROCESSING=true # Procesamiento paralelo habilitado
HYBRID_ANALYSIS_ENABLED=true    # Análisis híbrido (local + OpenAI)

# 🚀 NEW: Advanced Performance Features (v3.3)
ENABLE_DATASET_CACHING=false         # Dataset-level caching (2h TTL, instant re-uploads)
DATASET_CACHE_TTL_HOURS=2            # Cache expiration time
ENABLE_INTELLIGENT_SAMPLING=false    # Smart sampling for large datasets (>50K rows)
SAMPLING_THRESHOLD=50000             # Trigger sampling at 50K rows
SAMPLING_TARGET_SIZE=10000           # Sample down to 10K rows (90% cost savings)
SAMPLING_MIN_PER_CATEGORY=100        # Minimum samples per NPS category
```

### Running Tests

#### Backend Tests (Python/pytest)

```bash
cd api
pytest tests/ -v --cov=app
```

**Test categories available:**

- `pytest api/tests/integration/api/` - API endpoint tests
- `pytest tests/e2e/` - End-to-end integration tests
- `pytest -m "not slow"` - Skip slow tests
- `pytest --cov-report=html` - Generate HTML coverage report

#### Frontend Type Check & Lint

```bash
cd web
npm run type-check  # TypeScript validation
npm run lint        # ESLint checks
```

#### All Checks via GitHub Actions (Locally)

```bash
# Install act: https://github.com/nektos/act
act -j backend-checks
act -j frontend-checks
```

**Note:** All tests are automatically run on pull requests and pushes to main via GitHub Actions.

#### 🎯 Feature Flag Guide

**Dataset Caching** (`ENABLE_DATASET_CACHING`):

- **What it does**: Caches complete analysis results by dataset fingerprint
- **When to enable**: When users frequently re-upload the same datasets
- **Impact**:
  - 0 seconds response time on duplicate uploads (vs 30-60s)
  - 100% cost savings on cached analyses
  - 2-hour TTL (configurable)
- **Use case**: QA environments, demo datasets, iterative analysis workflows

**Intelligent Sampling** (`ENABLE_INTELLIGENT_SAMPLING`):

- **What it does**: Stratified sampling by NPS category for large datasets
- **When to enable**: When processing datasets > 50K comments
- **Impact**:
  - 90%+ cost reduction (e.g., 120K → 10K comments analyzed)
  - 90%+ speed improvement
  - Statistical accuracy maintained (NPS ± 5 points, <5% distribution error)
- **Use case**: Massive feedback campaigns, annual surveys, enterprise datasets

**Combined Effect Example** (100K comments dataset):

```
Without features:  120 seconds, $2.40 USD
With sampling:     12 seconds,  $0.24 USD (90% savings)
Cached re-upload:  <1 second,   $0.00 USD (instant)
```

### API REST

#### Subir Archivo

```bash
POST /upload
Content-Type: multipart/form-data

Respuesta:
{
  "task_id": "uuid-v4",
  "status": "pending",
  "message": "File uploaded successfully"
}
```

#### Consultar Estado

```bash
GET /status/{task_id}

Respuesta:
{
  "task_id": "uuid-v4",
  "status": "completed",
  "progress": 100,
  "message": "Analysis complete",
  "processed_rows": 500
}
```

#### Obtener Resultados

```bash
GET /results/{task_id}

Respuesta:
{
  "summary": {
    "total_comments": 500,
    "avg_sentiment": 0.65,
    "nps_score": 42
  },
  "emotions_summary": {...},
  "pain_points": [...],
  "detailed_results": [...]
}
```

#### Exportar Resultados

```bash
GET /export/{task_id}?format=xlsx

Formatos disponibles: csv, xlsx, all
```

### Deployment Options

Este proyecto soporta **tres opciones de deployment** dependiendo de tus necesidades:

#### Opción 1: Render.com - Recomendado para Startups y MVP

**📋 Modos de Deployment:** Ver [DEPLOYMENT_MODES.md](DEPLOYMENT_MODES.md) para detalles completos.

**Modo 1: Git-based Deployment (Actual/Default)** ⭐ Recomendado

- ✅ Simple push-to-deploy workflow
- ✅ Configurado con `render.yaml` + build scripts
- ✅ Deployments automáticos en push a `main`
- 💰 Costo: ~$32.40-34.20/mes (incluye build minutes)

**Modo 2: Docker Image Deployment (Opcional)**

- ✅ Builds en GitHub Actions (gratis)
- ✅ 60-70% más rápido en deployments
- ✅ Zero build minutes en Render
- 💰 Costo: ~$32.00/mes (ahorra $0.40-2.20/mes)
- 📖 Guía: [DOCKER_SETUP.md](DOCKER_SETUP.md)

**Servicios Requeridos:**

1. **customer-feedback-app** (Web Service) - Public
2. **customer-feedback-api** (Web Service) - Private
3. **customer-feedback-worker** (Background Worker) - Private
4. **feedback-analyzer-redis** (Redis) - External

**Configuración Crítica del Worker:**

```bash
# IMPORTANTE: URLs completas, no usar ${REDIS_URL}
REDIS_URL=redis://red-xxxxx:6379
CELERY_BROKER_URL=redis://red-xxxxx:6379
CELERY_RESULT_BACKEND=redis://red-xxxxx:6379
OPENAI_API_KEY=sk-xxxxx
```

#### Opción 2: AWS EKS - Recomendado para Empresas (NEW! 🆕)

**Deployment de nivel empresarial con Kubernetes en AWS**

**Características:**

- ✅ Auto-scaling horizontal (pods: 2-10, nodes: 2-10)
- ✅ Alta disponibilidad multi-AZ
- ✅ Managed Redis (ElastiCache)
- ✅ Infrastructure as Code (Terraform)
- ✅ CI/CD con GitHub Actions
- ✅ Monitoreo completo con CloudWatch
- 💰 Costo: ~$200-400/mes (escala con uso)

**Quick Start:**

```bash
# 1. Setup completo de infraestructura (15-20 min)
./infrastructure/scripts/setup-aws-infra.sh production

# 2. Configurar secrets en AWS
./infrastructure/scripts/set-secrets.sh production

# 3. Build y push de imágenes Docker (5-10 min)
./infrastructure/scripts/build-and-push.sh production

# 4. Deploy a Kubernetes (3-5 min)
./infrastructure/scripts/deploy-k8s.sh production

# 5. Obtener URL del Load Balancer
kubectl get ingress -n default
```

**Componentes provisionados:**

- VPC con subnets públicas/privadas en 3 AZs
- EKS cluster (Kubernetes 1.28)
- Node groups con auto-scaling (t3.medium)
- ElastiCache Redis (cache.t3.micro)
- ECR repositories para imágenes Docker
- ALB (Application Load Balancer)
- Secrets Manager para credenciales
- CloudWatch para logs y métricas

**Documentación completa:** Ver [infrastructure/README.md](infrastructure/README.md)

#### Opción 3: Docker Compose - Desarrollo Local

#### Local Development con Docker (Opcional)

```bash
# Clonar y configurar
git clone https://github.com/yourusername/customer-feedback-app.git
cd customer-feedback-app
cp .env.example .env.local
# Editar .env.local y agregar OPENAI_API_KEY

# Iniciar con Docker Compose (emula Render exacto)
docker-compose up -d

# Acceder
# Frontend: http://localhost:3000
# API: http://localhost:10000
# API Docs: http://localhost:10000/docs
```

### MCP (Model Context Protocol) Integration (NEW! 🆕)

Integra AI assistants directamente con tu proyecto usando MCP.

**Compatibilidad:**

- Docker AI (Gordon) ✅
- Claude Desktop ✅
- Cursor / VSCode ✅
- Windsurf / Continue.dev ✅

**Setup con Docker AI (Gordon):**

```bash
# Gordon detecta automáticamente gordon-mcp.yml
docker ai "Analiza la estructura del proyecto"
docker ai "Revisa el endpoint de salud de la API"
docker ai "Busca archivos CSV con datos de feedback"
```

**Herramientas MCP disponibles:**

- **filesystem** - Lee archivos del proyecto y datasets
- **fetch** - Testea endpoints de API
- **time** - Operaciones de timestamp y duración

**Documentación completa:** Ver [.mcp/README.md](.mcp/README.md)

### Monitoreo y Logs

El sistema incluye logging estructurado completo:

```json
{
  "event": "Batch processing summary",
  "total_batches": 12,
  "completed": 12,
  "success_rate": 100,
  "total_tokens_used": 28980,
  "tokens_per_comment": 25.3,
  "deduplication_savings": 32.5
}
```

### Contribuir

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Documentación Técnica Completa

Para más detalles técnicos, consulta:

- [Índice de Documentación](../../../docs/README.md) - Punto de entrada a toda la documentación
- [Documentación Técnica Completa](../../../docs/TECHNICAL_DOCUMENTATION.md) - Arquitectura y detalles de implementación
- [Arquitectura Frontend](../../../docs/FRONTEND_ARCHITECTURE.md) - Estructura y componentes del frontend
- [Guía de Deployment en Render](../../../docs/RENDER_DEPLOYMENT.md) - Configuración de despliegue
- [Integración de Servicios](../../../docs/SERVICE_INTEGRATION.md) - Comunicación entre servicios

</details>

---

## 📞 Soporte

¿Necesitas ayuda o tienes sugerencias?

- 📧 Email: support@feedbackanalyzer.com
- 💬 Chat: Disponible en la aplicación
- 📖 [Documentación completa](../../../docs)
- 🐛 [Reportar un bug](https://github.com/yourusername/customer-feedback-app/issues)

---

## 📜 Licencia

Este proyecto está licenciado bajo MIT License - ver [LICENSE](../../../LICENSE) para más detalles.

---

**Desarrollado por AI Whisperers Team**

_Versión 3.8.0 - Estado: PRODUCCIÓN - Última actualización: 6 de Noviembre 2025_

### Cambios Recientes (v3.7.0)

#### Architecture & Code Quality (NEW!)

- **Dependency Injection** - Sistema completo de DI con 6 interfaces core (IFileProcessor, IAnalyzer, IExporter, IValidator, ISampler, ICache)
- **Modular Architecture** - 10 archivos grandes refactorizados en 38 módulos enfocados (~200 líneas cada uno)
- **Centralized Configuration** - Sistema unificado de constantes, formatos de archivo, y umbrales
- **Test Infrastructure** - Pre-push hooks optimizados, PYTHONPATH estandarizado
- **Excel Improvements** - Correcciones en NPS Analysis sheet, mejoras en Score-Sentiment Correlation
- **Security Updates** - Corrección de vulnerabilidad HTTP/2 request splitting (GHSA-847f-9342-265h)

Ver [CHANGELOG.md](CHANGELOG.md) para detalles completos.

### Versión Anterior (v3.4.0)

#### Infrastructure & DevOps (NEW! 🆕)

- ✅ **AWS EKS Infrastructure** - Terraform IaC completo para deployment empresarial
- ✅ **Kubernetes** - Auto-scaling, multi-AZ, alta disponibilidad
- ✅ **ElastiCache Redis** - Managed Redis para producción
- ✅ **CI/CD Pipeline** - GitHub Actions para deploy automático
- ✅ **MCP Integration** - Model Context Protocol para AI assistants
- ✅ **Docker AI Support** - Compatible con Gordon, Claude Desktop, Cursor

#### Backend Performance

- ✅ **Redis Singleton Pattern** - Connection pooling centralizado (20 conexiones)
- ✅ **Configuration System** - Settings centralizados con validación
- ✅ **Structured Logging** - Logs estructurados con context tracing
- ✅ **Dynamic Analysis** - Procesamiento condicional según columnas disponibles

#### Versión Anterior (v3.2.0)

**Frontend:**

- ✅ Refactorización completa de componentes (Clean Architecture)
- ✅ Code splitting y lazy loading (65% reducción de bundle)
- ✅ Componentes modulares: ResultsCharts (380→65 líneas), FileUpload (251→100 líneas)
- ✅ Glass Design System implementado
- ✅ TypeScript estricto con tipos explícitos

**Backend:**

- ✅ Análisis híbrido: Sentiment local (VADER/TextBlob) + OpenAI
- ✅ Procesamiento paralelo con event loop optimizado
- ✅ Deduplicación inteligente SHA256 (15-20% ahorro)
- ✅ Excel profesional con gráficos y formato condicional
- ✅ Parser flexible con detección dinámica de columnas
- ✅ Gestión de memoria dinámica (batch sizing adaptativo)
- ✅ Cache de comentarios con 7 días TTL
