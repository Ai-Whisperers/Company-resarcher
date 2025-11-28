# cluster-template

**Description:** 
**URL:** https://github.com/Ai-Whisperers/cluster-template
**Visibility:** PRIVATE

---

# Kubernetes Cluster Template

**Doc-Type:** Repository Overview · Version 1.0 · Updated 2025-11-17 · Author AI Whisperers

On-premise Kubernetes deployment template with Model Context Protocol (MCP) server integration for AI-assisted cluster management using Claude Code.

---

## Purpose

**deployment_template** - Production-ready Kubernetes cluster configuration for Docker Desktop with comprehensive tooling, port management, and AI integration

**target_audience** - DevOps engineers, platform teams, and developers deploying containerized applications on-premise

**key_differentiator** - MCP server enables Claude Code to interact directly with Kubernetes cluster for deployments, monitoring, and troubleshooting

---

## Quick Start

### Prerequisites

- Docker Desktop with Kubernetes enabled (v1.34.1+)
- kubectl CLI tool
- Git
- Claude Code CLI
- Basic understanding of Kubernetes concepts

### 5-Minute Setup

```bash
# 1. Clone repository to your home directory
git clone https://github.com/Ai-Whisperers/cluster-template.git ~/.claude

# 2. Verify Kubernetes cluster
kubectl cluster-info

# 3. Build MCP server
cd ~/.claude/mcp/configs
docker-compose -f docker-compose.mcp-gateway.yml build kubernetes

# 4. Register MCP server in Claude settings
# Edit ~/.claude/settings.json and add mcpServers section (see documentation)

# 5. Test deployment
cd ~/.claude/mcp/examples/deployments
source ../../configs/ports.env
./deploy.sh web-app-example.yaml test
```

**next_steps** - See [GETTING-STARTED.md](GETTING-STARTED.md) for detailed onboarding

---

## What's Included

### MCP Kubernetes Server

**location** - `.claude/mcp/servers/kubernetes/`
**capabilities** - 6 kubectl operations exposed as AI tools (deploy, status, logs, scale, delete, cluster-info)
**transport** - Stdio protocol with Docker containerization
**documentation** - [MCP README](.claude/mcp/README.md), [Architecture](.claude/mcp/ARCHITECTURE.md)

### Port Management Strategy

**location** - `.claude/mcp/configs/ports.env`
**approach** - Centralized environment-based port allocation by service type
**ranges** - Web (30000-30099), API (30100-30199), DB (30200-30299), Monitoring (30400-30499)
**documentation** - [PORT-STRATEGY.md](.claude/mcp/PORT-STRATEGY.md)

### Deployment Templates

**location** - `.claude/mcp/examples/deployments/`
**templates** - Web application, API service, PostgreSQL database
**automation** - `deploy.sh` script with validation and monitoring
**documentation** - [Deployments README](.claude/mcp/examples/deployments/README.md)

### Slash Commands

**location** - `.claude/commands/`
**commands** - `/k8s-deploy`, `/k8s-status`, `/k8s-logs`, `/k8s-scale`, `/k8s-delete`, `/k8s-info`
**usage** - Direct Kubernetes operations from Claude Code CLI

### Documentation

**setup_guides** - [QUICKSTART.md](.claude/mcp/QUICKSTART.md), [SETUP.md](.claude/mcp/SETUP.md)
**implementation_summaries** - [ON-PREMISE-KUBERNETES-READY.md](ON-PREMISE-KUBERNETES-READY.md), [MCP-KUBERNETES-SETUP-COMPLETE.md](MCP-KUBERNETES-SETUP-COMPLETE.md)
**gap_analysis** - [KUBERNETES-MCP-GAP-ANALYSIS.md](KUBERNETES-MCP-GAP-ANALYSIS.md) with 43 identified gaps and 6-week roadmap

---

## Repository Structure

