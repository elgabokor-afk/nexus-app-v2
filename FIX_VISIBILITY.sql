
-- FIX_VISIBILITY.sql
-- Ensures the Dashboard can see data without being logged in (or as Anon).

-- 1. Market Signals
ALTER TABLE public.market_signals ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public Read Signals" ON public.market_signals;
CREATE POLICY "Public Read Signals" ON public.market_signals FOR SELECT USING (true);

-- 2. Paper Positions
ALTER TABLE public.paper_positions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public Read Positions" ON public.paper_positions;
CREATE POLICY "Public Read Positions" ON public.paper_positions FOR SELECT USING (true);

-- 3. System Logs
ALTER TABLE public.system_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public Read Logs" ON public.system_logs;
CREATE POLICY "Public Read Logs" ON public.system_logs FOR SELECT USING (true);

-- 4. Assets (for Oracle)
ALTER TABLE public.assets ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public Read Assets" ON public.assets;
CREATE POLICY "Public Read Assets" ON public.assets FOR SELECT USING (true);
