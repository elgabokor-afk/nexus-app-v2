-- V2100: NUCLEAR POLICY RESET
-- The "Nice" method didn't work. Now we use the Brute Force method.
-- This script drops ALL policies on 'paper_positions' and 'bot_params' completely.

-- 1. Disable RLS momentarily to flush policies
ALTER TABLE paper_positions DISABLE ROW LEVEL SECURITY;
ALTER TABLE bot_params DISABLE ROW LEVEL SECURITY;

-- 2. DROP BY NAME (Coverage for known variants)
DROP POLICY IF EXISTS "Allow Authenticated Read Access" ON paper_positions;
DROP POLICY IF EXISTS "Public Read Positions" ON paper_positions;
DROP POLICY IF EXISTS "Enable read access for all users" ON paper_positions;
DROP POLICY IF EXISTS "Public Read Access" ON paper_positions;
DROP POLICY IF EXISTS "Allow Public Read Access" ON paper_positions;
DROP POLICY IF EXISTS "Universal Read Access" ON paper_positions;

-- 3. Re-Enable RLS
ALTER TABLE paper_positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_params ENABLE ROW LEVEL SECURITY;

-- 4. Create the ONLY 2 Policies needed
-- A. Bot Params: Public Read
CREATE POLICY "Obey The Config" ON bot_params 
FOR SELECT USING (true);

-- B. Paper Positions: Public Read (Dashboard needs this)
CREATE POLICY "Universal Dashboard Access" ON paper_positions 
FOR SELECT USING (true);

-- 5. Permission Grant (Just in case role was revoked)
GRANT SELECT ON paper_positions TO anon, authenticated, service_role;
GRANT SELECT ON bot_params TO anon, authenticated, service_role;
