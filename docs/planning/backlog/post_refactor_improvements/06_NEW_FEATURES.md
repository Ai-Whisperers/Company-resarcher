# ✨ New Features

This document details the new functional capabilities planned for the application. These features leverage the improved architecture to deliver more value to end-users.

## FEAT-1: Batch Research API (8h)

### Concept & Rationale

Users often need to research lists of companies (e.g., "Analyze these 50 potential investments"). Doing this one by one is tedious and slow.

**The Feature:**
A **Batch Research API** that accepts a list of companies and processes them asynchronously.

- **Bulk Submission:** Single endpoint to submit multiple companies.
- **Background Processing:** Jobs are queued and processed by background workers, respecting rate limits.
- **Status Tracking:** Endpoints to check the progress of the entire batch (e.g., "45/50 completed").
- **Bulk Results:** Download all results in a single file (JSON/CSV) once complete.

### Key Implementation Details

- New endpoints: `POST /research/batch`, `GET /research/batch/{id}/status`, `GET /research/batch/{id}/results`.
- Use a persistent job queue (Postgres or Redis).
- Reference: `src/api/routers/batch.py` (Proposed)

## FEAT-2: Research Templates (6h)

### Concept & Rationale

Different users have different needs. An investor needs financial metrics; a salesperson needs contact info; a strategist needs competitor analysis. One size does not fit all.

**The Feature:**
**Customizable Research Templates** that define what data to fetch and how to analyze it.

- **Template Definition:** Templates specify the sections (e.g., "Financial Health", "Legal Risks"), the specific prompts to use for each section, and the desired output format.
- **Pre-built Templates:** Include standard templates like "Investment Analysis", "Competitor Analysis", and "Due Diligence".
- **Customization:** Allow users to override specific parts of a template for a request.

### Key Implementation Details

- `ResearchTemplate` class to encapsulate configuration.
- Registry of available templates.
- Reference: `src/core/templates/research.py` (Proposed)

## FEAT-3: Real-time Alerts (8h)

### Concept & Rationale

Research is often a snapshot in time, but business is dynamic. Users want to know when something significant changes _after_ the initial research.

**The Feature:**
**Real-time Alerts** (`CompanyMonitor`) that track companies for specific triggers.

- **Triggers:**
  - **News Mention:** Alert if the company is mentioned in news with specific keywords.
  - **Stock Change:** Alert if stock price moves by >X%.
  - **Sentiment Shift:** Alert if public sentiment drops significantly.
- **Monitoring:** Background service that periodically checks data sources for watched companies.

### Key Implementation Details

- `WatchConfig` to store user alert preferences.
- Background scheduler to run checks.
- Reference: `src/services/alerts/monitor.py` (Proposed)

## FEAT-4: Research Comparison (6h)

### Concept & Rationale

Users rarely look at companies in isolation. They want to compare a target company against its competitors or a list of peers.

**The Feature:**
A **Comparison Engine** (`ComparisonService`) that analyzes multiple companies side-by-side.

- **Dimensional Analysis:** Compare companies across specific dimensions (e.g., Revenue Growth, Market Share, Employee Count).
- **Normalization:** Ensure data is comparable (same currency, same time period).
- **Insights:** Generate comparative insights (e.g., "Company A has higher margins but slower growth than Company B").

### Key Implementation Details

- Aggregate data from multiple `ResearchResult` objects.
- Use LLM to generate comparative narrative.
- Reference: `src/services/comparison/service.py` (Proposed)

## FEAT-5: Export & Reporting (6h)

### Concept & Rationale

The end goal of research is often a presentation or a report to share with stakeholders. Raw JSON is not consumable for this audience.

**The Feature:**
**Professional Export Options** (`ExportService`).

- **PDF:** Cleanly formatted reports with headers, footers, and layout.
- **PowerPoint:** Generate slide decks with charts and bullet points, ready for presentation.
- **Excel:** Structured data export for financial modeling.

### Key Implementation Details

- Use libraries like `python-pptx` for PowerPoint and `playwright` or `reportlab` for PDF generation.
- Support templating for the exports.
- Reference: `src/services/export/service.py` (Proposed)

## FEAT-6: Webhook Integrations (6h)

### Concept & Rationale

Users want to integrate research results into their own workflows (Slack, CRM, internal dashboards) without polling the API.

**The Feature:**
**Webhook System** (`WebhookService`) to push events to external URLs.

- **Events:** `research.completed`, `batch.completed`, `alert.triggered`.
- **Security:** Sign payloads with a secret key (`HMAC-SHA256`) so receivers can verify authenticity.
- **Reliability:** Retry logic (exponential backoff) for failed deliveries.

### Key Implementation Details

- Store webhook subscriptions in the database.
- Background worker to handle delivery and retries.
- Reference: `src/services/webhooks/service.py` (Proposed)
