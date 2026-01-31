-- ENABLE PUBLIC ACCESS FOR PAPER TRADING HISTORY
-- Run this in Supabase SQL Editor

-- 1. Enable RLS on the table (if not already enabled)
alter table paper_positions enable row level security;

-- 2. Create Policy: Allow Public Read Access
-- This ensures 'anon' users (public dashboard) can fetch the wins/losses
create policy "Public Read Positions"
on paper_positions
for select
to anon, authenticated, service_role
using (true);

-- 3. Create Policy: Service Role Write Access
-- Only the backend (service_role) should be able to insert/update trades
create policy "Service Role Write Positions"
on paper_positions
for insert
to service_role
with check (true);

create policy "Service Role Update Positions"
on paper_positions
for update
to service_role
using (true);

-- 4. Enable Realtime subscriptions for this table
alter publication supabase_realtime add table paper_positions;
