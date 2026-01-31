-- V1701: Cleanup Authenticated Policies
-- Fixes "Multiple permissive policies" warning for 'Allow Authenticated Read Access'

-- 1. Drop the specific AUTHENTICATED policy causing the warning
DROP POLICY IF EXISTS "Allow Authenticated Read Access" ON paper_positions;
DROP POLICY IF EXISTS "Enable read access for all users" ON paper_positions;
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON paper_positions;

-- 2. Ensure "Public Read Positions" is the ONLY Read policy
-- (We recreate it just to be safe, ensuring it covers everyone)
DROP POLICY IF EXISTS "Public Read Positions" ON paper_positions;

CREATE POLICY "Public Read Positions" ON paper_positions 
FOR SELECT USING (true);

-- 3. Ensure INSERT/UPDATE policies are separate (if needed)
-- Usually we want the Service Role to handle writes, but if you need Auth users to write:
-- CREATE POLICY "Auth Write Positions" ON paper_positions FOR INSERT TO authenticated WITH CHECK (true);
