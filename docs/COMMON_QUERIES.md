# 📊 NEXUS AI - COMMON QUERIES GUIDE

## Quick Reference for Database Queries

---

## 🎯 DASHBOARD QUERIES

### Get Overall Statistics
```sql
SELECT * FROM mv_dashboard_stats;
```

**Returns**: Active signals, open positions, 24h PnL, etc.

### Get Recent Activity (Last 24h)
```sql
SELECT * FROM v_recent_activity LIMIT 20;
```

---

## 📈 TRADING PERFORMANCE

### Performance by Symbol
```sql
SELECT * FROM v_performance_by_symbol
ORDER BY total_pnl DESC;
```

### User Trading Stats
```sql
SELECT * FROM get_user_trading_stats('user-uuid-here');
```

### Best Performing Trades
```sql
SELECT 
    symbol,
    side,
    entry_price,
    exit_price,
    pnl,
    opened_at,
    closed_at
FROM paper_positions
WHERE status = 'CLOSED'
ORDER BY pnl DESC
LIMIT 10;
```

### Worst Performing Trades
```sql
SELECT 
    symbol,
    side,
    entry_price,
    exit_price,
    pnl,
    opened_at,
    closed_at
FROM paper_positions
WHERE status = 'CLOSED'
ORDER BY pnl ASC
LIMIT 10;
```

### Win Rate by Direction
```sql
SELECT 
    side as direction,
    COUNT(*) as total_trades,
    COUNT(*) FILTER (WHERE pnl > 0) as wins,
    ROUND(COUNT(*) FILTER (WHERE pnl > 0)::numeric / COUNT(*)::numeric * 100, 2) as win_rate,
    ROUND(AVG(pnl), 2) as avg_pnl
FROM paper_positions
WHERE status = 'CLOSED'
GROUP BY side;
```

---

## 🧠 ACADEMIC VALIDATION

### Top Performing Papers
```sql
SELECT * FROM get_top_performing_papers(10);
```

### Validation Success Rate by University
```sql
SELECT * FROM v_academic_validation_stats
ORDER BY win_rate DESC;
```

### Signals with Academic Backing
```sql
SELECT 
    s.symbol,
    s.direction,
    s.ai_confidence,
    s.statistical_p_value,
    ap.authors,
    ap.university,
    COUNT(pp.id) as positions_taken,
    AVG(pp.pnl) FILTER (WHERE pp.status = 'CLOSED') as avg_pnl
FROM signals s
LEFT JOIN academic_papers ap ON s.academic_thesis_id = ap.id
LEFT JOIN paper_positions pp ON s.id = pp.signal_id
WHERE s.academic_thesis_id IS NOT NULL
GROUP BY s.id, ap.authors, ap.university
ORDER BY s.created_at DESC;
```

### Papers with Highest Citation Count
```sql
SELECT 
    authors,
    university,
    citation_count,
    quality_score,
    topic_cluster
FROM academic_papers
WHERE citation_count > 0
ORDER BY citation_count DESC, quality_score DESC
LIMIT 20;
```

---

## 🔍 SEARCH & DISCOVERY

### Search Papers by Keyword
```sql
SELECT 
    id,
    authors,
    university,
    content,
    quality_score,
    citation_count
FROM academic_papers
WHERE content_tsv @@ plainto_tsquery('english', 'momentum trading')
ORDER BY quality_score DESC, citation_count DESC
LIMIT 10;
```

### Papers by University
```sql
SELECT 
    university,
    COUNT(*) as paper_count,
    COUNT(embedding) as with_embeddings,
    AVG(quality_score) as avg_quality,
    SUM(citation_count) as total_citations
FROM academic_papers
GROUP BY university
ORDER BY paper_count DESC;
```

### Papers by Topic Cluster
```sql
SELECT 
    pc.topic_name,
    pc.description,
    COUNT(ap.id) as paper_count,
    AVG(ap.quality_score) as avg_quality
FROM paper_clusters pc
LEFT JOIN academic_papers ap ON ap.topic_cluster = pc.cluster_id
GROUP BY pc.cluster_id, pc.topic_name, pc.description
ORDER BY paper_count DESC;
```

---

## 📊 ACTIVE TRADING

### Current Active Signals
```sql
SELECT * FROM v_active_signals
ORDER BY created_at DESC;
```

### Open Positions
```sql
SELECT 
    symbol,
    side,
    quantity,
    entry_price,
    current_price,
    unrealized_pnl,
    opened_at,
    EXTRACT(EPOCH FROM (NOW() - opened_at))/3600 as hours_open
FROM paper_positions
WHERE status = 'OPEN'
ORDER BY opened_at DESC;
```

### Positions Near Stop Loss
```sql
SELECT 
    symbol,
    side,
    entry_price,
    stop_loss,
    current_price,
    unrealized_pnl,
    CASE 
        WHEN side = 'LONG' THEN ROUND((current_price - stop_loss) / current_price * 100, 2)
        ELSE ROUND((stop_loss - current_price) / current_price * 100, 2)
    END as distance_to_sl_pct
FROM paper_positions
WHERE status = 'OPEN'
    AND (
        (side = 'LONG' AND current_price < entry_price * 1.02)
        OR (side = 'SHORT' AND current_price > entry_price * 0.98)
    )
ORDER BY distance_to_sl_pct ASC;
```

