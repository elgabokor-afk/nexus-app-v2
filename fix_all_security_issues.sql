
-- ============================================
-- FIX ALL SECURITY ISSUES - Supabase Security Advisor
-- ============================================
-- Resuelve TODOS los problemas de RLS detectados
-- ============================================

-- ============================================
-- PASO 1: Verificar qué tablas existen
-- ============================================
SELECT 
    table_name,
    'EXISTS' as status
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'paper_players', 
    'paper_attempts', 
    'paper_stats',
    'paper_clusters',
    'paper_citations'
)
ORDER BY table_name;

-- ============================================
-- PASO 2: Limpiar tablas que NO existen
-- ============================================
DROP VIEW IF EXISTS public.paper_stats CASCADE;
DROP TABLE IF EXISTS public.paper_players CASCADE;
DROP TABLE IF EXISTS public.paper_attempts CASCADE;

-- ============================================
-- PASO 3: Habilitar RLS en tablas que SÍ existen
-- ============================================

-- Fix para paper_clusters (si existe)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'paper_clusters'
    ) THEN
        -- Habilitar RLS
        ALTER TABLE public.paper_clusters ENABLE ROW LEVEL SECURITY;
        
        -- Política: Todos pueden leer (datos académicos públicos)
        CREATE POLICY "Anyone can view paper_clusters"
        ON public.paper_clusters
        FOR SELECT
        USING (true);
        
        -- Política: Solo service_role puede insertar/actualizar
        CREATE POLICY "Service role can manage paper_clusters"
        ON public.paper_clusters
        FOR ALL
        USING (auth.jwt()->>'role' = 'service_role')
        WITH CHECK (auth.jwt()->>'role' = 'service_role');
        
        RAISE NOTICE 'RLS habilitado en paper_clusters';
    ELSE
        RAISE NOTICE 'paper_clusters no existe, saltando...';
    END IF;
END $$;

-- Fix para paper_citations (si existe)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'paper_citations'
    ) THEN
        -- Habilitar RLS
        ALTER TABLE public.paper_citations ENABLE ROW LEVEL SECURITY;
        
        -- Política: Todos pueden leer (datos académicos públicos)
        CREATE POLICY "Anyone can view paper_citations"
        ON public.paper_citations
        FOR SELECT
        USING (true);
        
        -- Política: Solo service_role puede insertar/actualizar
        CREATE POLICY "Service role can manage paper_citations"
        ON public.paper_citations
        FOR ALL
        USING (auth.jwt()->>'role' = 'service_role')
        WITH CHECK (auth.jwt()->>'role' = 'service_role');
        
        RAISE NOTICE 'RLS habilitado en paper_citations';
    ELSE
        RAISE NOTICE 'paper_citations no existe, saltando...';
    END IF;
END $$;

-- ============================================
-- PASO 4: Verificar que RLS está habilitado
-- ============================================
SELECT 
    schemaname,
    tablename,
    rowsecurity,
    CASE 
        WHEN rowsecurity THEN '✅ RLS Habilitado'
        ELSE '❌ RLS Deshabilitado'
    END as status
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('paper_clusters', 'paper_citations')
ORDER BY tablename;

-- ============================================
-- PASO 5: Ver políticas creadas
-- ============================================
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    cmd
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('paper_clusters', 'paper_citations')
ORDER BY tablename, policyname;

-- ============================================
-- RESULTADO ESPERADO:
-- ============================================
-- ✅ paper_clusters: RLS Habilitado con 2 políticas
-- ✅ paper_citations: RLS Habilitado con 2 políticas
-- ✅ Security Advisor: 0 errores
-- ============================================

-- ============================================
-- NOTAS:
-- ============================================
/*
1. Las tablas académicas (paper_clusters, paper_citations) son públicas
   porque contienen información de papers/tesis que todos pueden ver

2. Solo el service_role (backend) puede modificarlas

3. Después de ejecutar:
   - Ve a Security Advisor
   - Click en "Refresh"
   - Todos los errores deberían desaparecer
*/
