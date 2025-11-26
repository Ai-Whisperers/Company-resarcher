# aws-docker-mcp

**Description:** 
**URL:** https://github.com/Ai-Whisperers/aws-docker-mcp
**Visibility:** PRIVATE

---

# MCP Development Hub

A comprehensive local development environment integrating Docker and AWS MCP (Model Context Protocol) servers for AI-powered development workflows.

## Overview

The MCP Development Hub provides a unified platform for running both Docker and AWS MCP servers locally, enabling seamless integration with Claude Desktop and other AI assistants. It includes pre-configured services, automatic setup scripts, and comprehensive monitoring capabilities.

## Features

### Docker Integration
- **MCP Gateway**: Central hub for all Docker MCP servers
- **Pre-configured Services**: PostgreSQL, Redis, MinIO, LocalStack
- **Docker Hub Integration**: Direct access to Docker Hub repositories
- **Container Management**: Full control over Docker containers via MCP

### AWS Integration
- **45+ AWS MCP Servers**: Complete suite of AWS service integrations
- **LocalStack Support**: Test AWS services locally without cloud costs
- **Hybrid Mode**: Seamlessly switch between local and cloud AWS resources
- **SSO Support**: Secure authentication with AWS SSO

### Development Services
- **PostgreSQL**: Relational database with MCP server integration
- **Redis**: In-memory cache and message broker
- **MinIO**: S3-compatible object storage for local development
- **LocalStack**: Complete AWS cloud stack running locally

### Monitoring (Optional)
- **Grafana**: Visualization and dashboards
- **Prometheus**: Metrics collection and alerting

## Prerequisites

- Docker Desktop (Windows/macOS/Linux)
- AWS CLI (optional, for cloud integration)
- Python 3.8+ (for AWS MCP servers)
- Claude Desktop or compatible MCP client

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository (or copy the mcp-dev-hub folder)
cd mcp-dev-hub

