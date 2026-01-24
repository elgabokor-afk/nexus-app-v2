-- NEXUS V4.0: QUANTITATIVE ANALYST UPGRADE
-- Run this in Supabase SQL Editor

-- 1. Create 'analytics_signals' table (Deep Dive Metrics)
-- This table stores heavy quantitative data for each signal, keeping the main table light.
create table if not exists analytics_signals (
    id int primary key generated always as identity,
    signal_id int references market_signals(id) on delete cascade,
    
    -- Quant Metrics
    ema_200 numeric,                -- Trend Baseline
    rsi_value numeric,             -- RSI at signal time
    atr_value numeric,             --  Volatility at signal time
    
    -- Order Book Analysis
    imbalance_ratio numeric,        -- (-1.0 to 1.0) Bid/Ask Pressure
    spread_pct numeric,             -- Bid-Ask Spread %
    order_book_depth_score numeric, -- Liquidity Score (0-100)
    
    -- Meta
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- 2. Add Index for fast lookups
create index if not exists idx_analytics_signal_id on analytics_signals(signal_id);

-- 3. Security Policies (RLS)
alter table analytics_signals enable row level security;

-- Public Read (Dashboard needs to show this)
create policy "Public Read Analytics"
on analytics_signals for select
to anon, authenticated, service_role
using (true);

-- Service Role Write (Python Bot needs to insert)
create policy "Bot Insert Analytics"
on analytics_signals for insert
to service_role
with check (true);

-- 4. Realtime
alter publication supabase_realtime add table analytics_signals;
