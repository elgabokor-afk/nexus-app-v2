-- Optimizing RLS Policies for user_exchanges to reduce function calls
-- Wrapping in (select ...) forces a single evaluation per query instead of per row

DROP POLICY IF EXISTS "Users can view own keys" ON user_exchanges;
CREATE POLICY "Users can view own keys"
ON user_exchanges FOR SELECT
USING (user_id = (select auth.uid()));

DROP POLICY IF EXISTS "Users can insert own keys" ON user_exchanges;
CREATE POLICY "Users can insert own keys"
ON user_exchanges FOR INSERT
WITH CHECK (user_id = (select auth.uid()));

DROP POLICY IF EXISTS "Users can delete own keys" ON user_exchanges;
CREATE POLICY "Users can delete own keys"
ON user_exchanges FOR DELETE
USING (user_id = (select auth.uid()));
