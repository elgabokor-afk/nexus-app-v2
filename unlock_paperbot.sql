-- Unlock PaperBot Constraints

-- 0. Schema Fix: Add missing column if not exists
ALTER TABLE public.bot_params ADD COLUMN IF NOT EXISTS max_daily_positions INTEGER DEFAULT 5;

-- 1. Reset/Create permissve Bot Params
INSERT INTO public.bot_params (id, active, min_confidence, max_daily_positions, trading_fee_pct, account_risk_pct, strategy_version)
OVERRIDING SYSTEM VALUE
VALUES (1, true, 60.0, 50, 0.00075, 0.02, 2)
ON CONFLICT (id) DO UPDATE SET
    active = true,
    min_confidence = 60.0,
    max_daily_positions = 50,
    trading_fee_pct = 0.00075;

-- 2. Ensure Wallet has funds
UPDATE public.bot_wallet 
SET balance = 10000, equity = 10000 
WHERE id = 1 AND equity < 100;

-- 3. Clear "Stuck" positions (Optional, good for fresh start)
-- UPDATE public.paper_positions SET status = 'CLOSED', exit_reason = 'RESET' WHERE status = 'OPEN';
