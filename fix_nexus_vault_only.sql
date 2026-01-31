-- ============================================
-- FIX NEXUS_DATA_VAULT - Resolver 5 warnings restantes
-- ============================================
-- Este script solo arregla nexus_data_vault
-- ============================================

DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'nexus_data_vault') THEN
        
        RAISE NOTICE '🔧 Limpiando nexus_data_vault...';
        
        -- Eliminar TODAS las políticas existentes
        DROP POLICY IF EXISTS "Authenticated users can read" ON public.nexus_data_vault;
        DROP POLICY IF EXISTS "Public Read Vault" ON public.nexus_data_vault;
        DROP POLICY IF EXISTS "Public read access" ON public.nexus_data_vault;
        DROP POLICY IF EXISTS "Service role full access" ON public.nexus_data_vault;
        DROP POLICY IF EXISTS "Service Role Write Vault" ON public.nexus_data_vault;
        DROP POLICY IF EXISTS "Service role can manage vault" ON public.nexus_data_vault;
        DROP POLICY IF EXISTS "Anyone can read vault" ON public.nexus_data_vault;
        
        RAISE NOTICE '✅ Políticas antiguas eliminadas';
        
        -- Crear SOLO 2 políticas optimizadas con TO role
        CREATE POLICY "Public read access"
        ON public.nexus_data_vault
        FOR SELECT
        TO public
        USING (true);
        
        RAISE NOTICE '✅ Política de lectura pública creada';
        
        CREATE POLICY "Service role full access"
        ON public.nexus_data_vault
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);
        
        RAISE NOTICE '✅ Política de service role creada';
        RAISE NOTICE '🎉 nexus_data_vault optimizada correctamente';
        
    ELSE
        RAISE NOTICE '⚠️ Tabla nexus_data_vault no existe';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '❌ Error: %', SQLERRM;
END $$;

-- ============================================
-- VERIFICACIÓN
-- ============================================

-- Ver políticas de nexus_data_vault
SELECT 
    tablename,
    policyname,
    roles,
    cmd,
    CASE 
        WHEN policyname = 'Service role full access' AND roles = '{service_role}' THEN '✅ Correcto'
        WHEN policyname = 'Public read access' AND roles = '{public}' THEN '✅ Correcto'
        ELSE '⚠️ Revisar'
    END as status
FROM pg_policies
WHERE schemaname = 'public'
AND tablename = 'nexus_data_vault'
ORDER BY policyname;

-- Contar políticas (debería ser 2)
SELECT 
    COUNT(*) as num_policies,
    CASE 
        WHEN COUNT(*) = 2 THEN '✅ Correcto - 2 políticas'
        WHEN COUNT(*) > 2 THEN '⚠️ Aún hay duplicadas'
        ELSE '❌ Muy pocas políticas'
    END as status
FROM pg_policies
WHERE schemaname = 'public'
AND tablename = 'nexus_data_vault';

-- ============================================
-- RESULTADO ESPERADO:
-- ============================================
/*
✅ 2 políticas en nexus_data_vault:
   1. "Public read access" - roles: {public} - cmd: SELECT
   2. "Service role full access" - roles: {service_role} - cmd: ALL

DESPUÉS DE EJECUTAR:
1. Ve a Security Advisor
2. Click en "Refresh"
3. Los 5 warnings de nexus_data_vault deberían desaparecer
4. Total warnings: 0 ✅
*/
