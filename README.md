# NEXUS AI - Institutional SaaS Trading Platform

> **AI-Powered Crypto Trading Signals** | Multi-Agent Architecture | Academic-Backed Analysis

[![Railway Deploy](https://img.shields.io/badge/Railway-Deploy-blueviolet)](https://railway.app)
[![Next.js](https://img.shields.io/badge/Next.js-16-black)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.9-blue)](https://python.org)
[![Supabase](https://img.shields.io/badge/Supabase-Postgres-green)](https://supabase.com)

## 🚀 Overview

NEXUS AI is an institutional-grade algorithmic trading platform that combines:
- **Multi-Agent AI System** - Cosmos Worker, AI Oracle, Macro Feed, Nexus Executor
- **Academic Knowledge Base** - 100+ research papers from MIT, Stanford, Oxford
- **Real-Time Analysis** - WebSocket-powered live market scanning
- **Risk Management** - Smart Circuit Breakers and Position Sizing

**Live:** [nexuscryptosignals.com](https://nexuscryptosignals.com)

---

## 📐 Architecture

```
┌──────────────┐      ┌─────────────┐      ┌──────────────┐
│   Frontend   │◄────►│   Backend   │◄────►│   Database   │
│  (Next.js)   │      │  (Python)   │      │  (Supabase)  │
└──────────────┘      └─────────────┘      └──────────────┘
       │                     │                     │
       │                     │                     │
    WebSockets         AI Workers           Redis Cache
       │                     │                     │
       ▼                     ▼                     ▼
  Real-time UI      Signal Generation       Fast Lookup
```

### Services

**Frontend** (`nexus-app-v2`)
- Next.js 16 with Server-Side Rendering
- Real-time WebSocket dashboard
- Pusher integration for live updates
- Responsive UI with dark mode

**Backend** (`diplomatic-strength`)
- FastAPI + Uvicorn
- Multi-worker architecture:
  - **Cosmos Worker** - Signal generation
  - **AI Oracle** - ML predictions
  - **Macro Feed** - Market sentiment
  - **Nexus Executor** - Trade execution
- Redis for caching
- Academic RAG engine

**Database**
- Supabase (PostgreSQL 15)
- 20+ optimized tables
- Vector embeddings for AI
- Real-time subscriptions

---

## 🛠 Tech Stack

### Frontend
- **Framework:** Next.js 16 (React 19)
- **Language:** TypeScript
- **Styling:** CSS Modules
- **State:** React Hooks
- **Real-time:** Pusher Channels

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.9
- **ML:** XGBoost, scikit-learn
- **AI:** OpenAI GPT-4
- **Exchange:** Binance Futures API

### Infrastructure
- **Deployment:** Railway
- **Database:** Supabase
- **Cache:** Redis
- **CDN:** Railway Edge Network

---

## 📦 Installation

### Prerequisites
- Node.js 20+
- Python 3.9+
- Railway account
- Supabase project

### Local Development

1. **Clone repository**
```bash
git clone https://github.com/elgabokor-afk/nexus-app-v2.git
cd nexus-app-v2
```

2. **Install frontend dependencies**
```bash
npm install
```

3. **Install backend dependencies**
```bash
cd data-engine
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.local.example .env.local
# Edit .env.local with your credentials
```

5. **Run development servers**
```bash
# Terminal 1 - Frontend
npm run dev

# Terminal 2 - Backend
cd data-engine
python nexus_api.py
```

---

## 🚂 Railway Deployment

See [`PRODUCTION_GUIDE.md`](./PRODUCTION_GUIDE.md) for complete deployment instructions.

### Quick Deploy

1. Connect GitHub to Railway
2. Create new project
3. Add services:
   - Frontend: `docker/Dockerfile.frontend`
   - Backend: `docker/Dockerfile.backend`
4. Configure environment variables
5. Deploy

### Environment Variables

**Required for backend:**
- `NEXT_PUBLIC_SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY`
- `REDIS_URL`
- Pusher credentials

**Required for frontend:**
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_URL`
- Pusher public credentials

---

## 📚 Documentation

- [**Production Guide**](./PRODUCTION_GUIDE.md) - Railway deployment
- [**Coding Standards**](./CODING_STANDARDS.md) - Python best practices
- [**Implementation Plan**](./brain/implementation_plan.md) - Architecture decisions

---

## 🧪 Testing

```bash
# Frontend tests
npm test

# Backend config verification
python verify_config.py

# API health check
curl https://diplomatic-strength-production.up.railway.app/health
```

---

## 🎯 Features

- ✅ **AI Signal Generation** - Multi-model ensemble predictions
- ✅ **Academic Research** - RAG engine with 100+ papers
- ✅ **Real-Time Dashboard** - WebSocket live updates
- ✅ **Risk Management** - Circuit breakers, position sizing
- ✅ **Multi-Exchange** - Binance, DEX scanners
- ✅ **Whale Monitoring** - On-chain transaction tracking
- ✅ **Paper Trading** - Backtesting and simulation
- ✅ **Telegram Alerts** - Instant notifications

---

## 🔐 Security

- No secrets in code (environment variables only)
- Service role key for backend only
- Input validation and sanitization
- Rate limiting on APIs
- Non-root Docker containers
- HTTPS only in production

---

## 📊 Performance

- **Signal Latency:** <500ms
- **API Response:** <100ms (p95)
- **WebSocket:** Real-time (<50ms)
- **Database:** Connection pooling enabled
- **Cache Hit Rate:** >85% (Redis)

---

## 🤝 Contributing

This is a private institutional project. Contact repository owner for access.

---

## 📄 License

Proprietary - All Rights Reserved

---

## 👥 Team

**Developer:** elgabokor-afk  
**Platform:** Railway  
**Status:** Production (Live)

---

## 🔗 Links

- **Live App:** https://nexuscryptosignals.com
- **Backend API:** https://diplomatic-strength-production.up.railway.app
- **Supabase:** Private instance
- **Support:** Via Repository Issues

---

**Built with ❤️ for institutional-grade algorithmic trading**
