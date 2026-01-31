-- Force Visibility Policy
-- Ensures that 'anon' (public users) and 'authenticated' (logged in users) can ALWAYS see open positions.

-- 1. Drop existing policies to avoid conflicts (clean slate for SELECT)
DROP POLICY IF EXISTS "Enable read access for all users" ON paper_positions;
DROP POLICY IF EXISTS "Allow Public Read" ON paper_positions;

-- 2. Create the Ultimate Read Policy
CREATE POLICY "Universal Read Access" ON paper_positions
    FOR SELECT
    USING (true);

-- 3. Verify Realtime is ON (Commented out as it causes error if already added)
-- ALTER PUBLICATION supabase_realtime ADD TABLE paper_positions;

-- 4. Grant Select Permissions explicitly
GRANT SELECT ON paper_positions TO anon;
GRANT SELECT ON paper_positions TO authenticated;
GRANT SELECT ON bot_wallet TO anon;
GRANT SELECT ON bot_wallet TO authenticated;

COMMENT ON TABLE paper_positions IS 'Trading history - Publicly visible for transparency';
