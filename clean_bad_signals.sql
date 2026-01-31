-- Clean Bad Signals (Normalization Errors)
-- Deletes signals that have 'USD/USDT' or are 'USDT/USDC' garbage

DELETE FROM public.signals
WHERE symbol LIKE '%USD/USDT' -- e.g. UNIUSD/USDT
   OR symbol LIKE '%USDT/USDC'
   OR symbol LIKE '%UP/USDT'
   OR symbol LIKE '%DOWN/USDT';

-- Also delete from paper_trades if cascade doesn't handle it (it should due to FK, but safe check)
-- (Normally signals.id is FK in paper_trades with DELETE CASCADE? Let's assume yes or ignore orphans for now)