# Make scripts executable (Unix/Linux/macOS)
chmod +x scripts/*.sh

# Run the setup script
./scripts/setup.sh
```

For Windows users with Git Bash:
```bash
bash scripts/setup.sh
```

### 2. Configure Environment

Edit the `.env` file with your credentials:

```bash
# Docker credentials
DOCKER_HUB_USERNAME=your_username
DOCKER_HUB_TOKEN=your_token

# AWS configuration
AWS_PROFILE=your_profile
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Service passwords (change these!)
POSTGRES_PASSWORD=secure_password
MINIO_ROOT_PASSWORD=secure_password
```

### 3. Start Services

```bash
# Start core services only
./scripts/start.sh

# Start with monitoring (Grafana + Prometheus)
./scripts/start.sh --monitoring

# Start all services
./scripts/start.sh --all
```

### 4. Configure Claude Desktop

The setup script can automatically configure Claude Desktop. To manually configure:

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

Copy the contents from `config/claude_desktop_config.json` to the appropriate location.

## Service Access Points

| Service | URL/Port | Default Credentials |
|---------|----------|-------------------|
| MCP Gateway UI | http://localhost:8080 | - |
| MCP API | http://localhost:9000 | - |
| PostgreSQL | localhost:5432 | mcp_user / (see .env) |
| Redis | localhost:6379 | - |
| MinIO Console | http://localhost:9001 | mcp_admin / (see .env) |
| MinIO API | http://localhost:9002 | mcp_admin / (see .env) |
| LocalStack | http://localhost:4566 | - |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | - |

## Management Scripts

### setup.sh
Initial setup and configuration wizard
```bash
./scripts/setup.sh
```

### start.sh
Start all services
```bash
./scripts/start.sh [--monitoring|--all]
```

### stop.sh
Stop all services
```bash
./scripts/stop.sh [--volumes]  # --volumes removes all data
```

### status.sh
Check service health and status
```bash
./scripts/status.sh
```

### logs.sh
View service logs
```bash
./scripts/logs.sh [service] [-f] [-t 100]

# Examples:
./scripts/logs.sh postgres -f     # Follow PostgreSQL logs
./scripts/logs.sh -t 50          # Last 50 lines from all services
```

## AWS MCP Servers

### Core Servers (Install First)

1. **aws-core**: Orchestrates all other AWS MCP servers
2. **aws-cloudcontrol**: Natural language infrastructure management
3. **aws-documentation**: Access AWS docs and best practices

### Service-Specific Servers

- **S3**: Object storage management
- **Lambda**: Serverless function management
- **DynamoDB**: NoSQL database operations
- **EC2**: Compute instance management
- **CloudWatch**: Monitoring and logs

### Local Development with LocalStack

LocalStack provides local implementations of AWS services:

```bash
# Configure AWS CLI for LocalStack
aws configure set aws_access_key_id test --profile localstack
aws configure set aws_secret_access_key test --profile localstack
aws configure set region us-east-1 --profile localstack

# Use LocalStack endpoint
aws --endpoint-url=http://localhost:4566 --profile localstack s3 ls
```

## Docker MCP Integration

### Available MCP Servers

The Docker MCP Gateway provides access to:
- Docker Hub repositories
- Container management
- Image operations
- Network management
- Volume management
- Secret management

### Security Configuration

Edit `docker/docker-mcp-settings.yaml` to configure:
- Allowed mount paths
- Read-only restrictions
- Resource limits
- Network isolation

## Troubleshooting

### Common Issues

#### Docker daemon not running
```bash
# Start Docker Desktop manually
# Windows/macOS: Open Docker Desktop application
# Linux: sudo systemctl start docker
```

#### AWS credentials not configured
```bash
# Configure AWS CLI
aws configure

# Or use SSO
aws sso configure
```

#### Port conflicts
```bash
# Check what's using a port
netstat -ano | findstr :8080  # Windows
lsof -i :8080                  # macOS/Linux

# Change ports in docker-compose.yml if needed
```

#### Services not starting
```bash
# Check logs
./scripts/logs.sh [service-name]

# Restart specific service
docker-compose restart [service-name]

# Clean restart
./scripts/stop.sh --volumes
./scripts/start.sh
```

### Reset Everything

```bash
# Stop all services and remove volumes
./scripts/stop.sh --volumes

# Remove all MCP containers and networks
docker rm -f $(docker ps -aq --filter "name=mcp-")
docker network rm mcp-network

# Start fresh
./scripts/setup.sh
./scripts/start.sh
```

## Advanced Configuration

### Custom MCP Servers

Add custom MCP servers to `config/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "custom-server": {
      "command": "node",
      "args": ["path/to/server.js"],
      "env": {
        "API_KEY": "${CUSTOM_API_KEY}"
      }
    }
  }
}
```

### Production Considerations

For production use:

1. **Security**: Update all default passwords in `.env`
2. **Persistence**: Configure volume backups
3. **Monitoring**: Enable Grafana and Prometheus
4. **Resource Limits**: Adjust in `docker-compose.yml`
5. **Network Security**: Configure firewall rules

## Project Structure

```
mcp-dev-hub/
├── docker/                 # Docker MCP configurations
│   ├── claude_docker_config.json
│   └── docker-mcp-settings.yaml
├── aws/                   # AWS MCP configurations
│   ├── claude_aws_config.json
│   └── aws-mcp-settings.yaml
├── config/                # Hub configuration files
│   ├── claude_desktop_config.json
│   └── mcp-hub-config.json
├── scripts/               # Management scripts
│   ├── setup.sh
│   ├── start.sh
│   ├── stop.sh
│   ├── status.sh
│   └── logs.sh
├── docs/                  # Additional documentation
├── docker-compose.yml     # Service definitions
├── .env.example          # Environment template
└── README.md             # This file
```

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is provided as-is for development purposes. Ensure you comply with all relevant licenses for the services and tools included.

## Support

For issues specific to:
- **Docker MCP**: Check [Docker MCP documentation](https://docs.docker.com/mcp)
- **AWS MCP**: See [AWS MCP documentation](https://awslabs.github.io/mcp/)
- **Claude Desktop**: Visit [Claude documentation](https://docs.anthropic.com/claude)

## Acknowledgments

Built using:
- Docker and Docker Compose
- AWS MCP Servers by AWS Labs
- LocalStack for AWS emulation
- PostgreSQL, Redis, MinIO
- Grafana and Prometheus for monitoring