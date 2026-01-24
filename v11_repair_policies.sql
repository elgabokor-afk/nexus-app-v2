-- Drop policies if they exist to avoid conflicts (Safe Repair)
DROP POLICY IF EXISTS "Allow Public Read Access" ON paper_positions;
DROP POLICY IF EXISTS "Allow Authenticated Read Access" ON paper_positions;

-- Re-Enable RLS
ALTER TABLE paper_positions ENABLE ROW LEVEL SECURITY;

-- 1. Allow Public (Anon) Read Access
CREATE POLICY "Allow Public Read Access" ON paper_positions
    FOR SELECT
    TO anon
    USING (true);

-- 2. Allow Authenticated (Logged In) Read Access
CREATE POLICY "Allow Authenticated Read Access" ON paper_positions
    FOR SELECT
    TO authenticated
    USING (true);

-- Output success message
DO $$
BEGIN
    RAISE NOTICE 'Policies successfully repaired for paper_positions';
END $$;
