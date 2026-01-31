-- NEXUS V5.0: LEVERAGE & MARGIN UPGRADE
-- Run this in Supabase SQL Editor

-- 1. Update Global Params
alter table bot_params 
add column if not exists default_leverage int default 10,
add column if not exists margin_mode text default 'ISOLATED';

-- 2. Update Positions Table
alter table paper_positions
add column if not exists leverage int default 10,
add column if not exists margin_mode text default 'ISOLATED',
add column if not exists liquidation_price numeric,
add column if not exists initial_margin numeric;

-- 3. Update existing records (optional cleanup)
update paper_positions set initial_margin = (entry_price * quantity) / 10 where initial_margin is null;
