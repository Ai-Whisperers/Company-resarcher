# clustering-for-ai-whisperers-hosting-and-deploys

**Description:** Full config suite for devops and CICD on gitlab+kubernetes+docker-desktop+windowsWSL stack
**URL:** https://github.com/Ai-Whisperers/clustering-for-ai-whisperers-hosting-and-deploys
**Visibility:** PRIVATE

---

# Kubernetes Cluster Administration Repository
Doc-Type: Infrastructure Documentation · Version 1.0 · Updated 2025-11-10 · AI Whisperers

This repository provides production-grade Kubernetes cluster administration with GitOps workflows, automated backups, and comprehensive disaster recovery. Infrastructure configurations are declarative and version-controlled, enabling reproducible deployments across environments. The repository integrates Velero for application backup, etcd snapshots for state preservation, ArgoCD for continuous deployment, and GitLab for CI/CD pipelines.

## Quick Start

Deploy the complete infrastructure stack using these commands:

```bash
# Install core components
kubectl apply -f k8s/namespaces/namespaces.yaml
kubectl apply -f k8s/core/resource-quotas.yaml
kubectl apply -f k8s/storage/storage-classes.yaml

# Deploy backup infrastructure
kubectl apply -f config/velero/install.yaml
kubectl apply -f config/velero/schedules.yaml
kubectl apply -f config/etcd/snapshot-cronjob.yaml

# Install ArgoCD for GitOps
kubectl apply -f config/gitops/argocd/install.yaml
kubectl apply -f config/gitops/argocd/projects.yaml

# Deploy GitLab (after configuring secrets)
helm install gitlab gitlab/gitlab -f gitlab/infrastructure/values-production.yaml
```

## Repository Structure

```
k8s-cluster/
├── config/                    # Cluster configuration persistence
│   ├── velero/               # Backup and restore with Velero
│   ├── etcd/                 # etcd state snapshots
│   ├── gitops/               # ArgoCD/Flux GitOps configs
│   └── policies/             # Cluster-wide policies
│
├── gitlab/                   # GitLab production infrastructure
│   ├── infrastructure/       # GitLab deployment manifests
│   ├── runners/              # CI/CD runner configurations
│   └── policies/             # Network and security policies
│
├── docker-desktop/           # Docker Desktop local development
│   ├── contexts/             # Kubernetes context configs
│   ├── extensions/           # DD extension settings
│   └── settings/             # Docker daemon configuration
│
├── k8s/                      # Kubernetes cluster resources
│   ├── namespaces/           # Namespace definitions
│   ├── core/                 # Resource quotas, limits
│   ├── networking/           # Ingress, services, policies
│   ├── storage/              # Storage classes, PV/PVC
│   ├── security/             # RBAC, pod security
│   └── monitoring/           # Prometheus, Grafana
│
└── scripts/                  # Automation and tooling
```

## Core Components

### Backup & Disaster Recovery

**Velero** — Application-level backup and restore
- Full cluster backups daily at 2:00 AM (30-day retention)
- Critical namespace backups every 6 hours (7-day retention)
- GitLab hourly backups (72-hour retention)
- S3-compatible storage with encryption
- Automated volume snapshots

**etcd Snapshots** — Cluster state preservation
- Snapshots every 4 hours with 7-day retention
- Encrypted storage with AWS KMS
- Automated health checks and alerts
- Independent from Velero for redundancy

Configuration: `config/velero/` · `config/etcd/`

### GitOps Continuous Deployment

**ArgoCD** — Declarative GitOps automation
- Continuous sync from GitLab repositories
- Multi-project isolation (production, staging, dev)
- Automated rollbacks on health degradation
- GitLab SSO integration
- Slack notifications for deployments

**Application Sync Policy**
- Auto-sync enabled with self-healing
- Retry limit: 5 attempts with exponential backoff
- Prune orphaned resources automatically

Configuration: `config/gitops/argocd/`

### GitLab Infrastructure

