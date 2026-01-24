-- Enable RLS on paper_positions if not already enabled
ALTER TABLE paper_positions ENABLE ROW LEVEL SECURITY;

-- Allow public (anon) read access to paper_positions
-- This allows the marketing website to fetch live trades without login
CREATE POLICY "Allow Public Read Access" ON paper_positions
    FOR SELECT
    TO anon
    USING (true);

-- Ensure service_role still has full access (already implicit, but good to be safe if policies restrict)
-- (No specific policy needed for service_role usually as it bypasses RLS, but ensuring authenticated users can also read)
CREATE POLICY "Allow Authenticated Read Access" ON paper_positions
    FOR SELECT
    TO authenticated
    USING (true);
