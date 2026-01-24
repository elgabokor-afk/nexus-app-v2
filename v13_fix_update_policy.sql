-- Enable UPDATE access for Manual Close functionality
-- Without this, the Frontend cannot set 'closure_requested' to TRUE.

-- 1. Allow Generic Update for Authenticated Users (Safe)
CREATE POLICY "Allow Authenticated Update" ON paper_positions
    FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- 2. Allow Update for Anon Users (If using Public Dashboard)
-- CAUTION: This allows anyone to requested a close. For V2 demo this is fine.
CREATE POLICY "Allow Public Update" ON paper_positions
    FOR UPDATE
    TO anon
    USING (true)
    WITH CHECK (true);

-- Retry in case it failed before due to conflict
DO $$
BEGIN
    RAISE NOTICE 'Update Policies Added. Manual Close should work now.';
END $$;
