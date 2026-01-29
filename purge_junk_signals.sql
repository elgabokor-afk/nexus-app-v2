-- Purge Unwanted Stablecoin Signals
DELETE FROM public.signals 
WHERE symbol LIKE 'USD1%' 
   OR symbol LIKE 'USDC%' 
   OR symbol LIKE 'FDUSD%' 
   OR symbol LIKE 'USDE%'
   OR symbol LIKE 'TUSD%'
   OR symbol LIKE 'BUSD%';

-- Also clean up analytics linked to them (cascade should handle it, but just in case)
-- (Cascades are set on signal_id references usually)
