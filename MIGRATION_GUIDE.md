# 🚀 NEXUS AI - MIGRATION GUIDE TO PRODUCTION

## Complete Guide to Migrate RAG System to nexus-app-v2

---

## 📋 What Will Be Migrated

### Core RAG System (4 files)
- ✅ `data-engine/rag_engine_v2.py` - Advanced RAG engine
- ✅ `data-engine/academic_manager.py` - Paper management
- ✅ `data-engine/embedding_cache.py` - Cost optimization
- ✅ `data-engine/cosmos_validator.py` - Updated integration

### Utility Scripts (3 files)
- ✅ `scripts/audit_academic_database.py` - Database auditor
- ✅ `scripts/generate_all_embeddings.py` - Mass generator
- ✅ `scripts/monitor_database.py` - Progress monitor

### Database Scripts (2 files)
- ✅ `scripts/setup-database.sql` - Initial setup
- ✅ `scripts/database-optimization.sql` - Optimization

### Documentation (6 files)
- ✅ `docs/RAG_SYSTEM.md` - Technical docs
- ✅ `docs/COMMON_QUERIES.md` - Query reference
- ✅ `IMPLEMENTATION_SUMMARY.md` - What was built
- ✅ `NEXT_STEPS.md` - Action items
- ✅ `CHECKLIST.md` - Task tracking
- ✅ `README_RAG.md` - Quick reference

---

## 🎯 Migration Steps

### Step 1: Backup (5 minutes)

```bash
# Navigate to nexus-app-v2
cd C:\Users\NPC2\OneDrive\Escritorio\nexus-app-v2

# Create backup branch
git checkout -b backup-before-rag
git add .
git commit -m "Backup before RAG system migration"
git push origin backup-before-rag

# Return to main
git checkout main
```

### Step 2: Run Migration Script (2 minutes)

```bash
# From the current directory (test project)
MIGRATE_TO_NEXUS_APP_V2.bat
```

This will:
- ✅ Create timestamped backup
- ✅ Copy all RAG files
- ✅ Copy documentation
- ✅ Preserve existing files

### Step 3: Verify Files (2 minutes)

```bash
# Navigate to nexus-app-v2
cd C:\Users\NPC2\OneDrive\Escritorio\nexus-app-v2

# Check RAG files
dir data-engine\rag_engine_v2.py
dir data-engine\academic_manager.py
dir data-engine\embedding_cache.py

# Check scripts
dir scripts\audit_academic_database.py
dir scripts\generate_all_embeddings.py
dir scripts\monitor_database.py

# Check docs
dir docs\RAG_SYSTEM.md
dir docs\COMMON_QUERIES.md
```

### Step 4: Setup Supabase Database (15 minutes)

1. **Login to Supabase**
   - Go to: https://supabase.com/dashboard
   - Select your project

2. **Run Initial Setup**
   - Open **SQL Editor**
   - Copy content from `scripts/setup-database.sql`
   - Paste and click **Run**
   - Wait for "Setup complete!" message

3. **Run Optimization**
   - Copy content from `scripts/database-optimization.sql`
   - Paste and click **Run**
   - Wait for "Optimization complete!" message

4. **Verify Setup**
   ```sql
   -- Check extensions
   SELECT * FROM pg_extension WHERE extname IN ('vector', 'pg_trgm');
   
   -- Check tables
   SELECT * FROM paper_stats;
   
   -- Check functions
   SELECT * FROM get_top_performing_papers(5);
   
   -- Check views
   SELECT * FROM v_performance_by_symbol LIMIT 5;
   ```

### Step 5: Test RAG System (10 minutes)

```bash
# Audit database
python scripts/audit_academic_database.py

# Expected output:
# ================================================================================
#   NEXUS AI - ACADEMIC DATABASE AUDIT
# ================================================================================
# 
# 📚 Total Papers: 1,234
# ✅ With Embeddings: 0
# ❌ Missing Embeddings: 1,234
# 📊 Completion: 0.0%
# 
# 💰 Estimated cost: $24.68 USD
# ⏱️  Estimated time: 2.5 hours
```

