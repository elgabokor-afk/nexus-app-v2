-- ============================================
-- CREAR ÍNDICES RECOMENDADOS POR SUPABASE
-- ============================================
-- Basado en Performance Advisor de Supabase
-- Estos índices mejorarán significativamente el performance
-- ============================================

-- ============================================
-- ÍNDICES PARA paper_positions
-- ============================================

-- Índice 1: closed_at (para queries de posiciones cerradas)
CREATE INDEX IF NOT EXISTS idx_paper_positions_closed_at 
ON public.paper_positions USING btree (closed_at);

-- Índice 2: signal_id (para relacionar posiciones con señales)
CREATE INDEX IF NOT EXISTS idx_paper_positions_signal_id 
ON public.paper_positions USING btree (signal_id);

-- Índice 3: opened_at (para queries de posiciones abiertas)
CREATE INDEX IF NOT EXISTS idx_paper_positions_opened_at 
ON public.paper_positions USING btree (opened_at);

-- Índice 4: status (para filtrar por estado)
CREATE INDEX IF NOT EXISTS idx_paper_positions_status 
ON public.paper_positions USING btree (status);

-- Índice 5: Compuesto status + opened_at (para queries combinadas)
CREATE INDEX IF NOT EXISTS idx_paper_positions_status_opened_at 
ON public.paper_positions USING btree (status, opened_at DESC);

-- Índice 6: Compuesto status + closed_at (para queries combinadas)
CREATE INDEX IF NOT EXISTS idx_paper_positions_status_closed_at 
ON public.paper_positions USING btree (status, closed_at DESC);

-- ============================================
-- ÍNDICES PARA market_signals
-- ============================================

-- Índice 7: timestamp (para queries por fecha)
CREATE INDEX IF NOT EXISTS idx_market_signals_timestamp 
ON public.market_signals USING btree (timestamp DESC);

-- Índice 8: symbol (para queries por símbolo)
CREATE INDEX IF NOT EXISTS idx_market_signals_symbol 
ON public.market_signals USING btree (symbol);

-- Índice 9: Compuesto symbol + timestamp (para queries combinadas)
CREATE INDEX IF NOT EXISTS idx_market_signals_symbol_timestamp 
ON public.market_signals USING btree (symbol, timestamp DESC);

-- ============================================
-- ÍNDICES PARA signals (tabla principal)
-- ============================================

-- Índice 10: created_at (para queries por fecha)
CREATE INDEX IF NOT EXISTS idx_signals_created_at 
ON public.signals USING btree (created_at DESC);

-- Índice 11: symbol (para queries por símbolo)
CREATE INDEX IF NOT EXISTS idx_signals_symbol 
ON public.signals USING btree (symbol);

-- Índice 12: ai_confidence (para filtrar por confianza)
CREATE INDEX IF NOT EXISTS idx_signals_confidence 
ON public.signals USING btree (ai_confidence DESC);

-- Índice 13: Compuesto symbol + created_at
CREATE INDEX IF NOT EXISTS idx_signals_symbol_created_at 
ON public.signals USING btree (symbol, created_at DESC);

-- ============================================
-- ÍNDICES PARA analytics_signals (OPCIONAL - solo si existe la tabla)
-- ============================================

-- Índice 14: signal_id (para relacionar con market_signals)
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'analytics_signals') THEN
        CREATE INDEX IF NOT EXISTS idx_analytics_signals_signal_id 
        ON public.analytics_signals USING btree (signal_id);
    END IF;
END $$;

-- ============================================
-- ÍNDICES PARA bot_wallet
-- ============================================

-- Índice 15: last_updated (para queries de historial)
CREATE INDEX IF NOT EXISTS idx_bot_wallet_updated_at 
ON public.bot_wallet USING btree (last_updated DESC);

-- ============================================
-- ÍNDICES PARA error_logs
-- ============================================

-- Índice 16: created_at (para queries de logs recientes)
CREATE INDEX IF NOT EXISTS idx_error_logs_created_at 
ON public.error_logs USING btree (created_at DESC);

-- Índice 17: severity (para filtrar por severidad)
CREATE INDEX IF NOT EXISTS idx_error_logs_severity 
ON public.error_logs USING btree (severity);

-- ============================================
-- VERIFICACIÓN
-- ============================================

-- Ver todos los índices creados
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
    AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- Contar índices por tabla
SELECT 
    tablename,
    COUNT(*) as num_indices,
    CASE 
        WHEN COUNT(*) >= 3 THEN '✅ Bien optimizada'
        WHEN COUNT(*) >= 1 THEN '⚠️ Parcialmente optimizada'
        ELSE '❌ Sin índices'
    END as estado
FROM pg_indexes
WHERE schemaname = 'public'
    AND indexname LIKE 'idx_%'
GROUP BY tablename
ORDER BY COUNT(*) DESC;

-- ============================================
-- RESULTADO ESPERADO:
-- ============================================
/*
✅ 17 índices creados exitosamente

TABLAS OPTIMIZADAS:
- paper_positions: 6 índices
- market_signals: 3 índices
- signals: 4 índices
- analytics_signals: 1 índice
- bot_wallet: 1 índice
- error_logs: 2 índices

IMPACTO ESPERADO:
- Queries 5-10x más rápidos
- Mejor performance en dashboard
- Menos carga en la base de datos
- Mejor experiencia de usuario

DESPUÉS DE EJECUTAR:
1. Ve a Performance Advisor en Supabase
2. Click en "Refresh"
3. Las recomendaciones deberían desaparecer
4. Verifica que los queries son más rápidos
*/
