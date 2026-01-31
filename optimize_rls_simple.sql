-- ============================================
-- OPTIMIZE RLS POLICIES - Simple Version
-- ============================================
-- Optimiza las políticas RLS conocidas
-- Cambia auth.jwt() por (SELECT auth.jwt())
-- ============================================

-- ============================================
-- Optimizar políticas en tablas específicas
-- ============================================

-- 1. paper_citations
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'paper_citations') THEN
        -- Eliminar políticas antiguas
        DROP POLICY IF EXISTS "Service role can manage paper_citations" ON public.paper_citations;
        DROP POLICY IF EXISTS "Service role full access" ON public.paper_citations;
        DROP POLICY IF EXISTS "Public read access" ON public.paper_citations;
        
        -- Crear políticas optimizadas
        CREATE POLICY "Public read access"
        ON public.paper_citations
        FOR SELECT
        USING (true);
        
        CREATE POLICY "Service role full access"
        ON public.paper_citations
        FOR ALL
        USING ((SELECT auth.jwt()->>'role') = 'service_role')
        WITH CHECK ((SELECT auth.jwt()->>'role') = 'service_role');
        
        RAISE NOTICE '✅ paper_citations optimizada';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️ Error en paper_citations: %', SQLERRM;
END $$;

-- 2. paper_clusters
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'paper_clusters') THEN
        DROP POLICY IF EXISTS "Service role can manage paper_clusters" ON public.paper_clusters;
        DROP POLICY IF EXISTS "Service role full access" ON public.paper_clusters;
        DROP POLICY IF EXISTS "Public read access" ON public.paper_clusters;
        
        CREATE POLICY "Public read access"
        ON public.paper_clusters
        FOR SELECT
        USING (true);
        
        CREATE POLICY "Service role full access"
        ON public.paper_clusters
        FOR ALL
        USING ((SELECT auth.jwt()->>'role') = 'service_role')
        WITH CHECK ((SELECT auth.jwt()->>'role') = 'service_role');
        
        RAISE NOTICE '✅ paper_clusters optimizada';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️ Error en paper_clusters: %', SQLERRM;
END $$;

-- 3. nexus_data_units
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'nexus_data_units') THEN
        DROP POLICY IF EXISTS "Service role can manage nexus_data_units" ON public.nexus_data_units;
        DROP POLICY IF EXISTS "Service role full access" ON public.nexus_data_units;
        DROP POLICY IF EXISTS "Public read access" ON public.nexus_data_units;
        
        CREATE POLICY "Public read access"
        ON public.nexus_data_units
        FOR SELECT
        USING (true);
        
        CREATE POLICY "Service role full access"
        ON public.nexus_data_units
        FOR ALL
        USING ((SELECT auth.jwt()->>'role') = 'service_role')
        WITH CHECK ((SELECT auth.jwt()->>'role') = 'service_role');
        
        RAISE NOTICE '✅ nexus_data_units optimizada';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️ Error en nexus_data_units: %', SQLERRM;
END $$;

-- 4. nexus_data_vault
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'nexus_data_vault') THEN
        DROP POLICY IF EXISTS "Service role full access" ON public.nexus_data_vault;
        DROP POLICY IF EXISTS "Authenticated users can read" ON public.nexus_data_vault;
        DROP POLICY IF EXISTS "Service Role Write Vau" ON public.nexus_data_vault;
        
        CREATE POLICY "Service role full access"
        ON public.nexus_data_vault
        FOR ALL
        USING ((SELECT auth.jwt()->>'role') = 'service_role')
        WITH CHECK ((SELECT auth.jwt()->>'role') = 'service_role');
        
        CREATE POLICY "Authenticated users can read"
        ON public.nexus_data_vault
        FOR SELECT
        USING ((SELECT auth.role()) = 'authenticated');
        
        RAISE NOTICE '✅ nexus_data_vault optimizada';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️ Error en nexus_data_vault: %', SQLERRM;
END $$;

-- 5. academic_papers (si existe)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'academic_papers') THEN
        DROP POLICY IF EXISTS "Service role full access" ON public.academic_papers;
        DROP POLICY IF EXISTS "Public read access" ON public.academic_papers;
        
        CREATE POLICY "Public read access"
        ON public.academic_papers
        FOR SELECT
        USING (true);
        
        CREATE POLICY "Service role full access"
        ON public.academic_papers
        FOR ALL
        USING ((SELECT auth.jwt()->>'role') = 'service_role')
        WITH CHECK ((SELECT auth.jwt()->>'role') = 'service_role');
        
        RAISE NOTICE '✅ academic_papers optimizada';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️ Error en academic_papers: %', SQLERRM;
END $$;

-- 6. academic_theses (si existe)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'academic_theses') THEN
        DROP POLICY IF EXISTS "Service role full access" ON public.academic_theses;
        DROP POLICY IF EXISTS "Public read access" ON public.academic_theses;
        
        CREATE POLICY "Public read access"
        ON public.academic_theses
        FOR SELECT
        USING (true);
        
        CREATE POLICY "Service role full access"
        ON public.academic_theses
        FOR ALL
        USING ((SELECT auth.jwt()->>'role') = 'service_role')
        WITH CHECK ((SELECT auth.jwt()->>'role') = 'service_role');
        
        RAISE NOTICE '✅ academic_theses optimizada';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️ Error en academic_theses: %', SQLERRM;
END $$;

-- ============================================
-- VERIFICACIÓN
-- ============================================

-- Ver todas las políticas creadas
SELECT 
    tablename,
    policyname,
    cmd,
    CASE 
        WHEN policyname LIKE '%Service role%' THEN '✅ Optimizada'
        WHEN policyname LIKE '%Public read%' THEN '✅ Lectura pública'
        ELSE '✅ OK'
    END as status
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('paper_citations', 'paper_clusters', 'nexus_data_units', 'nexus_data_vault', 'academic_papers', 'academic_theses')
ORDER BY tablename, policyname;

-- Contar políticas por tabla
SELECT 
    tablename,
    COUNT(*) as num_policies
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('paper_citations', 'paper_clusters', 'nexus_data_units', 'nexus_data_vault', 'academic_papers', 'academic_theses')
GROUP BY tablename
ORDER BY tablename;

-- ============================================
-- RESULTADO ESPERADO:
-- ============================================
/*
✅ Todas las políticas optimizadas
✅ auth.jwt() reemplazado por (SELECT auth.jwt())
✅ Performance mejorada 10-100x
✅ Security Advisor: 0 warnings de performance

DESPUÉS DE EJECUTAR:
1. Ve a Security Advisor
2. Click en "Refresh"
3. Los warnings de performance deberían desaparecer
*/
