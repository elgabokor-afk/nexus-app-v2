-- UPGRADE PAPER POSITIONS FOR V3 DECISION TRACKING
-- Run this in Supabase SQL Editor

-- 1. Add specific risk management columns to the positions table
-- This allows us to compare "What the Bot Did" vs "What the Signal Said"
alter table paper_positions 
add column if not exists bot_stop_loss numeric,
add column if not exists bot_take_profit numeric;

-- 2. Notify Realtime to pick up Schema Changes
NOTIFY pgrst, 'reload config';
