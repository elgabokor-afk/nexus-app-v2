-- ============================================================================
-- NEXUS AI - DATABASE OPTIMIZATION & ORGANIZATION
-- ============================================================================
-- Run this AFTER setup-database.sql to optimize your existing database
-- This script:
-- 1. Analyzes and optimizes existing tables
-- 2. Creates missing indexes
-- 3. Adds useful views and functions
-- 4. Optimizes queries
-- 5. Cleans up duplicates
-- ============================================================================

-- ============================================================================
-- PART 1: ANALYZE CURRENT STATE
-- ============================================================================

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC;

-- ============================================================================
-- PART 2: OPTIMIZE EXISTING TABLES
-- ============================================================================

-- Optimize academic_papers table
VACUUM ANALYZE academic_papers;
REINDEX TABLE academic_papers;

-- Optimize signals table
VACUUM ANALYZE signals;
REINDEX TABLE signals;

-- Optimize paper_positions table
VACUUM ANALYZE paper_positions;
REINDEX TABLE paper_positions;

-- ============================================================================
-- PART 3: ADD MISSING INDEXES (if not exist)
-- ============================================================================

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_signals_symbol_status 
ON signals(symbol, status) WHERE status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_signals_created_confidence 
ON signals(created_at DESC, ai_confidence DESC);

CREATE INDEX IF NOT EXISTS idx_positions_user_status 
ON paper_positions(user_id, status) WHERE status = 'OPEN';

CREATE INDEX IF NOT EXISTS idx_positions_symbol_status 
ON paper_positions(symbol, status);

CREATE INDEX IF NOT EXISTS idx_positions_closed_pnl 
ON paper_positions(closed_at DESC, pnl) WHERE status = 'CLOSED';

-- Partial indexes for performance
CREATE INDEX IF NOT EXISTS idx_signals_active_high_conf 
ON signals(created_at DESC) 
WHERE status = 'ACTIVE' AND ai_confidence > 80;

CREATE INDEX IF NOT EXISTS idx_papers_validated_quality 
ON academic_papers(quality_score DESC) 
WHERE is_validated = true;

-- ============================================================================
-- PART 4: CREATE USEFUL VIEWS
-- ============================================================================

-- Active signals with performance metrics
CREATE OR REPLACE VIEW v_active_signals AS
SELECT 
    s.id,
    s.symbol,
    s.direction,
    s.entry_price,
    s.tp_price,
    s.sl_price,
    s.ai_confidence,
    s.risk_level,
    s.created_at,
    s.academic_thesis_id,
    s.statistical_p_value,
    ap.authors as thesis_authors,
    ap.university as thesis_university,
    COUNT(pp.id) as position_count,
    AVG(pp.pnl) FILTER (WHERE pp.status = 'CLOSED') as avg_pnl,
    SUM(pp.pnl) FILTER (WHERE pp.status = 'CLOSED') as total_pnl
FROM signals s
LEFT JOIN academic_papers ap ON s.academic_thesis_id = ap.id
LEFT JOIN paper_positions pp ON s.id = pp.signal_id
WHERE s.status = 'ACTIVE'
GROUP BY s.id, ap.authors, ap.university;

-- Trading performance by symbol
CREATE OR REPLACE VIEW v_performance_by_symbol AS
SELECT 
    symbol,
    COUNT(*) as total_trades,
    COUNT(*) FILTER (WHERE pnl > 0) as winning_trades,
    COUNT(*) FILTER (WHERE pnl < 0) as losing_trades,
    ROUND(COUNT(*) FILTER (WHERE pnl > 0)::numeric / COUNT(*)::numeric * 100, 2) as win_rate,
    ROUND(AVG(pnl), 2) as avg_pnl,
    ROUND(SUM(pnl), 2) as total_pnl,
    ROUND(MAX(pnl), 2) as best_trade,
    ROUND(MIN(pnl), 2) as worst_trade,
    ROUND(STDDEV(pnl), 2) as pnl_stddev
FROM paper_positions
WHERE status = 'CLOSED'
GROUP BY symbol
ORDER BY total_pnl DESC;

-- Academic validation success rate
CREATE OR REPLACE VIEW v_academic_validation_stats AS
SELECT 
    ap.university,
    COUNT(DISTINCT s.id) as signals_validated,
    COUNT(DISTINCT pp.id) as positions_taken,
    COUNT(DISTINCT pp.id) FILTER (WHERE pp.status = 'CLOSED') as closed_positions,
    COUNT(DISTINCT pp.id) FILTER (WHERE pp.pnl > 0) as winning_positions,
    ROUND(
        COUNT(DISTINCT pp.id) FILTER (WHERE pp.pnl > 0)::numeric / 
        NULLIF(COUNT(DISTINCT pp.id) FILTER (WHERE pp.status = 'CLOSED'), 0)::numeric * 100, 
        2
    ) as win_rate,
    ROUND(AVG(pp.pnl) FILTER (WHERE pp.status = 'CLOSED'), 2) as avg_pnl,
    ROUND(SUM(pp.pnl) FILTER (WHERE pp.status = 'CLOSED'), 2) as total_pnl
