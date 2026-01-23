-- UPGRADE DATABASE FOR ADVANCED METRICS
-- Run this in Supabase SQL Editor

-- 1. Add metrics to 'market_signals' if they don't exist
alter table market_signals 
add column if not exists atr_value numeric,
add column if not exists volume_ratio numeric;

-- 2. Add metrics to 'paper_positions' for performance analysis
alter table paper_positions 
add column if not exists confidence_score numeric,
add column if not exists signal_type text,
add column if not exists rsi_entry numeric,
add column if not exists atr_entry numeric;

-- 3. Notify Realtime to pick up Schema Changes
NOTIFY pgrst, 'reload config';
