# Quick Start - CI/CD Setup

## Prerequisites

- GitHub account with repository access
- Docker installed on deployment server
- SSH access to deployment server

## 5-Minute Setup

### 1. Enable Package Publishing (2 min)

**Important:** You must enable package creation for GitHub Container Registry.

1. Go to: `Settings` → `Actions` → `General`
2. Under "Workflow permissions":
   - Select **"Read and write permissions"**
   - Check **"Allow GitHub Actions to create and approve pull requests"**
3. Click **Save**

**For organization repositories:**
1. Go to: Organization Settings → `Packages` → `Package creation`
2. Under "Package creation":
   - Allow members to publish packages
3. Ensure GitHub Actions has permission to create packages:
   - `Settings` → `Actions` → `General` → Workflow permissions → "Read and write"

### 2. Add Deployment Secrets (2 min)

Go to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

Add these secrets:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `DEPLOY_SSH_KEY` | Private SSH key | `-----BEGIN RSA PRIVATE KEY-----...` |
| `DEPLOY_HOST` | Server IP/hostname | `192.168.1.100` |
| `DEPLOY_USER` | SSH username | `ubuntu` |
| `DEPLOY_PATH` | Deploy directory | `/home/ubuntu/crm-app` |

Optional:
- `STAGING_URL` - e.g., `http://staging.example.com`
- `PROD_URL` - e.g., `https://example.com`

### 3. Trigger First Deployment (1 min)

```bash
# Push to main branch
git push origin main

# Or manually trigger from GitHub:
# Actions → CI/CD Pipeline → Run workflow
```

That's it! 🎉

## What Happens Automatically

When you push to `main` or `develop`:

1. ✅ Tests run (backend + frontend)
2. ✅ Version bumps (minor by default)
3. ✅ Docker images build
4. ✅ Images push to GitHub Container Registry
5. ✅ Deployment to server

## View Build Status

Check the **Actions** tab in your repository to see:
- Build progress
- Test results
- Deployment status

## Access Your Application

After deployment:
- **Frontend**: `http://your-server-ip`
- **Backend API**: `http://your-server-ip:8000/docs`
- **Health Check**: `http://your-server-ip:8000/api/v1/health`

## Manual Deployment (Alternative)

If you prefer manual deployment:

```bash
# On your deployment server
cd ~/crm-app
./deploy.sh production
```

## Troubleshooting

### Build Fails
- Check Actions logs for errors
- Ensure tests pass locally: `npm test` / `pytest`

### Deployment Fails
- Verify SSH key in secrets
- Check server has Docker installed
- Ensure port 80 and 8000 are available

### View Server Logs
```bash
ssh user@server
cd ~/crm-app
docker-compose logs -f
```

## Next Steps

- Configure custom domain
- Set up SSL/HTTPS
- Configure monitoring
- Set up database backups

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed documentation.