**High Availability Deployment**
- 3 webservice replicas with 2Gi memory each
- 2 Sidekiq workers for background jobs
- 3 Gitaly replicas for Git storage (500Gi SSD)
- PostgreSQL 14 with read replicas
- Redis cluster with persistence

**Object Storage Integration**
- S3 buckets for artifacts, LFS, packages, registry
- Automated daily backups to S3
- 7-day daily, 4-week weekly, 12-month monthly retention

**CI/CD Runners**
- 5 Docker runners with 10 concurrent jobs
- 3 Kubernetes runners for native workloads
- Resource limits: 2 CPU, 4Gi memory per runner

Configuration: `gitlab/infrastructure/` · `gitlab/runners/`

### Security & Compliance

**Pod Security Standards**
- Restricted enforcement for production namespace
- Baseline for GitLab namespace
- Default deny-all network policies
- Automated service account token mounting disabled

**Network Segmentation**
- Namespace-level network isolation
- Explicit allow policies for required communication
- Ingress NGINX with ModSecurity and OWASP CRS

**TLS & Certificates**
- Automated TLS with cert-manager
- Let's Encrypt production issuer
- TLS 1.2+ with strong cipher suites

Configuration: `k8s/security/` · `gitlab/policies/`

### Monitoring & Observability

**Prometheus Stack**
- 30-day metric retention with 100Gi storage
- GitLab, ArgoCD, and cluster metrics
- Custom alerting rules for critical events
- Slack integration for notifications

**Grafana Dashboards**
- Pre-configured dashboards for cluster health
- GitLab performance metrics
- Resource utilization tracking
- Automated TLS ingress

Configuration: `k8s/monitoring/prometheus-values.yaml`

## Environment Workflows

### Production Deployment

```bash
# 1. Apply namespace and quotas
kubectl apply -f k8s/namespaces/namespaces.yaml
kubectl apply -f k8s/core/resource-quotas.yaml

# 2. Deploy storage infrastructure
kubectl apply -f k8s/storage/storage-classes.yaml

# 3. Install backup systems
kubectl create namespace velero
kubectl create secret generic velero-credentials --from-file=cloud=credentials-velero
kubectl apply -f config/velero/install.yaml
kubectl apply -f config/velero/schedules.yaml

# 4. Deploy etcd backup
kubectl apply -f config/etcd/snapshot-cronjob.yaml
kubectl create secret generic etcd-backup-secrets \
  --from-literal=kms_key_id=$KMS_KEY_ID \
  --from-literal=aws_access_key_id=$AWS_ACCESS_KEY_ID \
  --from-literal=aws_secret_access_key=$AWS_SECRET_ACCESS_KEY \
  -n etcd-backup

# 5. Install ArgoCD
kubectl create namespace argocd
kubectl apply -f config/gitops/argocd/install.yaml
kubectl apply -f config/gitops/argocd/projects.yaml

# 6. Configure GitLab secrets (replace placeholders)
kubectl apply -f gitlab/infrastructure/secrets-template.yaml

# 7. Deploy GitLab
helm repo add gitlab https://charts.gitlab.io/
helm install gitlab gitlab/gitlab \
  -f gitlab/infrastructure/values-production.yaml \
  --namespace gitlab

# 8. Deploy GitLab runners
helm repo add gitlab https://charts.gitlab.io/
helm install gitlab-runner gitlab/gitlab-runner \
  -f gitlab/runners/values-runners.yaml \
  --namespace gitlab-runners
```

### Local Development (Docker Desktop)

```bash
# 1. Enable Kubernetes in Docker Desktop
# Settings → Kubernetes → Enable Kubernetes

# 2. Configure resource limits (daemon.json)
cp docker-desktop/settings/daemon.json ~/.docker/daemon.json

# 3. Create development namespaces
kubectl apply -f k8s/namespaces/namespaces.yaml

# 4. Deploy minimal stack for testing
kubectl apply -f k8s/core/resource-quotas.yaml
kubectl apply -f config/gitops/argocd/install.yaml

# 5. Port forward services
kubectl port-forward -n argocd svc/argocd-server 8080:443
kubectl port-forward -n monitoring svc/grafana 3000:80
```

