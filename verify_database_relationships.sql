-- ============================================
-- VERIFICAR RELACIONES DE BASE DE DATOS
-- ============================================
-- Este script verifica qué foreign keys existen
-- y cuáles faltan en tu schema
-- ============================================

-- ============================================
-- PARTE 1: Ver todas las relaciones existentes
-- ============================================

SELECT
    '📊 RELACIONES EXISTENTES' as seccion;

SELECT
    tc.table_name as tabla_origen,
    kcu.column_name as columna,
    ccu.table_name AS tabla_destino,
    ccu.column_name AS columna_destino,
    tc.constraint_name as nombre_constraint
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;

-- ============================================
-- PARTE 2: Contar relaciones por tabla
-- ============================================

SELECT
    '📈 CONTEO DE RELACIONES POR TABLA' as seccion;

SELECT 
    tc.table_name as tabla,
    COUNT(*) as num_foreign_keys,
    CASE 
        WHEN COUNT(*) = 0 THEN '⚠️ Sin relaciones'
        WHEN COUNT(*) < 2 THEN '✅ Pocas relaciones'
        ELSE '✅ Bien conectada'
    END as estado
FROM information_schema.table_constraints AS tc
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
GROUP BY tc.table_name
ORDER BY COUNT(*) DESC;

-- ============================================
-- PARTE 3: Tablas sin ninguna relación
-- ============================================

SELECT
    '⚠️ TABLAS SIN FOREIGN KEYS' as seccion;

SELECT 
    t.table_name as tabla_aislada,
    CASE 
        WHEN t.table_name LIKE '%academic%' THEN '📚 Sistema RAG (OK si está aislado)'
        WHEN t.table_name LIKE '%nexus%' THEN '🗄️ Almacén de datos (OK si está aislado)'
        WHEN t.table_name LIKE '%paper%' THEN '📊 Trading (debería tener relaciones)'
        WHEN t.table_name LIKE '%signal%' THEN '🎯 Trading (debería tener relaciones)'
        WHEN t.table_name LIKE '%bot%' THEN '🤖 Bot (debería tener relaciones)'
        ELSE '❓ Revisar'
    END as tipo
FROM information_schema.tables t
WHERE t.table_schema = 'public'
    AND t.table_type = 'BASE TABLE'
    AND NOT EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints tc
        WHERE tc.table_name = t.table_name
            AND tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
    )
ORDER BY t.table_name;

-- ============================================
-- PARTE 4: Verificar columnas que parecen FK pero no lo son
-- ============================================

SELECT
    '🔍 COLUMNAS QUE PARECEN FK PERO NO LO SON' as seccion;

SELECT 
    c.table_name as tabla,
    c.column_name as columna,
    c.data_type as tipo,
    CASE 
        WHEN c.column_name LIKE '%_id' THEN '⚠️ Parece FK'
        WHEN c.column_name LIKE 'user_id' THEN '⚠️ Debería apuntar a profiles'
        WHEN c.column_name LIKE 'signal_id' THEN '⚠️ Debería apuntar a signals'
        WHEN c.column_name LIKE 'position_id' THEN '⚠️ Debería apuntar a paper_positions'
        ELSE '✅ OK'
    END as sugerencia
FROM information_schema.columns c
WHERE c.table_schema = 'public'
    AND (c.column_name LIKE '%_id' OR c.column_name = 'user_id')
    AND NOT EXISTS (
        SELECT 1 
        FROM information_schema.key_column_usage kcu
        JOIN information_schema.table_constraints tc
            ON kcu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND kcu.table_name = c.table_name
            AND kcu.column_name = c.column_name
            AND kcu.table_schema = 'public'
    )
ORDER BY c.table_name, c.column_name;

-- ============================================
-- PARTE 5: Verificar integridad referencial
-- ============================================

SELECT
    '🔒 VERIFICAR INTEGRIDAD REFERENCIAL' as seccion;

-- Verificar si hay paper_positions sin signal_id válido
SELECT 
    'paper_positions → signals' as relacion,
    COUNT(*) as registros_huerfanos,
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ Todos los registros tienen signal válido'
        ELSE '⚠️ Hay posiciones sin señal válida'
    END as estado
FROM paper_positions pp
WHERE pp.signal_id IS NOT NULL
    AND NOT EXISTS (
        SELECT 1 FROM signals s WHERE s.id = pp.signal_id
    );

-- Verificar si hay paper_trades sin position_id válido
SELECT 
    'paper_trades → paper_positions' as relacion,
    COUNT(*) as registros_huerfanos,
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ Todos los trades tienen posición válida'
        ELSE '⚠️ Hay trades sin posición válida'
    END as estado
FROM paper_trades pt
WHERE pt.position_id IS NOT NULL
    AND NOT EXISTS (
        SELECT 1 FROM paper_positions pp WHERE pp.id = pt.position_id
    );

-- ============================================
-- PARTE 6: Resumen y recomendaciones
-- ============================================

SELECT
    '📋 RESUMEN' as seccion;

SELECT 
    (SELECT COUNT(*) FROM information_schema.table_constraints 
     WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'public') as total_foreign_keys,
    
    (SELECT COUNT(DISTINCT table_name) FROM information_schema.table_constraints 
     WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'public') as tablas_con_fk,
    
    (SELECT COUNT(*) FROM information_schema.tables 
     WHERE table_schema = 'public' AND table_type = 'BASE TABLE') as total_tablas,
    
    CASE 
        WHEN (SELECT COUNT(*) FROM information_schema.table_constraints 
              WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'public') > 10 
        THEN '✅ Bien conectado'
        WHEN (SELECT COUNT(*) FROM information_schema.table_constraints 
              WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'public') > 5 
        THEN '⚠️ Pocas relaciones'
        ELSE '❌ Muy pocas relaciones'
    END as estado_general;

-- ============================================
-- RESULTADO ESPERADO:
-- ============================================
/*
Este script te mostrará:

1. ✅ Todas las relaciones (FK) que existen actualmente
2. 📊 Cuántas relaciones tiene cada tabla
3. ⚠️ Qué tablas están completamente aisladas
4. 🔍 Columnas que parecen FK pero no lo son
5. 🔒 Si hay datos huérfanos (registros sin padre válido)
6. 📋 Resumen general del estado de las relaciones

DESPUÉS DE EJECUTAR:
- Si ves muchas tablas aisladas → Normal para sistemas RAG/AI
- Si ves datos huérfanos → Necesitamos crear las FK
- Si ves pocas relaciones → Puedo crear un script para añadirlas
*/
