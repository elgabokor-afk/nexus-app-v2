-- 1. Create the Secure Table
CREATE TABLE IF NOT EXISTS public.vip_signal_details (
    signal_id BIGINT REFERENCES public.signals(id) ON DELETE CASCADE PRIMARY KEY,
    entry_price NUMERIC,
    tp_price NUMERIC,
    sl_price NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Enable RLS
ALTER TABLE public.vip_signal_details ENABLE ROW LEVEL SECURITY;

-- 3. Policies
-- VIP Users: READ ONLY
DROP POLICY IF EXISTS "VIP Read Details" ON public.vip_signal_details;
CREATE POLICY "VIP Read Details" ON public.vip_signal_details
FOR SELECT TO authenticated
USING (
  (select auth.uid()) IN (SELECT id FROM public.profiles WHERE subscription_level = 'vip')
);

-- Service Role: FULL ACCESS
DROP POLICY IF EXISTS "Service Role Full Access" ON public.vip_signal_details;
CREATE POLICY "Service Role Full Access" ON public.vip_signal_details
FOR ALL TO service_role
USING (true);

-- 4. Realtime
DO $$
BEGIN
  INSERT INTO _realtime.publication_tables (publication_name, schema_name, table_name)
  VALUES ('supabase_realtime', 'public', 'vip_signal_details')
  ON CONFLICT DO NOTHING;
EXCEPTION WHEN OTHERS THEN
  NULL;
END $$;

-- 5. Data Migration (Backfill)
INSERT INTO public.vip_signal_details (signal_id, entry_price, tp_price, sl_price, created_at)
SELECT id, entry_price, tp_price, sl_price, created_at
FROM public.signals
ON CONFLICT (signal_id) DO UPDATE 
SET entry_price = EXCLUDED.entry_price,
    tp_price = EXCLUDED.tp_price,
    sl_price = EXCLUDED.sl_price;

-- NOTE: We are NOT dropping columns from 'signals' yet to prevent immediate downtime.
-- We will deprecate them in the next step after Frontend/Worker updates are live.
