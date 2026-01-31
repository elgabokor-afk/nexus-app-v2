-- ============================================
-- CLEANUP RLS FINAL - Resolver todos los warnings
-- ============================================
-- Elimina políticas duplicadas y optimiza las restantes
-- ============================================

-- ============================================
-- PARTE 1: Limpiar academic_papers (tiene muchas políticas duplicadas)
-- ============================================
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'academic_papers') THEN
        -- Eliminar TODAS las políticas antiguas
        DROP POLICY IF EXISTS "Service Delete Papers" ON public.academic_papers;
        DROP POLICY IF EXISTS "Service Insert Papers" ON public.academic_papers;
        DROP POLICY IF EXISTS "Service Update Papers" ON public.academic_papers;
        DROP POLICY IF EXISTS "Public read access" ON public.academic_papers;
        DROP POLICY IF EXISTS "Public read papers" ON public.academic_papers;
        DROP POLICY IF EXISTS "Public/Bot can read papers" ON public.academic_papers;
        DROP POLICY IF EXISTS "Service role full access" ON public.academic_papers;
        
        -- Crear SOLO 2 políticas optimizadas
        CREATE POLICY "Public read access"
        ON public.academic_papers
        FOR SELECT
        TO public
        USING (true);
        
        CREATE POLICY "Service role full access"
        ON public.academic_papers
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);
        
        RAISE NOTICE '✅ academic_papers limpiada y optimizada';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️ Error en academic_papers: %', SQLERRM;
END $$;

-- ============================================
-- PARTE 2: Limpiar nexus_data_vault
-- ============================================
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'nexus_data_vault') THEN
        -- Eliminar políticas duplicadas
        DROP POLICY IF EXISTS "Authenticated users can read" ON public.nexus_data_vault;
        DROP POLICY IF EXISTS "Public Read Vault" ON public.nexus_data_vault;
        DROP POLICY IF EXISTS "Service role full access" ON public.nexus_data_vault;
        
        -- Crear SOLO 2 políticas optimizadas
        CREATE POLICY "Public read access"
        ON public.nexus_data_vault
        FOR SELECT
        TO public
        USING (true);
        
        CREATE POLICY "Service role full access"
        ON public.nexus_data_vault
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);
        
        RAISE NOTICE '✅ nexus_data_vault limpiada y optimizada';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️ Error en nexus_data_vault: %', SQLERRM;
END $$;

-- ============================================
-- PARTE 3: Limpiar paper_citations
-- ============================================
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'paper_citations') THEN
        -- Eliminar políticas duplicadas
        DROP POLICY IF EXISTS "Anyone can view paper_citations" ON public.paper_citations;
        DROP POLICY IF EXISTS "Public read access" ON public.paper_citations;
        DROP POLICY IF EXISTS "Service role full access" ON public.paper_citations;
        
        -- Crear SOLO 2 políticas optimizadas
        CREATE POLICY "Public read access"
        ON public.paper_citations
        FOR SELECT
        TO public
        USING (true);
        
        CREATE POLICY "Service role full access"
        ON public.paper_citations
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);
        
        RAISE NOTICE '✅ paper_citations limpiada y optimizada';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️ Error en paper_citations: %', SQLERRM;
END $$;

-- ============================================
-- PARTE 4: Limpiar paper_clusters
-- ============================================
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'paper_clusters') THEN
        -- Eliminar políticas duplicadas
        DROP POLICY IF EXISTS "Anyone can view paper_clusters" ON public.paper_clusters;
        DROP POLICY IF EXISTS "Public read access" ON public.paper_clusters;
        DROP POLICY IF EXISTS "Service role full access" ON public.paper_clusters;
        
        -- Crear SOLO 2 políticas optimizadas
        CREATE POLICY "Public read access"
        ON public.paper_clusters
        FOR SELECT
        TO public
        USING (true);
        
        CREATE POLICY "Service role full access"
        ON public.paper_clusters
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);
        
        RAISE NOTICE '✅ paper_clusters limpiada y optimizada';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️ Error en paper_clusters: %', SQLERRM;
END $$;

-- ============================================
-- VERIFICACIÓN FINAL
-- ============================================

-- Ver todas las políticas restantes
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
AND tablename IN ('academic_papers', 'nexus_data_vault', 'paper_citations', 'paper_clusters')
ORDER BY tablename, policyname;

-- Contar políticas por tabla (debería ser 2 por tabla)
SELECT 
    tablename,
    COUNT(*) as num_policies,
    CASE 
        WHEN COUNT(*) = 2 THEN '✅ Correcto'
        WHEN COUNT(*) > 2 THEN '⚠️ Aún hay duplicadas'
        ELSE '❌ Muy pocas'
    END as status
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('academic_papers', 'nexus_data_vault', 'paper_citations', 'paper_clusters')
GROUP BY tablename
ORDER BY tablename;

-- ============================================
-- RESULTADO ESPERADO:
-- ============================================
/*
✅ academic_papers: 2 políticas (Public read + Service role)
✅ nexus_data_vault: 2 políticas (Public read + Service role)
✅ paper_citations: 2 políticas (Public read + Service role)
✅ paper_clusters: 2 políticas (Public read + Service role)

DESPUÉS DE EJECUTAR:
1. Ve a Security Advisor
2. Click en "Refresh"
3. Los 40 warnings deberían reducirse significativamente
4. Solo quedarán warnings informativos (OK)
*/
