-- ============================================
-- VERIFICAR RELACIONES DE BASE DE DATOS (VERSIÓN SEGURA)
-- ============================================
-- Este script verifica qué foreign keys existen
-- sin asumir estructura de tablas
-- ============================================

-- ============================================
-- PARTE 1: Ver todas las tablas que existen
-- ============================================

SELECT '📊 TABLAS EN EL SCHEMA PUBLIC' as seccion;

SELECT 
    table_name as tabla,
    table_type as tipo
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- ============================================
-- PARTE 2: Ver todas las relaciones existentes
-- ============================================

SELECT '🔗 RELACIONES (FOREIGN KEYS) EXISTENTES' as seccion;

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
-- PARTE 3: Contar relaciones por tabla
-- ============================================

SELECT '📈 CONTEO DE RELACIONES POR TABLA' as seccion;

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
-- PARTE 4: Tablas sin ninguna relación
-- ============================================

SELECT '⚠️ TABLAS SIN FOREIGN KEYS' as seccion;

SELECT 
    t.table_name as tabla_aislada,
    CASE 
        WHEN t.table_name LIKE '%academic%' THEN '📚 Sistema RAG (OK si está aislado)'
        WHEN t.table_name LIKE '%nexus%' THEN '🗄️ Almacén de datos (OK si está aislado)'
        WHEN t.table_name LIKE '%paper%' THEN '📊 Trading (debería tener relaciones)'
        WHEN t.table_name LIKE '%signal%' THEN '🎯 Trading (debería tener relaciones)'
        WHEN t.table_name LIKE '%bot%' THEN '🤖 Bot (debería tener relaciones)'
        WHEN t.table_name LIKE '%profile%' THEN '👤 Usuarios (debería tener relaciones)'
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
-- PARTE 5: Columnas que parecen FK pero no lo son
-- ============================================

SELECT '🔍 COLUMNAS QUE PARECEN FK PERO NO LO SON' as seccion;

SELECT 
    c.table_name as tabla,
    c.column_name as columna,
    c.data_type as tipo,
    CASE 
        WHEN c.column_name = 'user_id' THEN '⚠️ Debería apuntar a profiles o auth.users'
        WHEN c.column_name = 'signal_id' THEN '⚠️ Debería apuntar a signals'
        WHEN c.column_name = 'position_id' THEN '⚠️ Debería apuntar a paper_positions'
        WHEN c.column_name = 'paper_id' THEN '⚠️ Debería apuntar a academic_papers'
        WHEN c.column_name LIKE '%_id' AND c.column_name != 'id' THEN '⚠️ Parece FK'
        ELSE '✅ OK'
    END as sugerencia
FROM information_schema.columns c
WHERE c.table_schema = 'public'
    AND (
        c.column_name LIKE '%_id' 
        OR c.column_name = 'user_id'
    )
    AND c.column_name != 'id'
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
-- PARTE 6: Ver estructura de tablas clave
-- ============================================

SELECT '📋 ESTRUCTURA DE TABLAS CLAVE' as seccion;

-- Ver columnas de signals
SELECT 
    'signals' as tabla,
    column_name as columna,
    data_type as tipo,
    is_nullable as nullable
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name = 'signals'
ORDER BY ordinal_position;

-- Ver columnas de paper_positions
SELECT 
    'paper_positions' as tabla,
    column_name as columna,
    data_type as tipo,
    is_nullable as nullable
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name = 'paper_positions'
ORDER BY ordinal_position;

-- Ver columnas de paper_trades
SELECT 
    'paper_trades' as tabla,
    column_name as columna,
    data_type as tipo,
    is_nullable as nullable
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name = 'paper_trades'
ORDER BY ordinal_position;

-- ============================================
-- PARTE 7: Resumen general
-- ============================================

SELECT '📊 RESUMEN GENERAL' as seccion;

SELECT 
    (SELECT COUNT(*) FROM information_schema.table_constraints 
     WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'public') as total_foreign_keys,
    
    (SELECT COUNT(DISTINCT table_name) FROM information_schema.table_constraints 
     WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'public') as tablas_con_fk,
    
    (SELECT COUNT(*) FROM information_schema.tables 
     WHERE table_schema = 'public' AND table_type = 'BASE TABLE') as total_tablas,
    
    ROUND(
        100.0 * (SELECT COUNT(DISTINCT table_name) FROM information_schema.table_constraints 
                 WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'public')
        / NULLIF((SELECT COUNT(*) FROM information_schema.tables 
                  WHERE table_schema = 'public' AND table_type = 'BASE TABLE'), 0)
    , 2) as porcentaje_tablas_conectadas,
    
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

1. 📊 Todas las tablas que existen
2. 🔗 Todas las relaciones (FK) actuales
3. 📈 Cuántas relaciones tiene cada tabla
4. ⚠️ Qué tablas están aisladas
5. 🔍 Columnas que parecen FK pero no lo son
6. 📋 Estructura de tablas clave (signals, positions, trades)
7. 📊 Resumen general

INTERPRETACIÓN:
- Si ves 0-5 FK → Sistema muy desacoplado (común en AI/trading)
- Si ves 5-15 FK → Balance razonable
- Si ves >15 FK → Sistema bien estructurado

PRÓXIMO PASO:
Basado en los resultados, puedo crear un script para añadir
las relaciones que falten (si es necesario).
*/
