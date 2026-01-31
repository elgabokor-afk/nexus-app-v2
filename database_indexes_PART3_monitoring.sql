-- ============================================================================
-- PARTE 3: ÍNDICES PARA MONITORING Y SISTEMA AUXILIAR
-- Ejecutar al final
-- ============================================================================

-- AI_MODEL_REGISTRY
CREATE INDEX IF NOT EXISTS idx_ai_model_registry_active 
ON ai_model_registry(active, updated_at DESC) 
WHERE active = true;

CREATE INDEX IF NOT EXISTS idx_ai_model_registry_version 
ON ai_model_registry(version_tag);

-- ERROR_LOGS
CREATE INDEX IF NOT EXISTS idx_error_logs_service_level 
ON error_logs(service, error_level, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp 
ON error_logs(created_at DESC);

-- PROFILES (VIP system)
CREATE INDEX IF NOT EXISTS idx_profiles_subscription 
ON profiles(subscription_level) 
WHERE subscription_level = 'vip';

-- ORACLE_INSIGHTS
CREATE INDEX IF NOT EXISTS idx_oracle_insights_symbol_timeframe 
ON oracle_insights(symbol, timeframe, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_oracle_insights_timestamp 
ON oracle_insights(timestamp DESC);

-- AI_ASSET_RANKINGS
CREATE INDEX IF NOT EXISTS idx_ai_asset_rankings_score 
ON ai_asset_rankings(score DESC, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_asset_rankings_symbol 
ON ai_asset_rankings(symbol);

-- VIP_SIGNAL_DETAILS
CREATE INDEX IF NOT EXISTS idx_vip_signal_details_signal_id 
ON vip_signal_details(signal_id);

-- Analizar todas las tablas
ANALYZE ai_model_registry;
ANALYZE error_logs;
ANALYZE profiles;
ANALYZE oracle_insights;
ANALYZE ai_asset_rankings;
ANALYZE vip_signal_details;

-- VACUUM para optimizar almacenamiento
VACUUM ANALYZE paper_positions;
VACUUM ANALYZE signals;
VACUUM ANALYZE academic_papers;
VACUUM ANALYZE academic_chunks;

-- Reporte final de todos los índices
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public' 
  AND indexname LIKE 'idx_%'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Contar total de índices creados
SELECT COUNT(*) as total_indexes_created
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND indexname LIKE 'idx_%';