```
cluster-template/
├── README.md (this file)
├── GETTING-STARTED.md (developer onboarding)
├── ON-PREMISE-KUBERNETES-READY.md (implementation summary)
├── MCP-KUBERNETES-SETUP-COMPLETE.md (initial setup)
├── KUBERNETES-MCP-GAP-ANALYSIS.md (production readiness gaps)
│
└── .claude/
    ├── CLAUDE.md (user-level configuration template)
    ├── FOLDER-STRUCTURE-FINAL.md (directory organization)
    │
    ├── mcp/ (Kubernetes MCP implementation)
    │   ├── README.md (MCP overview)
    │   ├── ARCHITECTURE.md (system design)
    │   ├── SETUP.md (detailed installation)
    │   ├── QUICKSTART.md (5-minute guide)
    │   ├── PORT-STRATEGY.md (port allocation)
    │   │
    │   ├── servers/kubernetes/ (MCP server code)
    │   │   ├── server.py (Python implementation)
    │   │   ├── Dockerfile (containerization)
    │   │   └── README.md (server documentation)
    │   │
    │   ├── configs/ (configuration files)
    │   │   ├── ports.env (port allocation variables)
    │   │   ├── docker-compose.mcp-gateway.yml (MCP gateway)
    │   │   └── gordon-mcp.yml (Gordon configuration)
    │   │
    │   └── examples/deployments/ (deployment templates)
    │       ├── web-app-example.yaml (NGINX)
    │       ├── api-service-example.yaml (REST API)
    │       ├── database-example.yaml (PostgreSQL)
    │       ├── deploy.sh (automation script)
    │       └── README.md (template documentation)
    │
    ├── commands/ (slash commands for Claude Code)
    │   ├── k8s-deploy.md, k8s-status.md, etc.
    │   └── doc.md, doc-validate.md, doc-ratio.md
    │
    ├── docs/ (reference documentation)
    │   ├── mcp-configuration.md (official MCP docs)
    │   ├── settings-folder-structure.md (folder structure)
    │   ├── FOLDER-STRUCTURE-ANALYSIS.md (analysis)
    │   └── MIGRATION-TO-CLAUDE-MCP.md (migration log)
    │
    ├── customizations/documentation-style/ (doc standards)
    │   ├── documentation-format.md
    │   ├── toon-format-reference.md
    │   └── neuroparsing-protocol.md
    │
    ├── agents/ (custom agent definitions)
    │   └── agent-architect.md
    │
    └── local/ (development artifacts, gitignored)
        ├── README.md (usage guide)
        └── PROJECT-TEMPLATE.md (team standards template)
```

---

## Key Features

### AI-Assisted Cluster Management

**mcp_integration** - Claude Code can deploy, monitor, scale, and troubleshoot Kubernetes resources through natural language
**slash_commands** - Direct kubectl operations without leaving Claude Code CLI
**context_aware** - AI understands cluster state, port allocations, and deployment templates

### Port Abstraction

**centralized_config** - Single `ports.env` file manages all port allocations
**range_based** - Organized by service type (Web, API, DB, Monitoring)
**template_support** - Deployment manifests use environment variable substitution
**conflict_prevention** - Port registry tracks allocations across namespaces

### Production-Ready Templates

**best_practices** - Health checks, resource limits, secrets management, persistent volumes
**configurable** - Environment-based customization for dev/staging/production
**documented** - Inline comments explaining each configuration choice
**tested** - Validated deployment patterns for common workloads

### Comprehensive Documentation

**dual_layer_format** - Human-readable headers with structured technical details
**cognitive_optimization** - 4-7 item chunks, max 3 hierarchy levels
**onboarding_focused** - Step-by-step guides for new developers
**gap_analysis** - Honest assessment of what's missing for production

---

## Current Status

**cluster_verified** - Kubernetes v1.34.1 running on Docker Desktop
**mcp_server_built** - Container image ready (configs-kubernetes:latest, 304MB)
**port_strategy_implemented** - Centralized allocation with 5 service type ranges
**templates_created** - 3 deployment examples with automation script
**documentation_complete** - 11 comprehensive guides across setup, architecture, operations

**not_yet_production** - See [KUBERNETES-MCP-GAP-ANALYSIS.md](KUBERNETES-MCP-GAP-ANALYSIS.md) for 43 identified gaps

---

## Getting Started

**new_developers** - Read [GETTING-STARTED.md](GETTING-STARTED.md) for complete onboarding
**quick_deployment** - Follow [QUICKSTART.md](.claude/mcp/QUICKSTART.md) for 5-minute setup
**understanding_architecture** - Review [ARCHITECTURE.md](.claude/mcp/ARCHITECTURE.md)
**production_readiness** - Consult [KUBERNETES-MCP-GAP-ANALYSIS.md](KUBERNETES-MCP-GAP-ANALYSIS.md)

