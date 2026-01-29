-- Fix: Missing RLS Policies for academic_alpha
-- Issue: Table has RLS enabled but no policies, blocking access or flagging security warnings.

-- 1. Ensure RLS is enabled (idempotent)
ALTER TABLE public.academic_alpha ENABLE ROW LEVEL SECURITY;

-- 2. Policy: Service Role (Backend/Admin) - Full Access
CREATE POLICY "Service Role can manage alpha"
  ON public.academic_alpha
  FOR ALL
  USING ( auth.role() = 'service_role' );

-- 3. Policy: Public/Authenticated (Users/Bots) - Read Only
-- Assuming strategies (alpha) might be public or at least visible to the bot
CREATE POLICY "Public/Bot can read alpha"
  ON public.academic_alpha
  FOR SELECT
  USING ( true );

-- 4. Verification Check
do $$
begin
  if not exists (
    select from pg_policies where tablename = 'academic_alpha'
  ) then
    raise warning 'Policies for academic_alpha were not created correctly.';
  else
    raise notice 'RLS Policies for academic_alpha applied successfully.';
  end if;
end $$;
