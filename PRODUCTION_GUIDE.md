# NEXUS AI - Production Deployment Guide

## Quick Start

### Prerequisites
- Railway account with project created
- GitHub repository connected to Railway
- Supabase project configured
- Environment variables ready

### Services Overview

**Backend (`diplomatic-strength`)**
- Python/FastAPI AI engine
- Workers: Cosmos AI, Oracle, Executor, Macro Feed
- Port: 8080 (configurable via $PORT)

**Frontend (`nexus-app-v2`)**
- Next.js 16 application
- Server-side rendering enabled
- Port: Dynamically assigned by Railway

**Database**
- Supabase (PostgreSQL)
- Redis for caching

---

## Environment Variables

### Backend Service

```env
# Core
PORT=8080
PYTHONUNBUFFERED=1

# Database
NEXT_PUBLIC_SUPABASE_URL=https://uxjjqrctxfajzicruvxc.supabase.co
SUPABASE_SERVICE_ROLE_KEY=[your-service-role-key]

# Real-time
REDIS_URL=${{Redis.REDIS_URL}}
PUSHER_APP_ID=2107673
PUSHER_SECRET=[your-secret]
NEXT_PUBLIC_PUSHER_KEY=dda05a0dc630ab53ec2e
NEXT_PUBLIC_PUSHER_CLUSTER=mt1

# AI Services
OPENAI_API_KEY=[your-api-key]

# Trading (Production)
BINANCE_API_KEY=[your-api-key]
BINANCE_SECRET=[your-secret]
TRADING_MODE=LIVE

# Market Data
CMC_PRO_API_KEY=[your-api-key]
HELIUS_API_KEY=[your-api-key]
```

### Frontend Service

```env
NEXT_PUBLIC_SUPABASE_URL=https://uxjjqrctxfajzicruvxc.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[your-anon-key]
NEXT_PUBLIC_PUSHER_KEY=dda05a0dc630ab53ec2e
NEXT_PUBLIC_PUSHER_CLUSTER=mt1
NEXT_PUBLIC_API_URL=https://diplomatic-strength-production.up.railway.app
```

---

## Deployment Steps

### 1. Connect Repository to Railway

1. Go to Railway dashboard
2. Create new project (if not exists)
3. Add services from GitHub repo
4. Configure branch: `main`

### 2. Configure Backend Service

1. Service name: `diplomatic-strength`
2. Dockerfile path: `docker/Dockerfile.backend`
3. Add all backend environment variables
4. Deploy

### 3. Configure Frontend Service

1. Service name: `nexus-app-v2`
2. Dockerfile path: `docker/Dockerfile.frontend`
3. Add all frontend environment variables
4. **Important:** Add build arguments:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_PUSHER_KEY`
   - `NEXT_PUBLIC_PUSHER_CLUSTER`
   - `NEXT_PUBLIC_API_URL`
5. Deploy

### 4. Configure Custom Domain

1. Go to `nexus-app-v2` → Settings → Networking
2. Add custom domain: `nexuscryptosignals.com`
3. Update DNS records at your domain provider:
   - Type: CNAME
   - Name: @
   - Value: [Railway provides this]

### 5. Verify Deployment

Run verification script locally:
```bash
python verify_config.py
```

Check Railway logs:
- Backend should show "✅ Cosmos Worker started"
- Frontend should show "✓ Ready in [time]"

---

## Monitoring

### Health Checks

**Backend:**
- Endpoint: `https://diplomatic-strength-production.up.railway.app/health`
- Expected: `{"status": "healthy"}`

**Frontend:**
- Endpoint: `https://nexuscryptosignals.com`
- Expected: Dashboard loads

### Logs

View in Railway dashboard:
1. Select service
2. Go to "Deployments"
3. Click latest deployment
4. View "Deploy Logs" or "Runtime Logs"

---

## Troubleshooting

### Backend Not Starting

1. Check environment variables are set
2. Verify `start_services.sh` is executable
3. Check logs for Python errors
4. Run `verify_config.py` to check config

### Frontend 404

1. Verify `NEXT_PUBLIC_API_URL` points to backend
2. Check Next.js build completed successfully
3. Verify domain DNS is configured

### No Signals Generating

1. Check Cosmos Worker logs
2. Verify Supabase connection
3. Check OpenAI API key is valid
4. Verify Redis connection

---

## Best Practices

### Security
- ✅ Never commit secrets to repository
- ✅ Use Railway environment variables
- ✅ Rotate API keys regularly
- ✅ Use service role key for backend only

### Performance
- ✅ Enable Redis caching
- ✅ Use connection pooling
- ✅ Monitor worker intervals
- ✅ Optimize database queries

### Maintenance
- ✅ Monitor Railway logs daily
- ✅ Check signal generation rate
- ✅ Review error rates
- ✅ Update dependencies monthly

---

## Support

For issues or questions:
1. Check Railway logs
2. Run `verify_config.py`
3. Review this guide
4. Check Supabase dashboard for database issues
