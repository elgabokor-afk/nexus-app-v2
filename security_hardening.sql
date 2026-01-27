-- SECURITY HARDENING: ROW LEVEL SECURITY (RLS) LOCKDOWN
-- Prevents anonymous users from hacking the bot logic or faking signals.

BEGIN;

-- 1. HARDEN SIGNALS TABLE
-- Only the Service Role (Backend) can INSERT/UPDATE/DELETE.
-- Authenticated & Anon users can ONLY SELECT.
ALTER TABLE public.signals ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Enable read access for all users" ON public.signals;
CREATE POLICY "Enable read access for all users" ON public.signals FOR SELECT USING (true);

DROP POLICY IF EXISTS "Enable write access for service role only" ON public.signals;
CREATE POLICY "Enable write access for service role only" ON public.signals 
FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

-- 2. HARDEN PAPER TRADES (User Specific)
-- Users can only see THEIR OWN trades.
ALTER TABLE public.paper_trades ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own trades" ON public.paper_trades;
CREATE POLICY "Users can view own trades" ON public.paper_trades 
FOR SELECT 
TO authenticated 
USING (auth.uid() = user_id);

-- Backend (Service Role) needs full access to manage trades for everyone
DROP POLICY IF EXISTS "Service role manages all trades" ON public.paper_trades;
CREATE POLICY "Service role manages all trades" ON public.paper_trades 
FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

-- 3. HARDEN ERROR LOGS
-- Only Service Role can INSERT logs. Admins can view.
ALTER TABLE public.error_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role inserts logs" ON public.error_logs;
CREATE POLICY "Service role inserts logs" ON public.error_logs 
FOR INSERT 
TO service_role 
WITH CHECK (true);

DROP POLICY IF EXISTS "Admins view logs" ON public.error_logs;
-- Assuming 'authenticated' for now, can be restricted to specific email later
CREATE POLICY "Admins view logs" ON public.error_logs 
FOR SELECT 
TO authenticated 
USING (true);

COMMIT;
