# Company-Information

**Description:** Centralized infrastructure hub for ai-whisperers company.
**URL:** https://github.com/Ai-Whisperers/Company-Information
**Visibility:** PUBLIC

---

# AI-Whisperers Org OS (Company-Information) MVP

A modern web-based control plane for managing the AI-Whisperers organization's repositories, providing automated health monitoring, Azure DevOps synchronization, and documentation governance.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/Ai-Whisperers/Company-Information.git
cd Company-Information

# Install dependencies
npm install

# Setup environment (ROOT .env - single source of truth)
cp .env.example .env
# Edit .env with your GitHub token and other credentials

# Initialize database
cd services/jobs
npx prisma migrate deploy
npx prisma generate
cd ../..

# Start development servers
npm run dev  # Runs both dashboard (port 3001) and jobs service (port 4000)
```

Visit http://localhost:3001 to access the dashboard.

## ⚙️ Environment Configuration

This project uses a **single ROOT `.env` file** as the source of truth for all services.

**DO NOT** create `.env` files in subdirectories (services/jobs, apps/dashboard).

### Required Variables

```bash
# GitHub (required)
GITHUB_TOKEN=your_github_personal_access_token

# Database (required)
DATABASE_URL=file:./services/jobs/dev.db

# Services (auto-configured)
JOBS_PORT=4000
DASHBOARD_PORT=3001
```

See `.env.example` for the complete list of variables with documentation.

### How It Works

1. **Root Contract**: All environment variables defined in ROOT `.env`
2. **Jobs Service**: Reads from `../../.env` (relative to services/jobs/src)
3. **Dashboard**: Loads ROOT `.env` via dotenv
4. **Scripts**: Use PathResolver for automatic project root detection

**No hardcoded paths anywhere!** ✅

## 📊 Features

### MVP Core Features

#### 1. **Org Pulse Report** ✅
- Weekly automated health reports
- Repository activity metrics
- Top contributor tracking
- Markdown and HTML output formats
- Historical report storage

#### 2. **ADO↔GitHub Linker** ✅
- Bidirectional work item linking
- Automatic PR/commit parsing for work item IDs
- Drift detection with <10 minute SLO
- Automatic repair mode for broken links

#### 3. **Documentation Gate** ✅
- CI checks for required documentation
- Template-based bootstrapping
- Label-triggered PR generation
- Configurable documentation policies

#### 4. **Multi-Agent Orchestration** ✅ 🆕
- Plugin-based agent architecture (6 agents, 4 plugins)
- Multi-agent workflow automation (4 pre-configured workflows)
- Integration with existing NestJS services
- Progressive disclosure pattern for minimal token usage
- Clear evolution path to MCP server (see [roadmap](./automation/MCP_EVOLUTION_ROADMAP.md))

**Available Workflows:**
- `weekly-org-pulse` - Weekly health reporting
- `pr-quality-gate` - Automated PR validation
- `ado-sync-cycle` - ADO-GitHub synchronization
- `compliance-audit` - Full repository compliance scan

See [automation/README.md](./automation/README.md) for complete documentation.

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│  Express Dashboard (3001)       │ ← User Interface
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   NestJS Jobs Service (4000)    │ ← Backend API
└────────────┬────────────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌─────────┐     ┌──────────┐
│ SQLite/ │     │  Redis   │
│Postgres │     │(Optional)│
└─────────┘     └──────────┘
```

## 📁 Project Structure

```
company-information/
├── apps/
│   └── dashboard/          # Express web dashboard (Vanilla JS)
├── services/
│   └── jobs/              # NestJS backend service
├── automation/
│   ├── orchestration/     # 🆕 Multi-agent orchestration system
│   │   ├── config/        # Agent, workflow, plugin configs
│   │   ├── core/          # Orchestration engine
│   │   ├── agents/        # Agent implementations
│   │   └── workflows/     # Workflow orchestrators
│   └── github-actions/    # CI/CD workflows
├── templates/             # Documentation templates
├── reports/              # Generated reports
├── scripts/              # PowerShell automation scripts
└── package.json          # Monorepo root
```

## 🔧 Configuration

### Required Environment Variables

