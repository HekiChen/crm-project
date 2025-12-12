# CI/CD Deployment Guide

This repository includes a complete CI/CD pipeline using GitHub Actions for building, testing, and deploying the CRM application.

## Overview

The pipeline automatically:
- ✅ Runs tests for both backend and frontend
- ✅ Bumps version numbers (patch/minor/major)
- ✅ Builds Docker containers
- ✅ Pushes images to GitHub Container Registry
- ✅ Deploys to staging/production environments

## Pipeline Stages

### 1. Version Management
- Automatically bumps version on push to `main` or `develop`
- Backend: Updates `pyproject.toml`
- Frontend: Updates `package.json`
- Default: **minor** version bump

### 2. Testing
- **Backend**: Runs pytest, linting (ruff), coverage reports
- **Frontend**: Runs type-check, linting (eslint), and builds

### 3. Build & Push Docker Images
- Builds multi-architecture Docker images
- Pushes to GitHub Container Registry (ghcr.io)
- Tags: `latest`, `branch-name`, `sha-<commit>`

### 4. Deployment
- **Staging**: Auto-deploys from `develop` branch
- **Production**: Auto-deploys from `main` branch
- Uses docker-compose for orchestration

## Setup Instructions

### 1. Configure GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions, and add:

#### Required Secrets:
```
DEPLOY_SSH_KEY          # SSH private key for deployment server
DEPLOY_HOST             # Deployment server hostname/IP
DEPLOY_USER             # SSH username
DEPLOY_PATH             # Path to deployment directory
```

#### Optional Secrets:
```
STAGING_URL             # Staging environment URL (for health checks)
PROD_URL                # Production environment URL (for health checks)
VITE_API_BASE_URL       # API base URL for frontend (default: /api/v1)
```

### 2. Enable GitHub Container Registry

1. Go to your repository Settings → Actions → General
2. Scroll to "Workflow permissions"
3. Select "Read and write permissions"
4. Check "Allow GitHub Actions to create and approve pull requests"

### 3. Prepare Deployment Server

On your deployment server:

```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Create deployment directory
mkdir -p ~/crm-app
cd ~/crm-app

# Copy docker-compose.prod.yml and .env file
# (These will be pulled from the repository during deployment)

# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

### 4. Configure Environment Variables

Copy and configure the production environment:

```bash
cp .env.production.example .env
# Edit .env with your actual values
nano .env
```

## Manual Deployment

### Deploy Latest Version:
```bash
# Pull latest code
git pull origin main

# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

### View Logs:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### Stop Services:
```bash
docker-compose -f docker-compose.prod.yml down
```

## Triggering Workflows

### Automatic Triggers:
- Push to `main` → Build, test, deploy to production
- Push to `develop` → Build, test, deploy to staging
- Pull request → Run tests only

### Manual Trigger:
1. Go to Actions tab
2. Select "CI/CD Pipeline"
3. Click "Run workflow"
4. Choose version bump type: patch/minor/major

## Version Bumping

### Automatic (on push to main/develop):
```bash
git push origin main  # Bumps minor version by default
```

### Manual:
```bash
# Backend
cd backend
bump2version minor  # or patch, major

# Frontend
cd frontend
npm version minor  # or patch, major
```

## Container Images

Images are available at:
```
ghcr.io/<your-username>/crm-project/backend:latest
ghcr.io/<your-username>/crm-project/frontend:latest
```

### Pull Images:
```bash
docker pull ghcr.io/<your-username>/crm-project/backend:latest
docker pull ghcr.io/<your-username>/crm-project/frontend:latest
```

## Health Checks

### Backend:
```bash
curl http://localhost:8000/api/v1/health
```

### Frontend:
```bash
curl http://localhost/health
```

## Rollback

To rollback to a previous version:

```bash
# List available tags
docker images ghcr.io/<your-username>/crm-project/backend

# Update docker-compose.prod.yml to use specific tag
# Or set environment variable:
export BACKEND_TAG=sha-abc123
export FRONTEND_TAG=sha-abc123

# Restart with specific version
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring

Check deployment status:
```bash
# Container status
docker-compose -f docker-compose.prod.yml ps

# Resource usage
docker stats

# Health checks
docker-compose -f docker-compose.prod.yml exec backend curl http://localhost:8000/api/v1/health
docker-compose -f docker-compose.prod.yml exec frontend curl http://localhost/health
```

## Troubleshooting

### Build Failures:
- Check GitHub Actions logs
- Verify all tests pass locally
- Check Docker build context

### Deployment Failures:
- Verify SSH key is correct
- Check server connectivity
- Verify Docker is installed and running
- Check disk space on server

### Container Issues:
```bash
# View logs
docker-compose -f docker-compose.prod.yml logs

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

## Security Notes

1. **Never commit secrets** to the repository
2. Use GitHub Secrets for sensitive data
3. Rotate SSH keys regularly
4. Use strong `SECRET_KEY` in production
5. Enable HTTPS with SSL/TLS certificates
6. Keep Docker images updated

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
