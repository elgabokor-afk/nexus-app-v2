-- Enable Supabase Realtime for critical tables (Plan B)
-- This allows the frontend to fall back to Supabase if Pusher fails.

BEGIN;

-- 1. Add 'signals' to the publication
ALTER PUBLICATION supabase_realtime ADD TABLE public.signals;

-- 2. Add 'paper_positions' (for PaperTrader backup)
ALTER PUBLICATION supabase_realtime ADD TABLE public.paper_positions;

-- 3. Add 'bot_wallet' (for Balance updates)
ALTER PUBLICATION supabase_realtime ADD TABLE public.bot_wallet;

COMMIT;

-- Verification (Output will appear in SQL Editor)
select * from pg_publication_tables where pubname = 'supabase_realtime';
