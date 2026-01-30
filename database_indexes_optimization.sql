-- ============================================================================
-- COSMOS AI - DATABASE INDEXES OPTIMIZATION
-- Fecha: 31 de Enero, 2026
-- Propósito: Optimizar consultas frecuentes y mejorar performance
-- Ejecutar en: Supabase SQL Editor
-- ============================================================================

-- ============================================================================
-- SECCIÓN 1: ÍNDICES PARA PAPER_POSITIONS
-- ============================================================================

-- Índice para búsquedas por símbolo (usado en fetch_training_data)
CREATE INDEX IF NOT EXISTS idx_paper_positions_symbol 
ON paper_positions(symbol);

-- Índice compuesto para consultas de posiciones cerradas ordenadas por fecha
CREATE INDEX IF NOT EXISTS idx_paper_positions_status_closed 
ON paper_positions(status, closed_at DESC) 
WHERE status = 'CLOSED';

-- Índice para búsquedas por signal_id (usado en joins)
CREATE INDEX IF NOT EXISTS idx_paper_positions_signal_id 
ON paper_positions(signal_id) 
WHERE signal_id IS NOT NULL;

-- Índice para consultas de posiciones abiertas
CREATE INDEX IF NOT EXISTS idx_paper_positions_status_open 
ON paper_positions(status, opened_at DESC) 
WHERE status = 'OPEN';

-- ============================================================================
-- SECCIÓN 2: ÍNDICES PARA SIGNALS
-- ============================================================================

-- Índice compuesto para consultas de señales por símbolo y fecha
CREATE INDEX IF NOT EXISTS idx_signals_symbol_created 
ON signals(symbol, created_at DESC);

-- Índice para señales activas ordenadas por confianza
CREATE INDEX IF NOT EXISTS idx_signals_confidence 
ON signals(ai_confidence DESC) 
WHERE status = 'ACTIVE';

-- Índice para búsquedas por thesis_id (usado en academic validation)
CREATE INDEX IF NOT EXISTS idx_signals_thesis_id 
ON signals(academic_thesis_id) 
WHERE academic_thesis_id IS NOT NULL;

-- Índice para señales por dirección (LONG/SHORT)
CREATE INDEX IF NOT EXISTS idx_signals_direction 
ON signals(direction, created_at DESC);

-- Índice para p-value filtering (academic research)
CREATE INDEX IF NOT EXISTS idx_signals_p_value 
ON signals(statistical_p_value) 
WHERE statistical_p_value IS NOT NULL AND statistical_p_value < 0.05;

-- ============================================================================
-- SECCIÓN 3: ÍNDICES PARA ACADEMIC_PAPERS
-- ============================================================================

-- Índice para búsquedas por universidad
CREATE INDEX IF NOT EXISTS idx_academic_papers_university 
ON academic_papers(university, published_date DESC);

-- Índice para búsquedas por citation count (papers más citados)
CREATE INDEX IF NOT EXISTS idx_academic_papers_citations 
ON academic_papers(citation_count DESC);

-- Índice para búsquedas por topic_tags (array search)
CREATE INDEX IF NOT EXISTS idx_academic_papers_tags 
ON academic_papers USING GIN(topic_tags);

-- ============================================================================
-- SECCIÓN 4: ÍNDICES VECTORIALES PARA ACADEMIC_CHUNKS
-- ============================================================================

-- Índice IVFFlat para búsqueda vectorial (cosine similarity)
-- NOTA: Requiere extensión pgvector
CREATE INDEX IF NOT EXISTS idx_academic_chunks_embedding 
ON academic_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Índice para búsquedas por paper_id
CREATE INDEX IF NOT EXISTS idx_academic_chunks_paper_id 
ON academic_chunks(paper_id);

-- ============================================================================
-- SECCIÓN 5: ÍNDICES PARA AI_MODEL_REGISTRY
-- ============================================================================

-- Índice para búsquedas de modelos activos
CREATE INDEX IF NOT EXISTS idx_ai_model_registry_active 
ON ai_model_registry(active, updated_at DESC) 
WHERE active = true;

-- Índice para búsquedas por version_tag
CREATE INDEX IF NOT EXISTS idx_ai_model_registry_version 
ON ai_model_registry(version_tag);

