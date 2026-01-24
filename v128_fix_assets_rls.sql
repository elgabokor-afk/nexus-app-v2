-- V128: Fix RLS on market_assets
-- User reported this table was public but had RLS disabled.

-- 1. Enable RLS
ALTER TABLE market_assets ENABLE ROW LEVEL SECURITY;

-- 2. Create Public Read Policy
-- Allows dashboard and bot to read asset list
DROP POLICY IF EXISTS "Public Read Assets" ON market_assets;

CREATE POLICY "Public Read Assets"
ON market_assets FOR SELECT
TO anon, authenticated, service_role
USING (true);

-- 3. Create Service Role Maintenance Policy
-- Allows backend to update priority scores or add new assets
DROP POLICY IF EXISTS "Service Maintenance Assets" ON market_assets;

CREATE POLICY "Service Maintenance Assets"
ON market_assets FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

COMMENT ON TABLE market_assets IS 'Registry of top 20 assets (RLS Enabled via V128)';
