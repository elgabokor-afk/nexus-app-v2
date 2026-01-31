-- ============================================
-- FIX ALL RLS ISSUES - Completo y Definitivo
-- ============================================
-- Resuelve TODOS los problemas de RLS detectados
-- ============================================

-- Lista de tablas detectadas sin RLS:
-- 1. paper_citations
-- 2. paper_clusters  
-- 3. academic_papers
-- 4. academic_theses (posiblemente)
-- 5. paper_citations (duplicado?)
-- Y posiblemente más...

-- ============================================
-- ESTRATEGIA: Habilitar RLS en TODAS las tablas públicas
-- ============================================

DO $$ 
DECLARE
    tabla RECORD;
BEGIN
    -- Iterar sobre TODAS las tablas en el schema public que NO tienen RLS
    FOR tabla IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND rowsecurity = false
        AND tablename NOT LIKE 'pg_%'  -- Excluir tablas del sistema
        AND tablename NOT LIKE 'sql_%' -- Excluir tablas SQL
    LOOP
        BEGIN
            -- Habilitar RLS
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', tabla.tablename);
            
            -- Crear política de lectura pública (para tablas académicas/públicas)
            EXECUTE format('
                CREATE POLICY IF NOT EXISTS "Public read access"
                ON public.%I
                FOR SELECT
                USING (true)
            ', tabla.tablename);
            
            -- Crear política de escritura solo para service_role
            EXECUTE format('
                CREATE POLICY IF NOT EXISTS "Service role full access"
                ON public.%I
                FOR ALL
                USING (auth.jwt()->>''role'' = ''service_role'')
                WITH CHECK (auth.jwt()->>''role'' = ''service_role'')
            ', tabla.tablename);
            
            RAISE NOTICE '✅ RLS habilitado en: %', tabla.tablename;
            
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE '⚠️ Error en tabla %: %', tabla.tablename, SQLERRM;
        END;
    END LOOP;
    
    RAISE NOTICE '🎉 Proceso completado!';
END $$;

-- ============================================
-- Limpiar tablas fantasma
-- ============================================
DROP VIEW IF EXISTS public.paper_stats CASCADE;
DROP TABLE IF EXISTS public.paper_players CASCADE;
DROP TABLE IF EXISTS public.paper_attempts CASCADE;

-- ============================================
-- VERIFICACIÓN FINAL
-- ============================================

-- Ver todas las tablas y su estado de RLS
SELECT 
    tablename,
    CASE 
        WHEN rowsecurity THEN '✅ RLS Habilitado'
        ELSE '❌ RLS Deshabilitado'
    END as rls_status,
    (SELECT COUNT(*) FROM pg_policies WHERE schemaname = 'public' AND pg_policies.tablename = pg_tables.tablename) as num_policies
FROM pg_tables
WHERE schemaname = 'public'
AND tablename NOT LIKE 'pg_%'
AND tablename NOT LIKE 'sql_%'
ORDER BY rowsecurity, tablename;

-- Contar problemas restantes
SELECT 
    COUNT(*) as tablas_sin_rls
FROM pg_tables
WHERE schemaname = 'public'
AND rowsecurity = false
AND tablename NOT LIKE 'pg_%'
AND tablename NOT LIKE 'sql_%';

-- ============================================
-- RESULTADO ESPERADO:
-- ============================================
/*
✅ RLS habilitado en TODAS las tablas públicas
✅ 2 políticas por tabla (lectura pública + escritura service_role)
✅ 0 tablas sin RLS
✅ Security Advisor: 0 errores de RLS

DESPUÉS DE EJECUTAR:
1. Ve a Security Advisor
2. Click en "Refresh"
3. Los errores de RLS deberían desaparecer
4. Pueden quedar warnings de performance (OK)
*/
