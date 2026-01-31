-- V129: ZOMBIE DATA PURGE
-- The user has 4800+ "OPEN" positions in the DB, likely from old testing or bugs.
-- This prevents the bot from opening new trades (Max 5 limit).

-- 1. Close ALL positions currently marked as OPEN.
-- We use a special exit reason 'ZOMBIE_PURGE' to identify them later.
UPDATE paper_positions
SET 
    status = 'CLOSED',
    exit_reason = 'ZOMBIE_PURGE',
    exit_price = entry_price, -- Neutral exit (no PnL impact on stats ideally, or 0)
    closed_at = NOW(),
    pnl = 0
WHERE status = 'OPEN';

-- 2. Verify Cleanup
SELECT count(*) as remaining_open FROM paper_positions WHERE status = 'OPEN';

-- NOTE:
-- After running this, restart the bot (paper_trader.py).
-- The V121 'reconcile_positions()' function will automatically detecting the *actual* 
-- open trades from Binance and re-insert them as valid, fresh records.