-- ============================================================================
-- SECCIÓN 6: ÍNDICES PARA ERROR_LOGS
-- ============================================================================

-- Índice para búsquedas por servicio y nivel de error
CREATE INDEX IF NOT EXISTS idx_error_logs_service_level 
ON error_logs(service, error_level, created_at DESC);

-- Índice para búsquedas por timestamp (logs recientes)
CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp 
ON error_logs(created_at DESC);

-- ============================================================================
-- SECCIÓN 7: ÍNDICES PARA PROFILES (VIP SYSTEM)
-- ============================================================================

-- Índice para búsquedas por subscription_level
CREATE INDEX IF NOT EXISTS idx_profiles_subscription 
ON profiles(subscription_level) 
WHERE subscription_level = 'vip';

-- ============================================================================
-- SECCIÓN 8: ÍNDICES PARA ORACLE_INSIGHTS
-- ============================================================================

-- Índice compuesto para búsquedas de insights por símbolo y timeframe
CREATE INDEX IF NOT EXISTS idx_oracle_insights_symbol_timeframe 
ON oracle_insights(symbol, timeframe, timestamp DESC);

-- Índice para búsquedas de insights recientes
CREATE INDEX IF NOT EXISTS idx_oracle_insights_timestamp 
ON oracle_insights(timestamp DESC);

-- ============================================================================
-- SECCIÓN 9: ÍNDICES PARA AI_ASSET_RANKINGS
-- ============================================================================

-- Índice para búsquedas por score (top performers)
CREATE INDEX IF NOT EXISTS idx_ai_asset_rankings_score 
ON ai_asset_rankings(score DESC, updated_at DESC);

-- Índice para búsquedas por símbolo
CREATE INDEX IF NOT EXISTS idx_ai_asset_rankings_symbol 
ON ai_asset_rankings(symbol);

-- ============================================================================
-- SECCIÓN 10: ÍNDICES PARA VIP_SIGNAL_DETAILS
-- ============================================================================

-- Índice para búsquedas por signal_id
CREATE INDEX IF NOT EXISTS idx_vip_signal_details_signal_id 
ON vip_signal_details(signal_id);

-- ============================================================================
-- SECCIÓN 11: ACTUALIZAR ESTADÍSTICAS DEL OPTIMIZADOR
-- ============================================================================

-- Analizar todas las tablas para actualizar estadísticas del query planner
ANALYZE paper_positions;
ANALYZE signals;
ANALYZE academic_papers;
ANALYZE academic_chunks;
ANALYZE ai_model_registry;
ANALYZE error_logs;
ANALYZE profiles;
ANALYZE oracle_insights;
ANALYZE ai_asset_rankings;
ANALYZE vip_signal_details;

-- ============================================================================
-- SECCIÓN 12: VERIFICACIÓN DE ÍNDICES
-- ============================================================================

-- Query para verificar todos los índices creados
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- ============================================================================
-- SECCIÓN 13: ANÁLISIS DE PERFORMANCE
-- ============================================================================

-- Query para verificar el tamaño de los índices
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- ============================================================================
-- SECCIÓN 14: VACUUM Y MANTENIMIENTO
-- ============================================================================

-- Ejecutar VACUUM ANALYZE para optimizar el almacenamiento
VACUUM ANALYZE paper_positions;
VACUUM ANALYZE signals;
VACUUM ANALYZE academic_papers;
VACUUM ANALYZE academic_chunks;

-- ============================================================================
-- NOTAS DE IMPLEMENTACIÓN
-- ============================================================================

/*
IMPACTO ESPERADO:
- Consultas de paper_positions por símbolo: 10x más rápidas
- Búsquedas de señales activas: 5x más rápidas
- Búsqueda vectorial académica: 20x más rápida (con IVFFlat)
- Consultas de logs: 3x más rápidas

MANTENIMIENTO:
- Ejecutar ANALYZE semanalmente
- Ejecutar VACUUM ANALYZE mensualmente
- Monitorear tamaño de índices con la query de la Sección 13

ROLLBACK:
Si algún índice causa problemas, puede eliminarse con:
DROP INDEX IF EXISTS nombre_del_indice;

MONITOREO:
Para ver qué índices se están usando:
SELECT * FROM pg_stat_user_indexes WHERE schemaname = 'public';
*/

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================

COMMIT;