## Disaster Recovery Procedures

### Restore from Velero Backup

```bash
# List available backups
velero backup get

# Restore full cluster
velero restore create --from-backup full-cluster-backup-20250110

# Restore specific namespace
velero restore create --from-backup critical-namespaces-backup-20250110 \
  --include-namespaces gitlab
```

### Restore from etcd Snapshot

```bash
# Download snapshot from S3
aws s3 cp s3://k8s-etcd-snapshots/cluster-01/etcd-snapshot-20250110.db.gz .

# Decompress
gunzip etcd-snapshot-20250110.db.gz

# Restore etcd (requires cluster downtime)
ETCDCTL_API=3 etcdctl snapshot restore etcd-snapshot-20250110.db \
  --data-dir=/var/lib/etcd-restored \
  --initial-cluster=etcd-0=https://etcd-0:2380 \
  --initial-advertise-peer-urls=https://etcd-0:2380 \
  --name=etcd-0
```

## Access & Credentials

**ArgoCD**
- URL: https://argocd.company.com
- SSO: GitLab OAuth integration
- Initial password: `kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d`

**GitLab**
- URL: https://gitlab.company.com
- Root password: Stored in `gitlab-gitlab-initial-root-password` secret
- Registry: https://registry.company.com

**Grafana**
- URL: https://grafana.company.com
- Admin password: Set in `prometheus-values.yaml`

## Maintenance & Operations

### Backup Validation

```bash
# Check Velero backup status
velero backup describe full-cluster-backup-latest

# Verify etcd snapshot integrity
ETCDCTL_API=3 etcdctl snapshot status /backup/etcd-snapshot-latest.db -w table
```

### GitOps Sync

```bash
# Force ArgoCD sync
argocd app sync <application-name>

# Check sync status
argocd app get <application-name>
```

### Resource Monitoring

```bash
# Check namespace resource usage
kubectl top nodes
kubectl top pods -n production

# Review quota usage
kubectl describe resourcequota -n production
```

## Troubleshooting

**Issue**: Velero backup failing
- Check S3 credentials: `kubectl get secret velero-credentials -n velero`
- Verify storage location: `velero backup-location get`
- Review logs: `kubectl logs -n velero deployment/velero`

**Issue**: ArgoCD sync errors
- Check repository credentials: `kubectl get secret gitlab-repo-creds -n argocd`
- Verify application health: `argocd app get <app-name>`
- Review sync logs: `kubectl logs -n argocd deployment/argocd-application-controller`

**Issue**: GitLab pods failing
- Check resource quotas: `kubectl describe resourcequota -n gitlab`
- Verify PVC binding: `kubectl get pvc -n gitlab`
- Review pod logs: `kubectl logs -n gitlab <pod-name>`

---

```toon
repository_metadata:
  name: k8s-cluster-administration
  version: "1.0.0"
  updated: "2025-11-10"
  status: production

  technology_stack:
    orchestration: kubernetes-1.28
    gitops: argocd-2.9.0
    backup: velero-1.12.0
    ci_cd: gitlab-16.7.0
    monitoring: prometheus-stack-55.0.0

  deployment_targets:
    production:
      provider: aws
      regions: [us-east-1]
      availability_zones: 3

    development:
      provider: docker-desktop
      local: true

  operational_requirements:
    backup_frequency:
      full: daily
      incremental: hourly
      etcd: 4h

    retention_policies:
      backups_daily: 7
      backups_weekly: 4
      backups_monthly: 12

    monitoring:
      uptime_target: 99.9%
      alert_response: 5m
      metrics_retention: 30d

  security_compliance:
    encryption_at_rest: required
    encryption_in_transit: required
    pod_security_standard: restricted
    network_policies: enforced
    rbac: enabled
    audit_logging: enabled
```
