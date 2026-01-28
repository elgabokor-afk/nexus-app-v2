-- RELAX BOT PARAMS (Unlock Trades)
UPDATE public.bot_params
SET 
  min_confidence = 55.0,     -- Was 70.0 (Signals are ~60 now)
  min_rrr = 1.5,             -- Was 2.5 (Too strict)
  rsi_buy_threshold = 70,    -- Was 30 (Allow "Momentum" buys)
  account_risk_pct = 0.5,    -- Increase risk slightly to see impact
  max_open_positions = 10    -- Allow more concurrency
WHERE active = true;

NOTIFY pgrst, 'reload config';
