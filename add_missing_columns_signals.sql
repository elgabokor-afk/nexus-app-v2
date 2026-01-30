-- ============================================================================
-- AÑADIR COLUMNAS FALTANTES A LA TABLA SIGNALS
-- Ejecutar ANTES de crear índices avanzados
-- ============================================================================

-- Añadir columnas académicas si no existen
ALTER TABLE signals 
ADD COLUMN IF NOT EXISTS academic_thesis_id BIGINT;

ALTER TABLE signals 
ADD COLUMN IF NOT EXISTS statistical_p_value NUMERIC;

-- Añadir columnas de scoring si no existen
ALTER TABLE signals 
ADD COLUMN IF NOT EXISTS nli_safety_score NUMERIC DEFAULT 1.0;

ALTER TABLE signals 
ADD COLUMN IF NOT EXISTS dex_force_score NUMERIC DEFAULT 0;

ALTER TABLE signals 
ADD COLUMN IF NOT EXISTS whale_sentiment_score NUMERIC DEFAULT 0;

-- Añadir columnas técnicas si no existen
ALTER TABLE signals 
ADD COLUMN IF NOT EXISTS rsi NUMERIC;

ALTER TABLE signals 
ADD COLUMN IF NOT EXISTS atr_value NUMERIC;

ALTER TABLE signals 
ADD COLUMN IF NOT EXISTS volume_ratio NUMERIC;

-- Verificar columnas añadidas
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'signals'
  AND column_name IN (
    'academic_thesis_id',
    'statistical_p_value',
    'nli_safety_score',
    'dex_force_score',
    'whale_sentiment_score',
    'rsi',
    'atr_value',
    'volume_ratio'
  )
ORDER BY column_name;

-- ============================================================================
-- AÑADIR COLUMNAS FALTANTES A LA TABLA PAPER_POSITIONS
-- ============================================================================

-- Añadir columna closed_at si no existe
ALTER TABLE paper_positions 
ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ;

-- Añadir columna signal_id si no existe
ALTER TABLE paper_positions 
ADD COLUMN IF NOT EXISTS signal_id BIGINT;

-- Verificar columnas añadidas
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'paper_positions'
  AND column_name IN ('closed_at', 'signal_id')
ORDER BY column_name;

-- ============================================================================
-- CREAR FOREIGN KEY SI NO EXISTE
-- ============================================================================

-- Eliminar constraint antigua si existe
ALTER TABLE paper_positions 
DROP CONSTRAINT IF EXISTS paper_positions_signal_id_fkey;

-- Crear nueva constraint
ALTER TABLE paper_positions 
ADD CONSTRAINT paper_positions_signal_id_fkey 
FOREIGN KEY (signal_id) REFERENCES signals(id);

-- ============================================================================
-- VERIFICACIÓN FINAL
-- ============================================================================

SELECT 
    '✅ Columnas añadidas correctamente' as status,
    COUNT(*) as total_columns
FROM information_schema.columns 
WHERE table_name IN ('signals', 'paper_positions');

-- ============================================================================
-- PRÓXIMO PASO
-- ============================================================================

/*
Ahora puedes ejecutar los índices avanzados:
1. database_indexes_PART1_positions_signals.sql (descomenta las líneas)
2. database_indexes_PART2_academic.sql
3. database_indexes_PART3_monitoring.sql
*/
