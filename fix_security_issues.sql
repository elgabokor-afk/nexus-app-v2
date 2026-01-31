-- ============================================
-- FIX SECURITY ISSUES - Supabase Security Advisor
-- ============================================
-- Fecha: 31 de Enero, 2026
-- Problemas detectados: 3 errores de seguridad
-- ============================================

-- ============================================
-- FIX 1: Habilitar RLS en paper_players
-- ============================================
ALTER TABLE public.paper_players ENABLE ROW LEVEL SECURITY;

-- Crear política para que los usuarios solo vean sus propios datos
CREATE POLICY "Users can view their own paper_players"
ON public.paper_players
FOR SELECT
USING (auth.uid() = user_id);

-- Política para insertar (si es necesario)
CREATE POLICY "Users can insert their own paper_players"
ON public.paper_players
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Política para actualizar (si es necesario)
CREATE POLICY "Users can update their own paper_players"
ON public.paper_players
FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- ============================================
-- FIX 2: Habilitar RLS en paper_attempts
-- ============================================
ALTER TABLE public.paper_attempts ENABLE ROW LEVEL SECURITY;

-- Crear política para que los usuarios solo vean sus propios intentos
CREATE POLICY "Users can view their own paper_attempts"
ON public.paper_attempts
FOR SELECT
USING (auth.uid() = user_id);

-- Política para insertar
CREATE POLICY "Users can insert their own paper_attempts"
ON public.paper_attempts
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- ============================================
-- FIX 3: Arreglar Security Definer View (paper_stats)
-- ============================================

-- Opción A: Cambiar a SECURITY INVOKER (Recomendado)
-- Primero, obtener la definición de la vista
-- Luego recrearla con SECURITY INVOKER

-- Eliminar la vista existente
DROP VIEW IF EXISTS public.paper_stats;

-- Recrear la vista con SECURITY INVOKER
-- NOTA: Ajusta esta definición según tu vista actual
CREATE OR REPLACE VIEW public.paper_stats
WITH (security_invoker = true)
AS
SELECT 
    user_id,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful_attempts,
    AVG(score) as average_score
FROM public.paper_attempts
GROUP BY user_id;

-- Dar permisos de lectura a usuarios autenticados
GRANT SELECT ON public.paper_stats TO authenticated;

-- ============================================
-- VERIFICACIÓN
-- ============================================

-- Verificar que RLS está habilitado
SELECT 
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('paper_players', 'paper_attempts');

-- Verificar políticas creadas
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('paper_players', 'paper_attempts')
ORDER BY tablename, policyname;

-- ============================================
-- NOTAS IMPORTANTES
-- ============================================

/*
1. Si paper_stats tiene una definición diferente, ajusta el CREATE VIEW
2. Si no tienes columna user_id en estas tablas, ajusta las políticas
3. Después de ejecutar, verifica en Security Advisor que los errores desaparecieron
4. Si tienes otras tablas sin RLS, considera habilitarlo también

ALTERNATIVA para paper_stats (si no quieres cambiar la vista):
- Puedes mantener SECURITY DEFINER pero asegurarte de que la vista
  solo expone datos que el usuario debería ver
- Añadir WHERE auth.uid() = user_id en la definición de la vista
*/
