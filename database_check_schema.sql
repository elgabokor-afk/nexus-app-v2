-- ============================================================================
-- DIAGNÓSTICO: Verificar Esquema de Base de Datos
-- Ejecutar PRIMERO antes de crear índices
-- ============================================================================

-- 1. Verificar columnas de la tabla SIGNALS
SELECT 
    'signals' as table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'signals'
ORDER BY ordinal_position;

-- 2. Verificar columnas de la tabla PAPER_POSITIONS
SELECT 
    'paper_positions' as table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'paper_positions'
ORDER BY ordinal_position;

-- 3. Verificar si existen las columnas críticas
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='signals' AND column_name='academic_thesis_id')
        THEN '✅ signals.academic_thesis_id EXISTS'
        ELSE '❌ signals.academic_thesis_id MISSING'
    END as check_1,
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='signals' AND column_name='statistical_p_value')
        THEN '✅ signals.statistical_p_value EXISTS'
        ELSE '❌ signals.statistical_p_value MISSING'
    END as check_2,
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='paper_positions' AND column_name='signal_id')
        THEN '✅ paper_positions.signal_id EXISTS'
        ELSE '❌ paper_positions.signal_id MISSING'
    END as check_3,
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='paper_positions' AND column_name='closed_at')
        THEN '✅ paper_positions.closed_at EXISTS'
        ELSE '❌ paper_positions.closed_at MISSING'
    END as check_4;

-- 4. Verificar tablas académicas
SELECT 
    table_name,
    COUNT(*) as column_count
FROM information_schema.columns 
WHERE table_name IN ('academic_papers', 'academic_chunks', 'academic_alpha')
GROUP BY table_name;

-- 5. Verificar extensión pgvector (necesaria para búsqueda vectorial)
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')
        THEN '✅ pgvector extension INSTALLED'
        ELSE '❌ pgvector extension NOT INSTALLED - Run: CREATE EXTENSION vector;'
    END as vector_check;

-- 6. Listar índices existentes
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public'
  AND tablename IN ('signals', 'paper_positions', 'academic_papers', 'academic_chunks')
ORDER BY tablename, indexname;

-- ============================================================================
-- INTERPRETACIÓN DE RESULTADOS
-- ============================================================================

/*
Si ves ❌ en algún check:
1. La columna no existe en tu esquema actual
2. Necesitas ejecutar una migración para añadirla
3. O ajustar los índices para omitir esa columna

COLUMNAS CRÍTICAS ESPERADAS:
- signals.academic_thesis_id (para validación PhD)
- signals.statistical_p_value (para filtrado estadístico)
- paper_positions.signal_id (para joins)
- paper_positions.closed_at (para queries de posiciones cerradas)

Si faltan, ejecuta primero: add_missing_columns.sql
*/
