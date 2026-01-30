-- ============================================================================
-- PARTE 1: ÍNDICES CRÍTICOS PARA PAPER_POSITIONS Y SIGNALS
-- Ejecutar primero - Son los más importantes para performance
-- ============================================================================

-- PAPER_POSITIONS (tabla más consultada)
CREATE INDEX IF NOT EXISTS idx_paper_positions_symbol 
ON paper_positions(symbol);

CREATE INDEX IF NOT EXISTS idx_paper_positions_status_closed 
ON paper_positions(status, closed_at DESC) 
WHERE status = 'CLOSED';

CREATE INDEX IF NOT EXISTS idx_paper_positions_signal_id 
ON paper_positions(signal_id) 
WHERE signal_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_paper_positions_status_open 
ON paper_positions(status, opened_at DESC) 
WHERE status = 'OPEN';

-- SIGNALS (segunda tabla más importante)
CREATE INDEX IF NOT EXISTS idx_signals_symbol_created 
ON signals(symbol, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_signals_confidence 
ON signals(ai_confidence DESC) 
WHERE status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_signals_direction 
ON signals(direction, created_at DESC);

-- NOTA: Los siguientes índices se omiten si las columnas no existen
-- Si recibes error, comenta las líneas correspondientes

-- Índice para academic_thesis_id (comentar si no existe)
-- CREATE INDEX IF NOT EXISTS idx_signals_thesis_id 
-- ON signals(academic_thesis_id) 
-- WHERE academic_thesis_id IS NOT NULL;

-- Índice para statistical_p_value (comentar si no existe)
-- CREATE INDEX IF NOT EXISTS idx_signals_p_value 
-- ON signals(statistical_p_value) 
-- WHERE statistical_p_value IS NOT NULL AND statistical_p_value < 0.05;

-- Analizar tablas
ANALYZE paper_positions;
ANALYZE signals;

-- Verificar índices creados
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND indexname LIKE 'idx_paper%' OR indexname LIKE 'idx_signals%'
ORDER BY tablename, indexname;