### Positions Near Take Profit
```sql
SELECT 
    symbol,
    side,
    entry_price,
    take_profit,
    current_price,
    unrealized_pnl,
    CASE 
        WHEN side = 'LONG' THEN ROUND((take_profit - current_price) / current_price * 100, 2)
        ELSE ROUND((current_price - take_profit) / current_price * 100, 2)
    END as distance_to_tp_pct
FROM paper_positions
WHERE status = 'OPEN'
    AND (
        (side = 'LONG' AND current_price > entry_price * 1.02)
        OR (side = 'SHORT' AND current_price < entry_price * 0.98)
    )
ORDER BY distance_to_tp_pct ASC;
```

---

## 📅 TIME-BASED ANALYSIS

### Performance by Day of Week
```sql
SELECT 
    TO_CHAR(closed_at, 'Day') as day_of_week,
    COUNT(*) as trades,
    COUNT(*) FILTER (WHERE pnl > 0) as wins,
    ROUND(AVG(pnl), 2) as avg_pnl,
    ROUND(SUM(pnl), 2) as total_pnl
FROM paper_positions
WHERE status = 'CLOSED'
GROUP BY EXTRACT(DOW FROM closed_at), TO_CHAR(closed_at, 'Day')
ORDER BY EXTRACT(DOW FROM closed_at);
```

### Performance by Hour of Day
```sql
SELECT 
    EXTRACT(HOUR FROM closed_at) as hour,
    COUNT(*) as trades,
    COUNT(*) FILTER (WHERE pnl > 0) as wins,
    ROUND(AVG(pnl), 2) as avg_pnl
FROM paper_positions
WHERE status = 'CLOSED'
GROUP BY EXTRACT(HOUR FROM closed_at)
ORDER BY hour;
```

### Monthly Performance
```sql
SELECT 
    TO_CHAR(closed_at, 'YYYY-MM') as month,
    COUNT(*) as trades,
    COUNT(*) FILTER (WHERE pnl > 0) as wins,
    ROUND(COUNT(*) FILTER (WHERE pnl > 0)::numeric / COUNT(*)::numeric * 100, 2) as win_rate,
    ROUND(SUM(pnl), 2) as total_pnl,
    ROUND(AVG(pnl), 2) as avg_pnl
FROM paper_positions
WHERE status = 'CLOSED'
GROUP BY TO_CHAR(closed_at, 'YYYY-MM')
ORDER BY month DESC;
```

---

## 🎯 RISK ANALYSIS

### Largest Open Positions
```sql
SELECT 
    symbol,
    side,
    quantity,
    entry_price,
    quantity * entry_price as position_value,
    unrealized_pnl,
    ROUND(unrealized_pnl / (quantity * entry_price) * 100, 2) as pnl_pct
FROM paper_positions
WHERE status = 'OPEN'
ORDER BY position_value DESC;
```

### Risk Exposure by Symbol
```sql
SELECT 
    symbol,
    COUNT(*) as open_positions,
    SUM(quantity * entry_price) as total_exposure,
    SUM(unrealized_pnl) as total_unrealized_pnl
FROM paper_positions
WHERE status = 'OPEN'
GROUP BY symbol
ORDER BY total_exposure DESC;
```

### Drawdown Analysis
```sql
WITH daily_pnl AS (
    SELECT 
        DATE(closed_at) as trade_date,
        SUM(pnl) as daily_pnl,
        SUM(SUM(pnl)) OVER (ORDER BY DATE(closed_at)) as cumulative_pnl
    FROM paper_positions
    WHERE status = 'CLOSED'
    GROUP BY DATE(closed_at)
),
peak_equity AS (
    SELECT 
        trade_date,
        cumulative_pnl,
        MAX(cumulative_pnl) OVER (ORDER BY trade_date) as peak
    FROM daily_pnl
)
SELECT 
    trade_date,
    cumulative_pnl,
    peak,
    peak - cumulative_pnl as drawdown,
    ROUND((peak - cumulative_pnl) / NULLIF(peak, 0) * 100, 2) as drawdown_pct
FROM peak_equity
WHERE peak > cumulative_pnl
ORDER BY drawdown DESC
LIMIT 10;
```

---

## 🔧 MAINTENANCE QUERIES

### Clean Old Data (90 days)
```sql
SELECT * FROM cleanup_old_data(90);
```

### Refresh Dashboard Stats
```sql
SELECT refresh_materialized_views();
```

### Check Database Size
```sql
SELECT 
    pg_size_pretty(pg_database_size(current_database())) as database_size;
```

### Check Table Sizes
```sql
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Check Index Usage
```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC;
```

### Find Unused Indexes
```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
    AND idx_scan = 0
    AND indexrelname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;
```

---

## 🚀 OPTIMIZATION QUERIES

### Analyze Query Performance
```sql
EXPLAIN ANALYZE
SELECT * FROM v_performance_by_symbol;
```

### Vacuum and Analyze All Tables
```sql
VACUUM ANALYZE;
```

### Reindex All Tables
```sql
REINDEX DATABASE postgres;
```

---

## 📝 NOTES

- Use `EXPLAIN ANALYZE` before any query to check performance
- Materialized views need manual refresh: `SELECT refresh_materialized_views();`
- Clean old data regularly: `SELECT cleanup_old_data(90);`
- Monitor index usage and drop unused indexes
- Run `VACUUM ANALYZE` weekly for optimal performance

---

**Last Updated**: 2024-01-30  
**Version**: 1.0
