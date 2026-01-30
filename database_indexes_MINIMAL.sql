-- ============================================================================
-- COSMOS AI - ÍNDICES MÍNIMOS (100% Seguro)
-- Ejecutar en Supabase SQL Editor
-- ============================================================================

-- PASO 1: Añadir columnas si faltan
ALTER TABLE signals ADD COLUMN IF NOT EXISTS academic_thesis_id BIGINT;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS statistical_p_value NUMERIC;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS rsi NUMERIC;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS atr_value NUMERIC;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS volume_ratio NUMERIC;
ALTER TABLE paper_positions ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ;
ALTER TABLE paper_positions ADD COLUMN IF NOT EXISTS signal_id BIGINT;

-- PASO 2: Crear índices básicos
CREATE INDEX IF NOT EXISTS idx_paper_positions_symbol ON paper_positions(symbol);
CREATE INDEX IF NOT EXISTS idx_paper_positions_status ON paper_positions(status);
CREATE INDEX IF NOT EXISTS idx_signals_symbol_created ON signals(symbol, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_direction ON signals(direction, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs(created_at DESC);

-- PASO 3: Analizar tablas
ANALYZE paper_positions;
ANALYZE signals;
ANALYZE error_logs;

-- PASO 4: Verificar (query simple)
SELECT COUNT(*) as total_indexes 
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND indexname LIKE 'idx_%';
