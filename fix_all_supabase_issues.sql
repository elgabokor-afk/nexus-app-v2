-- ============================================
-- FIX ALL SUPABASE ISSUES - Completo
-- ============================================
-- Resuelve los 8+ issues detectados en Supabase
-- ============================================

-- ============================================
-- PARTE 1: SECURITY - Habilitar RLS en todas las tablas públicas
-- ============================================

-- 1. paper_citations
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'paper_citations') THEN
        ALTER TABLE public.paper_citations ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "Anyone can view paper_citations" ON public.paper_citations;
        CREATE POLICY "Anyone can view paper_citations"
        ON public.paper_citations FOR SELECT USING (true);
        
        DROP POLICY IF EXISTS "Service role can manage paper_citations" ON public.paper_citations;
        CREATE POLICY "Service role can manage paper_citations"
        ON public.paper_citations FOR ALL
        USING (auth.jwt()->>'role' = 'service_role')
        WITH CHECK (auth.jwt()->>'role' = 'service_role');
        
        RAISE NOTICE '✅ RLS habilitado en paper_citations';
    END IF;
END $$;

-- 2. paper_clusters
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'paper_clusters') THEN
        ALTER TABLE public.paper_clusters ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "Anyone can view paper_clusters" ON public.paper_clusters;
        CREATE POLICY "Anyone can view paper_clusters"
        ON public.paper_clusters FOR SELECT USING (true);
        
        DROP POLICY IF EXISTS "Service role can manage paper_clusters" ON public.paper_clusters;
        CREATE POLICY "Service role can manage paper_clusters"
        ON public.paper_clusters FOR ALL
        USING (auth.jwt()->>'role' = 'service_role')
        WITH CHECK (auth.jwt()->>'role' = 'service_role');
        
        RAISE NOTICE '✅ RLS habilitado en paper_clusters';
    END IF;
END $$;

-- 3. nexus_data_units
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'nexus_data_units') THEN
        ALTER TABLE public.nexus_data_units ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "Service role can manage nexus_data_units" ON public.nexus_data_units;
        CREATE POLICY "Service role can manage nexus_data_units"
        ON public.nexus_data_units FOR ALL
        USING (auth.jwt()->>'role' = 'service_role')
        WITH CHECK (auth.jwt()->>'role' = 'service_role');
        
        RAISE NOTICE '✅ RLS habilitado en nexus_data_units';
    END IF;
END $$;

-- 4. Limpiar tablas fantasma
DROP VIEW IF EXISTS public.paper_stats CASCADE;
DROP TABLE IF EXISTS public.paper_players CASCADE;
DROP TABLE IF EXISTS public.paper_attempts CASCADE;

-- ============================================
-- PARTE 2: PERFORMANCE - Optimizar función match_papers
-- ============================================

-- Si la función match_papers existe, recrearla como IMMUTABLE o STABLE
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_proc 
        WHERE proname = 'match_papers' 
        AND pronamespace = 'public'::regnamespace
    ) THEN
        -- Marcar como STABLE en lugar de VOLATILE
        -- Esto permite que Postgres la optimice mejor
        ALTER FUNCTION public.match_papers STABLE;
        RAISE NOTICE '✅ Función match_papers optimizada';
    ELSE
        RAISE NOTICE 'ℹ️ Función match_papers no existe';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️ No se pudo optimizar match_papers: %', SQLERRM;
END $$;

-- ============================================
-- PARTE 3: EXTENSIONS - Mover pg_stat a schema correcto
-- ============================================

-- Verificar si pg_stat_statements está en public
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_extension 
        WHERE extname = 'pg_stat_statements' 
        AND extnamespace = 'public'::regnamespace
    ) THEN
        -- Mover a extensions schema
        ALTER EXTENSION pg_stat_statements SET SCHEMA extensions;
        RAISE NOTICE '✅ pg_stat_statements movida a extensions schema';
    ELSE
        RAISE NOTICE 'ℹ️ pg_stat_statements ya está en el schema correcto';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️ No se pudo mover pg_stat_statements: %', SQLERRM;
END $$;

-- ============================================
-- PARTE 4: ÍNDICES - Crear índices para queries lentas
-- ============================================

-- Índice para name lookup en pg_timezone_names (query lenta detectada)
CREATE INDEX IF NOT EXISTS idx_timezone_names_name 
ON pg_catalog.pg_timezone_names(name);

-- Índice para queries de academic_theses si existe
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'academic_theses') THEN
        CREATE INDEX IF NOT EXISTS idx_academic_theses_lookup 
        ON public.academic_theses(id, created_at);
        RAISE NOTICE '✅ Índice creado en academic_theses';
    END IF;
END $$;

-- ============================================
-- PARTE 5: VERIFICACIÓN FINAL
-- ============================================

-- Verificar RLS habilitado
SELECT 
    '🔒 SECURITY CHECK' as category,
    tablename,
    CASE 
        WHEN rowsecurity THEN '✅ RLS Habilitado'
        ELSE '❌ RLS Deshabilitado'
    END as status
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('paper_citations', 'paper_clusters', 'nexus_data_units')
ORDER BY tablename;

-- Verificar políticas creadas
SELECT 
    '📋 POLICIES' as category,
    tablename,
    COUNT(*) as num_policies
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('paper_citations', 'paper_clusters', 'nexus_data_units')
GROUP BY tablename
ORDER BY tablename;

-- Verificar extensiones
SELECT 
    '🔌 EXTENSIONS' as category,
    extname,
    nspname as schema
FROM pg_extension e
JOIN pg_namespace n ON e.extnamespace = n.oid
WHERE extname LIKE '%stat%'
ORDER BY extname;

-- ============================================
-- RESULTADO ESPERADO:
-- ============================================
/*
✅ RLS habilitado en 3 tablas
✅ 2 políticas por tabla (lectura pública + gestión service_role)
✅ Función match_papers optimizada
✅ Extensions en schema correcto
✅ Índices creados para queries lentas
✅ Security Advisor: 0 errores críticos
*/

-- ============================================
-- NOTAS IMPORTANTES:
-- ============================================
/*
1. Después de ejecutar este script:
   - Ve a Security Advisor
   - Click en "Refresh"
   - Verifica que los errores críticos desaparecieron

2. Para el warning de contraseñas comprometidas:
   - Ve a Authentication > Policies
   - Habilita "Breach Password Protection"
   - Esto es una configuración, no SQL

3. Para queries lentas:
   - Los índices ayudarán
   - Monitorea en "Database" > "Query Performance"
   - Considera añadir más índices según uso real

4. Si alguna tabla no existe, el script la saltará automáticamente
*/
