-- MASTER PURGE SCRIPT (Handling ALL Dependencies)
-- 1. Delete from Paper Positions (The new blocker)
DELETE FROM public.paper_positions 
WHERE signal_id IN (
    SELECT id FROM public.signals 
    WHERE symbol LIKE 'USD1%' OR symbol LIKE 'USDC%' OR symbol LIKE 'FDUSD%' OR symbol LIKE 'USDE%' OR symbol LIKE 'TUSD%' OR symbol LIKE 'BUSD%'
);

-- 2. Delete from Paper Trades
DELETE FROM public.paper_trades 
WHERE signal_id IN (
    SELECT id FROM public.signals 
    WHERE symbol LIKE 'USD1%' OR symbol LIKE 'USDC%' OR symbol LIKE 'FDUSD%' OR symbol LIKE 'USDE%' OR symbol LIKE 'TUSD%' OR symbol LIKE 'BUSD%'
);

-- 3. Delete from VIP Details
DELETE FROM public.vip_signal_details 
WHERE signal_id IN (
    SELECT id FROM public.signals 
    WHERE symbol LIKE 'USD1%' OR symbol LIKE 'USDC%' OR symbol LIKE 'FDUSD%' OR symbol LIKE 'USDE%' OR symbol LIKE 'TUSD%' OR symbol LIKE 'BUSD%'
);

-- 4. Delete from Audit History
DELETE FROM public.signal_audit_history 
WHERE signal_id IN (
    SELECT id FROM public.signals 
    WHERE symbol LIKE 'USD1%' OR symbol LIKE 'USDC%' OR symbol LIKE 'FDUSD%' OR symbol LIKE 'USDE%' OR symbol LIKE 'TUSD%' OR symbol LIKE 'BUSD%'
);

-- 5. Delete from Analytics (Skipped as table is missing)
-- DELETE FROM public.analytics_signals ...

-- 6. FINALLY Delete the Signals
DELETE FROM public.signals 
WHERE symbol LIKE 'USD1%' 
   OR symbol LIKE 'USDC%' 
   OR symbol LIKE 'FDUSD%' 
   OR symbol LIKE 'USDE%'
   OR symbol LIKE 'TUSD%'
   OR symbol LIKE 'BUSD%';

-- 7. Legacy Tables (Just in case)
DELETE FROM public.market_signals 
WHERE symbol LIKE 'USD1%' 
   OR symbol LIKE 'USDC%' 
   OR symbol LIKE 'FDUSD%' 
   OR symbol LIKE 'USDE%'
   OR symbol LIKE 'TUSD%'
   OR symbol LIKE 'BUSD%';
