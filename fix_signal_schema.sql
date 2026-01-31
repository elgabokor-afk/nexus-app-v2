-- Migration: Rename 'pair' to 'symbol' for consistency across the stack
-- Run this in Supabase SQL Editor

ALTER TABLE public.signals 
RENAME COLUMN pair TO symbol;

-- Update the RLS Policy to be safe (just in case they relied on column names, though unlikely)
-- No changes to RLS needed as they are Row-based ('true').
