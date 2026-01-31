
-- FIX_REALTIME_RANKING.sql
-- Description: Forces the 'ai_asset_rankings' table to be public and broadcasted via Realtime.

-- 1. Ensure Table Permissions (RLS)
ALTER TABLE public.ai_asset_rankings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public Read Rankings" ON public.ai_asset_rankings;
CREATE POLICY "Public Read Rankings" ON public.ai_asset_rankings FOR SELECT USING (true);


-- 2. Force Realtime Broadcast
-- We remove it first to ensure a clean add (in case it was stuck)
ALTER PUBLICATION supabase_realtime DROP TABLE public.ai_asset_rankings;
ALTER PUBLICATION supabase_realtime ADD TABLE public.ai_asset_rankings;

-- 3. Verify Replica Identity (Required for updates to broadcast correctly)
ALTER TABLE public.ai_asset_rankings REPLICA IDENTITY FULL;
