-- FIX V3 SCHEMA MIGRATION
-- Use this if you get "column does not exist" errors

-- 1. Ensure 'bot_params' has the new columns
alter table bot_params 
add column if not exists rsi_buy_threshold int default 30,
add column if not exists stop_loss_atr_mult numeric default 1.5,
add column if not exists take_profit_atr_mult numeric default 2.5;

-- 2. Ensure 'bot_wallet' exists
create table if not exists bot_wallet (
    id int primary key generated always as identity,
    balance numeric not null default 10000.00,
    equity numeric not null default 10000.00,
    total_trades int default 0,
    last_updated timestamp with time zone default timezone('utc'::text, now())
);

-- 3. Run the inserts again (safe to run multiple times)
insert into bot_params (rsi_buy_threshold, stop_loss_atr_mult, take_profit_atr_mult)
select 30, 1.5, 2.5
where not exists (select 1 from bot_params);

insert into bot_wallet (balance, equity)
select 10000.00, 10000.00
where not exists (select 1 from bot_wallet);

-- 4. Re-apply permissions just in case
alter table bot_wallet enable row level security;
alter table bot_params enable row level security;

create policy "Public Read Wallet V3"
on bot_wallet for select to anon, authenticated, service_role using (true);

create policy "Public Read Params V3"
on bot_params for select to anon, authenticated, service_role using (true);

-- 5. Realtime
alter publication supabase_realtime add table bot_wallet;
alter publication supabase_realtime add table bot_params;
