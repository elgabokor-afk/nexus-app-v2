-- V1601: Fix Invalid Symbol (POL/USD -> POL/USDT)
-- This fixes the "[BINANCE] Error fetching ticker" spam.

-- 1. Fix in paper_positions
UPDATE paper_positions
SET symbol = 'POL/USDT'
WHERE symbol = 'POL/USD';

-- 2. Fix in market_signals
UPDATE market_signals
SET symbol = 'POL/USDT'
WHERE symbol = 'POL/USD';

-- 3. Cleanup logic: If POL/USDT is still invalid on Binance (e.g. if you don't have access), 
-- you can uncomment the next lines to just close/delete them:
-- UPDATE paper_positions SET status = 'CLOSED', exit_reason = 'INVALID_SYMBOL' WHERE symbol LIKE 'POL%';