```bash
# Test academic manager
cd data-engine
python academic_manager.py

# Expected output:
# Testing Academic Manager...
# Found 0 papers (embeddings not generated yet)
```

### Step 6: Generate Embeddings (OVERNIGHT - 6-12 hours)

```bash
# Test with 10 papers first
python scripts/generate_all_embeddings.py --limit 10

# If successful, generate all
python scripts/generate_all_embeddings.py

# Monitor in another terminal
python scripts/monitor_database.py
```

### Step 7: Commit to Git (5 minutes)

```bash
cd C:\Users\NPC2\OneDrive\Escritorio\nexus-app-v2

# Create feature branch
git checkout -b feature/rag-system

# Add all files
git add data-engine/rag_engine_v2.py
git add data-engine/academic_manager.py
git add data-engine/embedding_cache.py
git add data-engine/cosmos_validator.py
git add scripts/audit_academic_database.py
git add scripts/generate_all_embeddings.py
git add scripts/monitor_database.py
git add scripts/setup-database.sql
git add scripts/database-optimization.sql
git add docs/RAG_SYSTEM.md
git add docs/COMMON_QUERIES.md
git add *.md

# Commit
git commit -m "feat: Add RAG system with 1000+ academic papers validation

- Implement RAG Engine V2 with multi-query search
- Add academic manager for paper management
- Add embedding cache for cost optimization
- Update cosmos validator with RAG integration
- Add database setup and optimization scripts
- Add comprehensive documentation

Features:
- Semantic search with pgvector
- Hybrid search (semantic + full-text)
- Confidence scoring with p-values
- Citation tracking
- Cost optimization (80% reduction)
- Real-time monitoring tools

Database:
- Setup script for initial configuration
- Optimization script for performance
- Useful views and functions
- Materialized views for dashboard
- Triggers for automation

Documentation:
- Complete technical documentation
- Common queries reference
- Implementation summary
- Migration guide
- Checklists and roadmap"

# Push to GitHub
git push origin feature/rag-system
```

### Step 8: Deploy to Production (Automatic)

Once you push to GitHub:

1. **Railway** (Backend)
   - Detects new commit
   - Builds Docker image
   - Deploys automatically
   - Check: https://your-app.railway.app

2. **Vercel** (Frontend)
   - Detects new commit
   - Builds Next.js app
   - Deploys automatically
   - Check: https://your-app.vercel.app

3. **Monitor Deployment**
   ```bash
   # Check Railway logs
   railway logs
   
   # Check Vercel logs
   vercel logs
   ```

### Step 9: Verify Production (10 minutes)

1. **Check Frontend**
   - Visit your Vercel URL
   - Verify dashboard loads
   - Check no console errors

2. **Check Backend**
   - Visit your Railway URL
   - Check health endpoint
   - Verify API responses

3. **Check Database**
   - Login to Supabase
   - Check table counts
   - Verify embeddings progress

4. **Test RAG System**
   ```bash
   # From production server (Railway)
   python scripts/audit_academic_database.py
   ```

---

## 🔍 Verification Checklist

### Files Migrated
- [ ] `data-engine/rag_engine_v2.py`
- [ ] `data-engine/academic_manager.py`
- [ ] `data-engine/embedding_cache.py`
- [ ] `data-engine/cosmos_validator.py` (updated)
- [ ] `scripts/audit_academic_database.py`
- [ ] `scripts/generate_all_embeddings.py`
- [ ] `scripts/monitor_database.py`
- [ ] `scripts/setup-database.sql`
- [ ] `scripts/database-optimization.sql`
- [ ] `docs/RAG_SYSTEM.md`
- [ ] `docs/COMMON_QUERIES.md`
- [ ] All markdown documentation

### Database Setup
- [ ] Extensions installed (vector, pg_trgm)
- [ ] Tables created (academic_papers, paper_clusters, etc.)
- [ ] Indexes created
- [ ] Functions created (match_papers, hybrid_search, etc.)
- [ ] Views created (v_performance_by_symbol, etc.)
- [ ] Triggers created
- [ ] Permissions granted

