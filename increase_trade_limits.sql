-- Relax Bot Parameters
-- Increases limits to allow 300+ trades/day

UPDATE public.bot_params
SET 
  max_open_positions = 50, -- High concurrent limit
  cooldown_minutes = 0,    -- No cooldown between trades (fire at will)
  weight_trend = 0.1,      -- Lower trend strictness to allow more volume
  weight_rsi = 0.4,        -- Focus on RSI mean reversion
  active = true
WHERE active = true;

-- If no row exists, insert default high-volume config
INSERT INTO public.bot_params (max_open_positions, cooldown_minutes, weight_rsi, weight_imbalance, weight_trend, active)
SELECT 50, 0, 0.4, 0.3, 0.1, true
WHERE NOT EXISTS (SELECT 1 FROM public.bot_params WHERE active = true);
