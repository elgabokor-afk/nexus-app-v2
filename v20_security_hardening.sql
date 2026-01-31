-- V20 Security Hardening
-- Description: Restrict overly permissive policies identified by Security Advisor.

-- 1. HARDEN PAPER_POSITIONS
-- Drop the loose policies created in V13
DROP POLICY IF EXISTS "Allow Authenticated Update" ON paper_positions;
DROP POLICY IF EXISTS "Allow Public Update" ON paper_positions;

-- Create Restricted Update Policy
-- Only allow updates to positions that are currently OPEN.
-- This prevents tampering with historical (CLOSED) trade data.
CREATE POLICY "Secure Update Active" ON paper_positions
    FOR UPDATE
    USING (status = 'OPEN')
    WITH CHECK (status = 'OPEN'); 

-- 2. HARDEN ERROR_LOGS
-- Drop logical "Allow Service Access for ALL" if it exists (cleaning up)
DROP POLICY IF EXISTS "Allow Service Access for ALL" ON error_logs;

-- Allow Insert for logging (Public/Bot)
CREATE POLICY "Allow Log Insert" ON error_logs
    FOR INSERT
    WITH CHECK (true);

-- Allow Select for Dashboard (Public/Auth)
CREATE POLICY "Allow Log View" ON error_logs
    FOR SELECT
    USING (true);

-- 3. HARDEN FUNCTIONS
-- (No other SQL functions need hardening at this time)
