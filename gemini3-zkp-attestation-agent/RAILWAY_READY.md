# ✅ Railway Deployment - Ready Checklist

## Status: **READY FOR DEPLOYMENT** 🚀

All necessary files and configurations have been created for Railway deployment.

---

## Files Created/Updated

### ✅ Railway Configuration Files
- [x] `railway.toml` - Railway deployment config (updated healthcheck to `/health/live`)
- [x] `nixpacks.toml` - Build configuration with Python 3.11
- [x] `Procfile` - Process file for web service
- [x] `runtime.txt` - Python version specification (3.11.9)
- [x] `.dockerignore` - Docker build optimization

### ✅ Documentation
- [x] `RAILWAY_DEPLOYMENT.md` - Complete deployment guide
- [x] `.env.production.example` - Production environment variables template
- [x] `README.md` - Updated with deployment section

### ✅ Application Code
- [x] Health endpoints (`/health/live`, `/health/ready`, `/health`)
- [x] Database auto-initialization on startup
- [x] Environment variable validation with proper defaults
- [x] CORS configuration for production
- [x] Security settings (JWT, encryption)

---

## Pre-Deployment Checklist

Before deploying to Railway, ensure:

- [ ] GitHub repository is up to date
- [ ] All changes are committed and pushed
- [ ] Railway account is created
- [ ] Credit card added to Railway (if using paid features)

---

## Deployment Steps

### 1. Deploy to Railway (2 minutes)

```bash
# Option A: Via Railway Dashboard
1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select: Compliledger/Zkp_Assestation_gemini3
4. Set root directory: gemini3-zkp-attestation-agent
5. Click "Deploy"

# Option B: Via Railway CLI
railway login
cd gemini3-zkp-attestation-agent
railway init
railway up
```

### 2. Add PostgreSQL Database (1 minute)

```bash
# In Railway Dashboard
1. Click "+ New" → "Database" → "PostgreSQL"
2. DATABASE_URL will be automatically set
3. Wait for provisioning (30 seconds)
```

### 3. Set Environment Variables (2 minutes)

**Required (must set manually):**

```bash
# Generate secrets
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# In Railway Dashboard → Variables, add:
JWT_SECRET=<your-generated-secret>
ENCRYPTION_KEY=<your-generated-key>
APP_ENV=production
DEBUG=false
```

**Optional (recommended):**

```env
CORS_ORIGINS=["https://your-frontend.com"]
SENTRY_DSN=your-sentry-dsn
ALGORAND_MNEMONIC=your-25-word-mnemonic
```

### 4. Verify Deployment (1 minute)

```bash
# Check health
curl https://your-app.railway.app/health/live
# Should return: {"status":"alive"}

# Check API docs
open https://your-app.railway.app/docs
```

---

## Environment Variables Quick Reference

| Variable | Required | Where to Get |
|----------|----------|--------------|
| `DATABASE_URL` | ✅ | Auto-set by Railway PostgreSQL |
| `JWT_SECRET` | ✅ | Generate: `openssl rand -hex 32` |
| `ENCRYPTION_KEY` | ✅ | Generate: `openssl rand -hex 32` |
| `APP_ENV` | ⚠️ | Set to: `production` |
| `DEBUG` | ⚠️ | Set to: `false` |
| `PORT` | ❌ | Auto-set by Railway |

---

## What Railway Will Do Automatically

1. ✅ Detect Python 3.11 from `runtime.txt`
2. ✅ Install dependencies from `requirements.txt`
3. ✅ Run database migrations on startup
4. ✅ Set PORT environment variable
5. ✅ Provide SSL/HTTPS automatically
6. ✅ Monitor health via `/health/live`
7. ✅ Auto-restart on failure
8. ✅ Set DATABASE_URL from PostgreSQL service

---

## Expected Build Output

```
==> Building with nixpacks
==> Installing Python 3.11.9
==> Installing dependencies from requirements.txt
==> Build complete
==> Starting application
INFO:     Started server process
INFO:     Waiting for application startup
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Post-Deployment URLs

After successful deployment:

- **API Base**: `https://your-app-name.railway.app`
- **API Docs**: `https://your-app-name.railway.app/docs`
- **Health Check**: `https://your-app-name.railway.app/health/live`
- **Metrics**: `https://your-app-name.railway.app/metrics`

---

## Testing the Deployment

### 1. Health Check
```bash
curl https://your-app.railway.app/health/live
```

### 2. Generate Test Token
```bash
# Copy from Railway logs or run locally
python -c "from app.core.auth import create_token_for_user; print(create_token_for_user('test','prod',['zkpa:admin']))"
```

### 3. Test API Endpoint
```bash
curl -X GET https://your-app.railway.app/api/v1/attestations \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Troubleshooting

### Build Fails
- Check Railway logs for specific error
- Verify `requirements.txt` is valid
- Ensure Python 3.11 is specified in `runtime.txt`

### App Crashes on Startup
- Check DATABASE_URL is set
- Verify JWT_SECRET and ENCRYPTION_KEY are set
- Review Railway logs

### Health Check Fails
- Use `/health/live` instead of `/health` (doesn't require DB)
- Check if app is still starting up
- Verify PORT is not hardcoded

---

## Railway Dashboard Quick Actions

```
View Logs:     Project → Deployments → View Logs
Variables:     Project → Variables → Add Variable
Metrics:       Project → Metrics
Database:      Project → PostgreSQL → Connect
Redeploy:      Project → Deployments → Redeploy
```

---

## Cost Estimate

**Hobby Plan** ($5/month):
- ✅ Web service (512MB RAM)
- ✅ PostgreSQL database (256MB)
- ✅ 100GB network egress
- ✅ SSL/HTTPS included

**Pro Plan** ($20/month):
- ✅ More resources (8GB RAM)
- ✅ Priority support
- ✅ Multiple environments

---

## Security Notes

⚠️ **Before going live:**

1. ✅ JWT_SECRET and ENCRYPTION_KEY must be unique and random
2. ✅ DEBUG must be set to `false`
3. ✅ CORS_ORIGINS should be restricted to your domains
4. ✅ Review all environment variables
5. ✅ Set up Sentry for error monitoring
6. ✅ Enable rate limiting

---

## Next Steps After Deployment

1. ✅ Test all API endpoints
2. ✅ Set up custom domain (optional)
3. ✅ Configure Sentry for monitoring
4. ✅ Fund Algorand account for blockchain features
5. ✅ Update frontend with new API URL
6. ✅ Add deployment URL to Devpost

---

## Support

- 📚 Full Guide: [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)
- 🐛 Issues: [GitHub Issues](https://github.com/Compliledger/Zkp_Assestation_gemini3/issues)
- 💬 Railway Support: https://discord.gg/railway

---

**Ready to deploy!** 🚀 Follow the steps above or see [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for detailed instructions.
