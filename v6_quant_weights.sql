-- NEXUS V6.5: SMART WEIGHTS & MACD
-- Run this in Supabase SQL Editor

-- 1. Update Analytics Table for MACD
alter table analytics_signals
add column if not exists macd_line numeric,
add column if not exists signal_line numeric,
add column if not exists histogram numeric;

-- 2. Update Bot Params for Dynamic Strategy Weights
alter table bot_params
add column if not exists weight_rsi numeric default 0.3,
add column if not exists weight_imbalance numeric default 0.3,
add column if not exists weight_trend numeric default 0.2,
add column if not exists weight_macd numeric default 0.2;

-- 3. Reset Defaults (Optional, ensures sum is 1.0)
update bot_params set 
    weight_rsi = 0.3, 
    weight_imbalance = 0.3,
    weight_trend = 0.2,
    weight_macd = 0.2
where active = true;
