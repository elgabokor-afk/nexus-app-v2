-- V1302: Policy Cleanup Script
-- Run this in Supabase SQL Editor to fix "Multiple permissive policies" warnings.

-- 1. Clean bot_params
DROP POLICY IF EXISTS "Public Read Params" ON bot_params;
DROP POLICY IF EXISTS "Public Read Params Fixed" ON bot_params;
DROP POLICY IF EXISTS "Allow Public Read" ON bot_params;

-- Re-apply single clean policy
CREATE POLICY "Public Read Params" ON bot_params 
FOR SELECT USING (true);


-- 2. Clean paper_positions
DROP POLICY IF EXISTS "Allow Public Read Access" ON paper_positions;
DROP POLICY IF EXISTS "Public Read Access" ON paper_positions;
DROP POLICY IF EXISTS "Public Read Positions" ON paper_positions;
DROP POLICY IF EXISTS "Universal Read Access" ON paper_positions;

-- Re-apply single clean policy
CREATE POLICY "Public Read Positions" ON paper_positions 
FOR SELECT USING (true);

-- 3. Ensure RLS is enabled
ALTER TABLE bot_params ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_positions ENABLE ROW LEVEL SECURITY;
