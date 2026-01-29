-- Clean bad symbol FOGO and weak signals
DELETE FROM signals 
WHERE symbol LIKE '%FOGO%' OR symbol LIKE 'FOGO%';

-- Clean invalid confidence signals (Garbage that slipped through)
-- If confidence is below 60, kill it (unless it's a legacy structure we trust, but 24 is definitely bad)
DELETE FROM signals 
WHERE ai_confidence < 60;

-- Clean signals where Entry = TP (Flat/Broken Calc)
DELETE FROM signals 
WHERE entry_price = tp_price OR entry_price = sl_price;
