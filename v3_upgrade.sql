-- NEXUS V3.0: SELF-OPTIMIZING ENGINE SCHEMA
-- Run this in Supabase SQL Editor to upgrade the "Brain"

-- 1. Create 'bot_wallet' (The Virtual Bankroll)
create table if not exists bot_wallet (
    id int primary key generated always as identity,
    balance numeric not null default 10000.00,  -- Initial $10k
    equity numeric not null default 10000.00,   -- Balance + Unrealized PnL
    total_trades int default 0,
    last_updated timestamp with time zone default timezone('utc'::text, now())
);

-- Seed Initial Wallet (Only if empty)
insert into bot_wallet (balance, equity)
select 10000.00, 10000.00
where not exists (select 1 from bot_wallet);

-- 2. Create 'bot_params' (The Learning Memory)
create table if not exists bot_params (
    id int primary key generated always as identity,
    active boolean default true,
    
    -- Dynamic Trading Variables (The bot will tweak these)
    rsi_buy_threshold int default 30,           -- Standard Oversold
    stop_loss_atr_mult numeric default 1.5,     -- Risk Multiplier
    take_profit_atr_mult numeric default 2.5,   -- Reward Multiplier
    
    -- Performance Tracking for this "Genotype"
    win_rate_window numeric default 0.0,
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Seed Initial Parameters
insert into bot_params (rsi_buy_threshold, stop_loss_atr_mult, take_profit_atr_mult)
select 30, 1.5, 2.5
where not exists (select 1 from bot_params);

-- 3. Enable Public Access (So Dashboard can show Wallet/Params)
alter table bot_wallet enable row level security;
alter table bot_params enable row level security;

create policy "Public Read Wallet"
on bot_wallet for select
to anon, authenticated, service_role
using (true);

create policy "Public Read Params"
on bot_params for select
to anon, authenticated, service_role
using (true);

-- 4. Enable Service Role Write Access (For the Python Bot)
create policy "Bot Update Wallet"
on bot_wallet for update
to service_role
using (true);

create policy "Bot Update Params"
on bot_params for update
to service_role
using (true);

-- 5. Realtime
alter publication supabase_realtime add table bot_wallet;
alter publication supabase_realtime add table bot_params;
