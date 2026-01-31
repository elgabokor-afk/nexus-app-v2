-- ============================================================================
-- COSMOS AI - ÍNDICES SEGUROS (Versión Simplificada)
-- Esta versión solo crea índices para columnas que definitivamente existen
-- ============================================================================

-- ============================================================================
-- PARTE 1: ÍNDICES BÁSICOS PARA PAPER_POSITIONS
-- ============================================================================

-- Índice para búsquedas por símbolo
CREATE INDEX IF NOT EXISTS idx_paper_positions_symbol 
ON paper_positions(symbol);

-- Índice para búsquedas por status
CREATE INDEX IF NOT EXISTS idx_paper_positions_status 
ON paper_positions(status);

-- Índice compuesto símbolo + status
CREATE INDEX IF NOT EXISTS idx_paper_positions_symbol_status 
ON paper_positions(symbol, status);

-- ============================================================================
-- PARTE 2: ÍNDICES BÁSICOS PARA SIGNALS
-- ============================================================================

-- Índice compuesto para consultas de señales por símbolo y fecha
CREATE INDEX IF NOT EXISTS idx_signals_symbol_created 
ON signals(symbol, created_at DESC);

-- Índice para señales por dirección (LONG/SHORT)
CREATE INDEX IF NOT EXISTS idx_signals_direction 
ON signals(direction, created_at DESC);

-- Índice para búsquedas por status
CREATE INDEX IF NOT EXISTS idx_signals_status 
ON signals(status);

-- Índice para ordenar por fecha
CREATE INDEX IF NOT EXISTS idx_signals_created_at 
ON signals(created_at DESC);

-- ============================================================================
-- PARTE 3: ÍNDICES PARA ERROR_LOGS
-- ============================================================================

-- Índice para búsquedas por timestamp (logs recientes)
CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp 
ON error_logs(created_at DESC);

-- ============================================================================
-- PARTE 4: ÍNDICES PARA PROFILES
-- ============================================================================

-- Índice para búsquedas por id (si la tabla existe)
-- CREATE INDEX IF NOT EXISTS idx_profiles_id ON profiles(id);

-- ============================================================================
-- PARTE 5: ANALIZAR TABLAS
-- ============================================================================

ANALYZE paper_positions;
ANALYZE signals;
ANALYZE error_logs;

-- ============================================================================
-- PARTE 6: VERIFICACIÓN
-- ============================================================================

-- Ver índices creados
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- Contar índices
SELECT COUNT(*) as total_indexes_created
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND indexname LIKE 'idx_%';

-- ============================================================================
-- NOTAS
-- ============================================================================

/*
Esta versión SEGURA solo crea índices para columnas básicas que existen en todas
las versiones del esquema:

PAPER_POSITIONS:
- symbol (TEXT)
- status (TEXT)

SIGNALS:
- symbol (TEXT)
- direction (TEXT)
- status (TEXT)
- created_at (TIMESTAMPTZ)

ERROR_LOGS:
- created_at (TIMESTAMPTZ)

IMPACTO ESPERADO:
- Consultas básicas: 5-10x más rápidas
- Sin riesgo de errores por columnas faltantes

PRÓXIMO PASO:
Si necesitas índices adicionales, primero ejecuta:
database_check_schema.sql

Luego añade columnas faltantes con:
add_missing_columns.sql
*/