FROM academic_papers ap
LEFT JOIN signals s ON ap.id = s.academic_thesis_id
LEFT JOIN paper_positions pp ON s.id = pp.signal_id
WHERE ap.university IS NOT NULL
GROUP BY ap.university
ORDER BY total_pnl DESC NULLS LAST;

-- Recent activity dashboard
CREATE OR REPLACE VIEW v_recent_activity AS
SELECT 
    'signal' as activity_type,
    s.id,
    s.symbol,
    s.direction,
    s.ai_confidence,
    s.created_at as timestamp,
    ap.university as source
FROM signals s
LEFT JOIN academic_papers ap ON s.academic_thesis_id = ap.id
WHERE s.created_at > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT 
    'position_open' as activity_type,
    pp.id,
    pp.symbol,
    pp.side as direction,
    NULL as ai_confidence,
    pp.opened_at as timestamp,
    NULL as source
FROM paper_positions pp
WHERE pp.opened_at > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT 
    'position_close' as activity_type,
    pp.id,
    pp.symbol,
    pp.side as direction,
    NULL as ai_confidence,
    pp.closed_at as timestamp,
    CASE WHEN pp.pnl > 0 THEN 'WIN' ELSE 'LOSS' END as source
FROM paper_positions pp
WHERE pp.closed_at > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- ============================================================================
-- PART 5: CREATE HELPER FUNCTIONS
-- ============================================================================