```bash
# Port Configuration
DASHBOARD_PORT=3001      # Dashboard server port (default: 3001)
JOBS_PORT=4000          # Jobs service port (default: 4000)

# GitHub
GITHUB_TOKEN=            # Personal access token with repo, workflow scopes
GITHUB_ORG=Ai-Whisperers

# Azure DevOps
AZURE_DEVOPS_PAT=        # Personal access token
AZURE_DEVOPS_ORG=        # Your ADO organization
AZURE_DEVOPS_PROJECT=    # Your ADO project

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/orgos_db
# or use SQLite for development:
# DATABASE_URL=file:./dev.db

# Redis (optional for job queues)
REDIS_HOST=localhost
REDIS_PORT=6379
```

See `.env.example` for complete configuration options.

## 📝 Development

### Running Services

```bash
# Dashboard only
npm run dev:dashboard

# Jobs service only
npm run dev:jobs

# Both services
npm run dev

# Run tests
npm test

# Lint code
npm run lint

# Type check
npm run typecheck
```

### Database Management

```bash
cd services/jobs

# Create migration
npx prisma migrate dev --name your_migration_name

# Apply migrations
npx prisma migrate deploy

# Open Prisma Studio
npx prisma studio
```

### Adding New Features

1. **Scanner**: Add to `services/jobs/src/scanners/`
2. **API Endpoint**: Add to appropriate module in `services/jobs/src/`
3. **Dashboard UI**: Update `apps/dashboard/dashboard.js` (vanilla JS)
4. **GitHub Action**: Add to `automation/github-actions/`

## 🚢 Deployment

### Production Deployment

```bash
# Build jobs service
npm run build:jobs

# Deploy dashboard (static hosting - no build required)
# Dashboard can be served from any static host or reverse proxy

# Deploy jobs service (Docker)
cd services/jobs
docker build -t org-os-jobs .
docker run -p 4000:4000 org-os-jobs

# Or deploy dashboard with jobs service
cd apps/dashboard
node api-server.js
```

### GitHub Actions Setup

1. Add these secrets to your repository:
   - `GITHUB_TOKEN`
   - `AZURE_DEVOPS_PAT`
   - `JOBS_API_KEY`
   - `SLACK_WEBHOOK_URL` (optional)

2. Enable GitHub Actions workflows

3. The following will run automatically:
   - Weekly Org Pulse (Mondays 9 AM)
   - Daily health scans (2 AM)
   - ADO sync (every 6 hours)
   - Docs gate (on every PR)

## 📊 API Documentation

### Dashboard API (Port 3001)
- `GET /api/health` - Health check
- `GET /api/config` - Get runtime configuration
- `GET /api/project/:name/todos` - Get project TODOs
- `GET /api/project/:name/github` - Get GitHub data
- `POST /api/excalibur/sync` - Run Excalibur sync

### Jobs Service API (Port 4000)
- `POST /api/scanners/health/trigger` - Trigger health scan
- `POST /api/sync/ado-github/trigger` - Trigger ADO sync
- `POST /api/reporters/org-pulse/generate` - Generate report
- `GET /api/reports/org-pulse/:week` - Get weekly report

Full API documentation available at http://localhost:4000/api (Swagger) when running locally.

## 🔍 Monitoring

### Health Metrics
- Repository health scores (0-100)
- Stale PR detection
- Branch protection status
- Activity tracking

### Performance Targets
- Dashboard load: <1.5s (P95)
- Weekly scan: <8 minutes
- ADO sync lag: <10 minutes
- Report generation: <15 minutes

## 🐛 Troubleshooting

### Common Issues

**Database connection failed**
```bash
# Check PostgreSQL is running
pg_isready

# Verify connection string
psql $DATABASE_URL
```

**GitHub API rate limited**
```bash
# Check rate limit status
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit
```

**Redis not running (optional)**
- Bull queues require Redis for background jobs
- For development without Redis, job features will be disabled
- Install Redis: https://redis.io/docs/getting-started/

**ADO sync not working**
- Verify PAT has work item read/write permissions
- Check organization and project names are correct
- Ensure work items use standard ID patterns (#123, WI123)

## 🤝 Contributing

See [CONTRIBUTING.md](../../../CONTRIBUTING.md) for development guidelines.

## 📄 License

MIT License - see [LICENSE](../../../LICENSE) for details.

## 🔗 Related Repositories

- [Comment-Analyzer](https://github.com/Ai-Whisperers/Comment-Analyzer)
- [AI-Investment](https://github.com/Ai-Whisperers/AI-Investment)
- [clockify-ADO-automated-report](https://github.com/Ai-Whisperers/clockify-ADO-automated-report)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Ai-Whisperers/Company-Information/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Ai-Whisperers/Company-Information/discussions)
- **Email**: support@ai-whisperers.com

---

Built with ❤️ by AI-Whisperers Team