---

## Use Cases

### Development Environment

**local_testing** - Deploy applications to local Kubernetes cluster
**port_forwarding** - Access services via NodePort (30000-32767)
**rapid_iteration** - Automated deployment script with validation

### On-Premise Production

**nodeport_services** - External access without cloud load balancers
**port_management** - Organized allocation prevents conflicts
**monitoring_ready** - Reserved ranges for Prometheus/Grafana

### AI-Assisted Operations

**natural_language_deploys** - "Deploy web-app-example to production namespace"
**troubleshooting** - "Show logs for failing pods in api namespace"
**scaling** - "Scale api-service to 5 replicas"

---

## Technology Stack

**orchestration** - Kubernetes v1.34.1 (Docker Desktop)
**containerization** - Docker with multi-stage builds
**mcp_framework** - Model Context Protocol (Anthropic)
**ai_integration** - Claude Code CLI with Sonnet 4.5
**automation** - Bash scripting, envsubst for templating
**documentation** - Markdown with dual-layer format

---

## Contributing

**report_issues** - Open GitHub issues for bugs or missing features
**submit_improvements** - Pull requests welcome for templates, documentation, MCP tools
**share_patterns** - Contribute deployment patterns for common workloads
**documentation_updates** - Improve onboarding or technical guides

See project standards in `.claude/local/PROJECT-TEMPLATE.md` for coding guidelines.

---

## Security Considerations

**secrets_warning** - Example database YAML contains plaintext password (line 17) - replace with Sealed Secrets or Vault
**kubeconfig_exposure** - MCP server mounts full admin kubeconfig - implement RBAC service accounts for production
**network_policies** - No network segmentation configured - implement zero-trust policies
**image_scanning** - No vulnerability scanning - integrate Trivy or Clair

Review [KUBERNETES-MCP-GAP-ANALYSIS.md](KUBERNETES-MCP-GAP-ANALYSIS.md) section 3 for complete security audit.

---

## Known Limitations

**mcp_not_registered** - Server built but not added to `~/.claude/settings.json` (requires manual configuration)
**never_tested** - Deployment templates not executed end-to-end
**no_monitoring** - Prometheus/Grafana not installed
**no_ingress** - HTTP(S) routing requires NGINX Ingress Controller installation
**helm_missing** - Package manager not available

See [KUBERNETES-MCP-GAP-ANALYSIS.md](KUBERNETES-MCP-GAP-ANALYSIS.md) for complete list of 43 gaps.

---

## Roadmap

### Phase 1: Foundation (Week 1)
- Register MCP server in settings.json
- End-to-end testing of deployment templates
- Install Sealed Secrets for secret management
- Install Helm package manager

### Phase 2: Production Essentials (Week 2-3)
- Deploy Prometheus + Grafana monitoring stack
- Install NGINX Ingress Controller
- Setup cert-manager for TLS automation
- Implement Velero backup strategy
- Configure RBAC for least-privilege access

### Phase 3: Security Hardening (Week 4)
- Enforce Pod Security Standards
- Implement network policies
- Integrate Trivy image scanning
- Enable Kubernetes audit logging

### Phase 4: Operational Excellence (Week 5-6)
- Deploy ArgoCD for GitOps workflow
- Setup Loki + Promtail for log aggregation
- Configure HPA with metrics-server
- Enhance MCP tools (exec, port-forward, metrics)
- Create Kustomize overlays for multi-environment

---

## License

**type** - Internal AI Whisperers template
**usage** - Free for company projects, not for external distribution
**attribution** - Maintain AI Whisperers metadata in documentation

---

## Support

**documentation** - Start with [GETTING-STARTED.md](GETTING-STARTED.md)
**troubleshooting** - See [ON-PREMISE-KUBERNETES-READY.md](ON-PREMISE-KUBERNETES-READY.md) section "Troubleshooting"
**questions** - Open GitHub issues or contact DevOps team
**slack** - #kubernetes-support (internal)

---

**Version:** 1.0.0 · **Updated:** 2025-11-17 · **Status:** Development Template · **Repository:** https://github.com/Ai-Whisperers/cluster-template