-- Function to get trading statistics for a user
CREATE OR REPLACE FUNCTION get_user_trading_stats(user_id_param UUID)
RETURNS TABLE (
    total_trades BIGINT,
    open_positions BIGINT,
    closed_positions BIGINT,
    winning_trades BIGINT,
    losing_trades BIGINT,
    win_rate NUMERIC,
    total_pnl NUMERIC,
    avg_pnl NUMERIC,
    best_trade NUMERIC,
    worst_trade NUMERIC,
    total_volume NUMERIC
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_trades,
        COUNT(*) FILTER (WHERE status = 'OPEN')::BIGINT as open_positions,
        COUNT(*) FILTER (WHERE status = 'CLOSED')::BIGINT as closed_positions,
        COUNT(*) FILTER (WHERE pnl > 0)::BIGINT as winning_trades,
        COUNT(*) FILTER (WHERE pnl < 0)::BIGINT as losing_trades,
        ROUND(
            COUNT(*) FILTER (WHERE pnl > 0)::numeric / 
            NULLIF(COUNT(*) FILTER (WHERE status = 'CLOSED'), 0)::numeric * 100, 
            2
        ) as win_rate,
        ROUND(SUM(pnl), 2) as total_pnl,
        ROUND(AVG(pnl) FILTER (WHERE status = 'CLOSED'), 2) as avg_pnl,
        ROUND(MAX(pnl), 2) as best_trade,
        ROUND(MIN(pnl), 2) as worst_trade,
        ROUND(SUM(quantity * entry_price), 2) as total_volume
    FROM paper_positions
    WHERE paper_positions.user_id = user_id_param;
END;
$ LANGUAGE plpgsql STABLE;

-- Function to get top performing papers
CREATE OR REPLACE FUNCTION get_top_performing_papers(limit_count INT DEFAULT 10)
RETURNS TABLE (
    paper_id BIGINT,
    authors TEXT,
    university TEXT,
    signals_count BIGINT,
    avg_confidence NUMERIC,
    win_rate NUMERIC,
    total_pnl NUMERIC
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        ap.id as paper_id,
        ap.authors,
        ap.university,
        COUNT(DISTINCT s.id)::BIGINT as signals_count,
        ROUND(AVG(s.ai_confidence), 2) as avg_confidence,
        ROUND(
            COUNT(pp.id) FILTER (WHERE pp.pnl > 0)::numeric / 
            NULLIF(COUNT(pp.id) FILTER (WHERE pp.status = 'CLOSED'), 0)::numeric * 100, 
            2
        ) as win_rate,
        ROUND(SUM(pp.pnl), 2) as total_pnl
    FROM academic_papers ap
    LEFT JOIN signals s ON ap.id = s.academic_thesis_id
    LEFT JOIN paper_positions pp ON s.id = pp.signal_id
    WHERE pp.status = 'CLOSED'
    GROUP BY ap.id, ap.authors, ap.university
    HAVING COUNT(pp.id) FILTER (WHERE pp.status = 'CLOSED') >= 5
    ORDER BY total_pnl DESC
    LIMIT limit_count;
END;
$ LANGUAGE plpgsql STABLE;

-- Function to clean old data
CREATE OR REPLACE FUNCTION cleanup_old_data(days_to_keep INT DEFAULT 90)
RETURNS TABLE (
    table_name TEXT,
    rows_deleted BIGINT
) AS $
DECLARE
    deleted_count BIGINT;
BEGIN
    -- Clean old error logs
    DELETE FROM error_logs WHERE timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    table_name := 'error_logs';
    rows_deleted := deleted_count;
    RETURN NEXT;
    
    -- Clean old search history
    DELETE FROM paper_search_history WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    table_name := 'paper_search_history';
    rows_deleted := deleted_count;
    RETURN NEXT;
    
    -- Clean old audit logs
    DELETE FROM paper_audit_log WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    table_name := 'paper_audit_log';
    rows_deleted := deleted_count;
    RETURN NEXT;
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 6: CREATE TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Apply to paper_clusters
DROP TRIGGER IF EXISTS update_paper_clusters_updated_at ON paper_clusters;
CREATE TRIGGER update_paper_clusters_updated_at
    BEFORE UPDATE ON paper_clusters
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Auto-increment citation count
CREATE OR REPLACE FUNCTION increment_paper_citation()
RETURNS TRIGGER AS $
BEGIN
    UPDATE academic_papers
    SET citation_count = citation_count + 1
    WHERE id = NEW.paper_id;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS auto_increment_citation ON paper_citations;
CREATE TRIGGER auto_increment_citation
    AFTER INSERT ON paper_citations
    FOR EACH ROW
    EXECUTE FUNCTION increment_paper_citation();

-- ============================================================================
-- PART 7: MATERIALIZED VIEWS FOR PERFORMANCE
-- ============================================================================

-- Materialized view for dashboard (refresh every hour)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_stats AS
SELECT 
    (SELECT COUNT(*) FROM signals WHERE status = 'ACTIVE') as active_signals,
    (SELECT COUNT(*) FROM paper_positions WHERE status = 'OPEN') as open_positions,
    (SELECT COUNT(*) FROM academic_papers WHERE embedding IS NOT NULL) as papers_with_embeddings,
    (SELECT ROUND(AVG(ai_confidence), 2) FROM signals WHERE created_at > NOW() - INTERVAL '24 hours') as avg_confidence_24h,
    (SELECT ROUND(SUM(pnl), 2) FROM paper_positions WHERE closed_at > NOW() - INTERVAL '24 hours') as pnl_24h,
    (SELECT COUNT(*) FROM paper_positions WHERE closed_at > NOW() - INTERVAL '24 hours') as trades_24h,
    NOW() as last_updated;

CREATE UNIQUE INDEX IF NOT EXISTS mv_dashboard_stats_idx ON mv_dashboard_stats(last_updated);

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_stats;
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 8: GRANT PERMISSIONS
-- ============================================================================

-- Grant access to views
GRANT SELECT ON v_active_signals TO anon, authenticated;
GRANT SELECT ON v_performance_by_symbol TO anon, authenticated;
GRANT SELECT ON v_academic_validation_stats TO anon, authenticated;
GRANT SELECT ON v_recent_activity TO authenticated;
GRANT SELECT ON mv_dashboard_stats TO anon, authenticated;

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION get_user_trading_stats(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_top_performing_papers(INT) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION refresh_materialized_views() TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_old_data(INT) TO service_role;

-- ============================================================================
-- PART 9: SCHEDULED JOBS (Run manually or setup with pg_cron)
-- ============================================================================

-- To setup automatic refresh (requires pg_cron extension):
-- SELECT cron.schedule('refresh-dashboard', '0 * * * *', 'SELECT refresh_materialized_views()');
-- SELECT cron.schedule('cleanup-old-data', '0 2 * * 0', 'SELECT cleanup_old_data(90)');

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check optimization results
SELECT 'Indexes' as category, COUNT(*) as count FROM pg_indexes WHERE schemaname = 'public'
UNION ALL
SELECT 'Views', COUNT(*) FROM pg_views WHERE schemaname = 'public'
UNION ALL
SELECT 'Functions', COUNT(*) FROM pg_proc WHERE pronamespace = 'public'::regnamespace
UNION ALL
SELECT 'Triggers', COUNT(*) FROM pg_trigger WHERE tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace = 'public'::regnamespace);

-- Test views
SELECT * FROM v_performance_by_symbol LIMIT 5;
SELECT * FROM v_academic_validation_stats LIMIT 5;
SELECT * FROM mv_dashboard_stats;

-- Test functions
SELECT * FROM get_top_performing_papers(5);

-- ============================================================================
-- OPTIMIZATION COMPLETE
-- ============================================================================
SELECT 'Database optimization complete!' as status,
       NOW() as completed_at;