### Testing
- [ ] Audit script runs successfully
- [ ] Academic manager imports correctly
- [ ] RAG engine imports correctly
- [ ] Embedding cache works
- [ ] Database queries return results

### Git & Deploy
- [ ] Backup branch created
- [ ] Feature branch created
- [ ] All files committed
- [ ] Pushed to GitHub
- [ ] Railway deployed successfully
- [ ] Vercel deployed successfully
- [ ] No deployment errors

### Production
- [ ] Frontend accessible
- [ ] Backend accessible
- [ ] Database accessible
- [ ] RAG system functional
- [ ] Embeddings generating (if started)

---

## 🐛 Troubleshooting

### Issue: Migration script fails
**Solution**: 
```bash
# Check target directory exists
dir C:\Users\NPC2\OneDrive\Escritorio\nexus-app-v2

# Run manually
copy data-engine\rag_engine_v2.py C:\Users\NPC2\OneDrive\Escritorio\nexus-app-v2\data-engine\
```

### Issue: SQL script fails in Supabase
**Solution**:
1. Check if extensions are enabled
2. Run scripts one section at a time
3. Check error messages in SQL Editor
4. Verify you're using Service Role key

### Issue: Import errors in Python
**Solution**:
```bash
# Install dependencies
pip install supabase openai redis python-dotenv

# Verify imports
python -c "from rag_engine_v2 import rag_engine"
```

### Issue: Git push fails
**Solution**:
```bash
# Check remote
git remote -v

# Pull first
git pull origin main

# Then push
git push origin feature/rag-system
```

### Issue: Railway deployment fails
**Solution**:
1. Check Railway logs
2. Verify environment variables
3. Check Dockerfile
4. Verify requirements.txt includes new dependencies

### Issue: Embeddings not generating
**Solution**:
1. Check OpenAI API key in `.env.local`
2. Verify Supabase credentials
3. Check API rate limits
4. Run with `--limit 10` first

---

## 📊 Expected Results

### After Migration
- ✅ All files in nexus-app-v2
- ✅ Git history preserved
- ✅ Backup created
- ✅ No existing files overwritten

### After Database Setup
- ✅ 15+ tables created
- ✅ 20+ indexes created
- ✅ 10+ functions created
- ✅ 5+ views created
- ✅ Triggers active

### After Embedding Generation
- ✅ 1000+ papers with embeddings
- ✅ Search returns results in <200ms
- ✅ Validation system working
- ✅ P-values calculated

### After Deployment
- ✅ Frontend live on Vercel
- ✅ Backend live on Railway
- ✅ Database optimized
- ✅ RAG system operational

---

## 🎯 Next Steps After Migration

1. **Generate Embeddings** (6-12 hours)
   ```bash
   python scripts/generate_all_embeddings.py
   ```

2. **Create Topic Clusters** (Week 2)
   - K-means clustering
   - Generate cluster names
   - Assign papers to clusters

3. **Implement Quality Scoring** (Week 2)
   - Citation-based scoring
   - Usage-based scoring
   - Performance-based scoring

4. **Build Research Dashboard** (Week 2)
   - Paper search UI
   - Cluster visualization
   - Citation tracking

5. **Write Tests** (Week 3)
   - Unit tests (70% coverage)
   - Integration tests
   - E2E tests

See `ROADMAP_8_WEEKS.md` for complete plan.

---

## 💰 Cost Summary

### One-Time
- Embedding generation: $20-25

### Monthly
- OpenAI API: $10-20 (with caching)
- Supabase: $0-25
- Railway: $20-50
- Vercel: $0-20
- **Total: $30-115/month**

---

## 📞 Support

- **Documentation**: See `docs/` folder
- **Queries**: See `docs/COMMON_QUERIES.md`
- **Troubleshooting**: See this guide
- **Roadmap**: See `ROADMAP_8_WEEKS.md`

---

**Status**: Ready for migration  
**Estimated Time**: 1-2 hours (+ overnight for embeddings)  
**Risk Level**: Low (backup created)  
**Rollback**: `git checkout backup-before-rag`

---

**Last Updated**: 2024-01-30  
**Version**: 1.0

