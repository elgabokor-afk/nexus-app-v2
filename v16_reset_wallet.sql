-- Reset Bot Wallet to Initial State
-- Sets Balance and Equity back to $10,000 and clears "Broken" state.

UPDATE bot_wallet 
SET 
    balance = 10000, 
    equity = 10000, 
    last_updated = NOW() 
WHERE id = 1;

-- Optional: Close all open positions if we mark them as 'RESET' or just leave them?
-- Usually better to mark old positions as closed if we are resetting the wallet to avoid PnL mismatch.
UPDATE paper_positions 
SET status = 'CLOSED', exit_reason = 'WALLET_RESET', exit_price = entry_price, pnl = 0 
WHERE status = 'OPEN';
