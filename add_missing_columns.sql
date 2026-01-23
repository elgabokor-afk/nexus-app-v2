
-- ADD MISSING COLUMNS
-- Run this in Supabase SQL Editor to fix the "Column not found" error

ALTER TABLE public.market_signals 
ADD COLUMN IF NOT EXISTS stop_loss numeric,
ADD COLUMN IF NOT EXISTS take_profit numeric;

-- Reload Schema Cache (Explicitly notify PostgREST)
NOTIFY pgrst, 'reload config';
