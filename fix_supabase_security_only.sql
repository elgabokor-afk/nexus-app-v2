-- ============================================
-- FIX SUPABASE SECURITY ISSUES - Solo Seguridad
-- ============================================
-- Resuelve SOLO los problemas de seguridad (RLS)
-- Sin tocar vistas del sistema
-- ============================================

-- ============================================
-- PARTE 1: Habilitar RLS en todas las tablas
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
    ELSE
        RAISE NOTICE 'ℹ️ paper_citations no existe, saltando...';
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
    ELSE
        RAISE NOTICE 'ℹ️ paper_clusters no existe, saltando...';
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
    ELSE
        RAISE NOTICE 'ℹ️ nexus_data_units no existe, saltando...';
    END IF;
END $$;

-- ============================================
-- PARTE 2: Limpiar tablas fantasma
-- ============================================
DROP VIEW IF EXISTS public.paper_stats CASCADE;
DROP TABLE IF EXISTS public.paper_players CASCADE;
DROP TABLE IF EXISTS public.paper_attempts CASCADE;

-- Mensaje de confirmación
DO $$ 
BEGIN
    RAISE NOTICE '✅ Tablas fantasma eliminadas';
END $$;

-- ============================================
-- PARTE 3: Optimizar función match_papers (si existe)
-- ============================================
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_proc 
        WHERE proname = 'match_papers' 
        AND pronamespace = 'public'::regnamespace
    ) THEN
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
-- VERIFICACIÓN FINAL
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
    policyname,
    cmd
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('paper_citations', 'paper_clusters', 'nexus_data_units')
ORDER BY tablename, policyname;

-- Contar políticas por tabla
SELECT 
    '📊 POLICY COUNT' as category,
    tablename,
    COUNT(*) as num_policies
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('paper_citations', 'paper_clusters', 'nexus_data_units')
GROUP BY tablename
ORDER BY tablename;

-- ============================================
-- RESULTADO ESPERADO:
-- ============================================
/*
✅ RLS habilitado en paper_citations (2 políticas)
✅ RLS habilitado en paper_clusters (2 políticas)
✅ RLS habilitado en nexus_data_units (1 política)
✅ Tablas fantasma eliminadas
✅ Función match_papers optimizada (si existe)

DESPUÉS DE EJECUTAR:
1. Ve a Security Advisor
2. Click en "Refresh"
3. Los errores críticos deberían desaparecer
*/
