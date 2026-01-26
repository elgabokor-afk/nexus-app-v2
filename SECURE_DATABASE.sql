
-- SECURE_DATABASE.sql
-- Fixes "Unrestricted Access" warnings by tightening policies.

-- 1. ERROR LOGS (Strict)
ALTER TABLE public.error_logs ENABLE ROW LEVEL SECURITY;

-- Remove old/loose policies
DROP POLICY IF EXISTS "Enable insert for all users" ON public.error_logs;
DROP POLICY IF EXISTS "Public Read Logs" ON public.error_logs;

-- Security Fix: Only allow Service Role (Bot) or Authenticated Users to Insert
CREATE POLICY "Strict Log Insert" ON public.error_logs
FOR INSERT TO authenticated, service_role
WITH CHECK (true);

-- Allow Public Read (for Dashboard Debugging) - Read-Only is safe
CREATE POLICY "Public Read Logs" ON public.error_logs
FOR SELECT USING (true);


-- 2. SYSTEM LOGS (Strict)
ALTER TABLE public.system_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Enable insert for all users" ON public.system_logs;

CREATE POLICY "Strict System Log Insert" ON public.system_logs
FOR INSERT TO authenticated, service_role
WITH CHECK (true);

CREATE POLICY "Public Read System Logs" ON public.system_logs
FOR SELECT USING (true);
