# Render Deployment Guide (FREE)

## Quick Deploy (Easiest Method - FREE TIER)

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Complete OptiBot system"
git push origin main
```

### Step 2: Deploy to Render (3 minutes)

**Simplest approach - Render Web Interface:**

1. **Go to**: https://render.com/
2. **Sign up/Login** with GitHub account
3. **New** → **Cron Job**
4. **Connect Repository**: `bin-bard/alpha-content-engine`
5. **Configure**:

   - **Name**: `alpha-content-engine`
   - **Command**: `python main.py`
   - **Schedule**: `0 9 * * *` (daily at 9 AM UTC)
   - **Docker**: Auto-detected from Dockerfile

6. **Environment Variables** (CRITICAL):

   ```
   OPENAI_API_KEY = your-openai-key-here
   ZS_SUBDOMAIN = optisignshelp
   ```

7. **Deploy**: Click "Create Cron Job"

### Step 3: Monitor

- **Job Logs**: Dashboard → alpha-content-engine → Logs
- **Status Check**: Added/Updated/Skipped articles count
- **Schedule**: Runs daily at 9 AM UTC (4 PM Vietnam)
- **Manual Run**: Click "Trigger" for immediate execution

## Alternative: Docker Deployment

Render also supports direct Dockerfile deployment:

1. **New** → **Web Service** (if you want web interface)
2. **Docker**: Will auto-detect Dockerfile
3. **Environment**: Same variables as above
4. **Schedule**: Use Render's cron job feature

## Important Notes

- **FREE TIER**: Available for small workloads
- Job runs once and exits (exit 0)
- **Cost**: FREE for 750 hours/month (sufficient for daily job)
- Logs retained for 30 days
- **Auto-scaling**: Only runs when scheduled
- **GitHub Integration**: Auto-deploys on push
- Repository: `bin-bard/alpha-content-engine` (ready to use)

## Why Render > DigitalOcean for this project:

- **FREE** vs $5/month
- **Simpler setup** (3 steps vs 7 steps)
- **Better logging** (30 days vs 7 days)
- **GitHub auto-deploy** included
