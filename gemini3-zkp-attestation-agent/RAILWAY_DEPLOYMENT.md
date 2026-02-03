# Railway Deployment Guide - ZKP Attestation Agent

This guide will help you deploy the ZKP Attestation Agent to Railway.

## Prerequisites

- Railway account (https://railway.app)
- GitHub repository access
- Basic understanding of environment variables

## Quick Deploy

### Option 1: Deploy from GitHub (Recommended)

1. **Connect to Railway**
   ```
   Visit: https://railway.app/new
   Click: "Deploy from GitHub repo"
   Select: Compliledger/Zkp_Assestation_gemini3
   ```

2. **Add PostgreSQL Database**
   ```
   In Railway dashboard:
   - Click "+ New"
   - Select "Database"
   - Choose "PostgreSQL"
   - Railway will automatically set DATABASE_URL
   ```

3. **Configure Service**
   ```
   - Root Directory: gemini3-zkp-attestation-agent
   - Build Command: (auto-detected from railway.toml)
   - Start Command: (auto-detected from railway.toml)
   ```

### Option 2: Deploy with Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Navigate to project
cd gemini3-zkp-attestation-agent

# Initialize Railway project
railway init

# Add PostgreSQL
railway add --database postgresql

# Deploy
railway up
```

## Required Environment Variables

Set these in Railway Dashboard → Variables:

### Essential (Must Set)

```env
# Application
APP_ENV=production
DEBUG=false

# Security - CRITICAL: Generate secure secrets!
JWT_SECRET=<generate-with-openssl-rand-hex-32>
ENCRYPTION_KEY=<generate-with-openssl-rand-hex-32>

# Database (Auto-set by Railway PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### Optional (Set as needed)

```env
# Algorand TestNet (for blockchain anchoring)
ALGORAND_MNEMONIC=<your-25-word-mnemonic>
ALGORAND_ANCHOR_APP_ID=<deployed-contract-app-id>

# Storage (if using S3)
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
AWS_S3_BUCKET=<your-bucket>

# Monitoring (optional)
SENTRY_DSN=<your-sentry-dsn>
SENTRY_ENVIRONMENT=production

# CORS (update with your frontend URL)
CORS_ORIGINS=["https://your-frontend.com"]
```

## Generate Secure Secrets

```bash
# JWT_SECRET
openssl rand -hex 32

# ENCRYPTION_KEY
openssl rand -hex 32
```

Or use Python:
```python
import secrets
print(secrets.token_hex(32))
```

## Post-Deployment Setup

### 1. Verify Deployment

```bash
# Check health endpoint
curl https://your-app.railway.app/health/live

# Expected response:
{"status": "alive"}
```

### 2. Access API Documentation

```
https://your-app.railway.app/docs
```

### 3. Initialize Database (First Deploy Only)

The database tables are automatically created on first startup via:
```python
# app/main.py - lifespan event
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

### 4. Generate Test JWT Token

```python
# Run locally or in Railway shell
python -c "from app.core.auth import create_token_for_user; print(create_token_for_user('admin','prod',['zkpa:admin']))"
```

## Railway Configuration Files

### `railway.toml`
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"
healthcheckPath = "/health/live"
restartPolicyType = "ON_FAILURE"
```

### `nixpacks.toml`
```toml
[phases.setup]
nixPkgs = ["python311", "postgresql", "gcc", "libpqxx"]

[start]
cmd = "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"
```

### `Procfile`
```
web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | - | PostgreSQL connection string (auto-set by Railway) |
| `JWT_SECRET` | ✅ | - | Secret key for JWT tokens |
| `ENCRYPTION_KEY` | ✅ | - | Key for data encryption |
| `APP_ENV` | ⚠️ | development | Set to `production` |
| `DEBUG` | ⚠️ | true | Set to `false` in production |
| `PORT` | ❌ | 8000 | Auto-set by Railway |
| `ALGORAND_MNEMONIC` | ❌ | - | For blockchain anchoring |
| `CORS_ORIGINS` | ❌ | localhost | Update with your frontend URL |

## Troubleshooting

### Issue: "Application startup failed. Exiting."

**Cause**: Database connection failed

**Solution**:
1. Verify PostgreSQL service is running in Railway
2. Check `DATABASE_URL` is set correctly
3. Ensure database allows connections from Railway app

### Issue: "ModuleNotFoundError"

**Cause**: Missing dependencies

**Solution**:
1. Verify `requirements.txt` is in root directory
2. Check Railway build logs
3. Try manual rebuild in Railway dashboard

### Issue: "Health check failed"

**Cause**: Database not ready or app crashed

**Solution**:
1. Check `/health/live` endpoint (doesn't require DB)
2. Check Railway logs for errors
3. Verify environment variables are set

### Issue: "403 Forbidden / CORS error"

**Cause**: CORS not configured for your domain

**Solution**:
```env
CORS_ENABLED=true
CORS_ORIGINS=["https://your-frontend.com","https://www.your-frontend.com"]
```

## Monitoring & Logs

### View Logs
```bash
# Using Railway CLI
railway logs

# Or in Railway Dashboard
Project → Deployments → View Logs
```

### Metrics Endpoint
```
GET /metrics
```
Returns Prometheus-compatible metrics

### Health Endpoints

- `/health/live` - Simple liveness check (no DB)
- `/health/ready` - Readiness check (requires DB)
- `/health` - Full health check with components

## Scaling

### Vertical Scaling (Resources)
```
Railway Dashboard → Settings → Resources
- Increase RAM (default: 512MB)
- Increase CPU (default: shared)
```

### Horizontal Scaling
Railway Pro plan supports multiple instances with load balancing.

## Database Backups

Railway automatically backs up PostgreSQL databases. To restore:
```
Railway Dashboard → Database → Backups → Restore
```

## Custom Domain

1. Railway Dashboard → Settings → Domains
2. Click "Add Domain"
3. Add your custom domain (e.g., `api.yourdomain.com`)
4. Update DNS records as shown by Railway

## Security Checklist

- [ ] Set `DEBUG=false` in production
- [ ] Generate and set secure `JWT_SECRET`
- [ ] Generate and set secure `ENCRYPTION_KEY`
- [ ] Configure `CORS_ORIGINS` to only allow your domains
- [ ] Enable HTTPS (Railway provides this automatically)
- [ ] Set up Sentry for error monitoring
- [ ] Review and set `RATE_LIMIT_*` variables

## Cost Estimation

Railway pricing (as of 2026):
- **Hobby Plan**: $5/month
  - 512 MB RAM, 1 vCPU
  - 100GB network egress
  - Community support

- **Pro Plan**: $20/month
  - 8GB RAM, 4 vCPU
  - 100GB network egress
  - Priority support

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Configure environment variables
3. ✅ Verify health endpoints
4. ✅ Test API via Swagger UI
5. ⏭️ Set up custom domain (optional)
6. ⏭️ Configure monitoring (Sentry)
7. ⏭️ Fund Algorand account for blockchain features

## Support Resources

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: https://github.com/Compliledger/Zkp_Assestation_gemini3/issues

## Example Deployment Script

Save as `deploy-to-railway.sh`:

```bash
#!/bin/bash

echo "🚂 Deploying ZKP Attestation Agent to Railway..."

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Install: npm i -g @railway/cli"
    exit 1
fi

# Login check
railway whoami || railway login

# Navigate to project
cd gemini3-zkp-attestation-agent

# Deploy
echo "🚀 Starting deployment..."
railway up

echo "✅ Deployment initiated!"
echo "📊 View logs: railway logs"
echo "🌐 View app: railway open"
```

## Production Readiness Checklist

Before going live:

- [ ] All required environment variables set
- [ ] Database migrations completed
- [ ] Health checks passing
- [ ] API documentation accessible
- [ ] JWT authentication working
- [ ] CORS configured correctly
- [ ] Error monitoring set up (Sentry)
- [ ] Logs reviewed for errors
- [ ] Load testing completed
- [ ] Backup strategy confirmed
- [ ] Custom domain configured (if needed)
- [ ] SSL/HTTPS verified

---

**Need Help?** Open an issue on GitHub or check Railway documentation.
