
-- RESET_TRADES.sql
-- WARNING: This will DELETE ALL paper trading history.
-- Use this to reset the "Daily Trade Limit" counter to 0.

TRUNCATE TABLE public.paper_positions;

-- Optional: Reset Wallet Logic (if you want a fresh start)
-- UPDATE public.bot_wallet SET balance = 1000, equity = 1000, updated_at = now();

