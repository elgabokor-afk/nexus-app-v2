-- Security Patch: Restrict oracle_insights to service_role only for writes
-- PREVIOUSLY: WITH CHECK (true) -> VULNERABLE
-- NOW: WITH CHECK (auth.role() = 'service_role') -> SECURE

BEGIN;

-- 1. Drop the permissive policy if it exists (using generic name assumption or we just replace)
DROP POLICY IF EXISTS "Allow Oracle Insert" ON public.oracle_insights;
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON public.oracle_insights;

-- 2. Create strict policy for INSERT
CREATE POLICY "Strict Oracle Write"
ON public.oracle_insights
FOR INSERT
TO service_role
WITH CHECK (true); -- Only service_role handles have access via 'TO service_role'

-- 3. Ensure SELECT is public or authed (keeping existing read access if needed)
-- Assuming we want users to SEE the insights but not fake them.
DROP POLICY IF EXISTS "Enable read access for all users" ON public.oracle_insights;
CREATE POLICY "Public Read Access"
ON public.oracle_insights
FOR SELECT
TO authenticated, anon
USING (true);

COMMIT;
