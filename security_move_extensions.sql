-- Security Patch: Move Extensions out of Public Schema
-- This prevents namespace pollution and improves security.

-- 1. Create the 'extensions' schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS extensions;

-- 2. Grant usage to standard roles
GRANT USAGE ON SCHEMA extensions TO postgres, anon, authenticated, service_role;

-- 3. Move the 'vector' extension to the new schema
-- This assumes the extension is currently in 'public' or another schema.
-- If it's not installed, this line might fail, so we wrap in a block or just use standard command.
-- ALTER EXTENSION is idempotent regarding the destination if it's already there? No.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_extension 
        WHERE extname = 'vector' AND extnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    ) THEN
        ALTER EXTENSION vector SET SCHEMA extensions;
    END IF;
END $$;

-- 4. Ensure future calls find it (Global Search Path update is often not possible via SQL editor for the whole cluster, 
-- but we can set it for the specific user or database if we had superuser, which Supabase usually handles).
-- Instead, we ensure our functions use "SET search_path = public, extensions".

-- 5. Re-verify function 'match_academic_knowledge' uses the correct path
-- (This was patched in the previous step, but re-asserting here makes this file self-contained for the fix).
CREATE OR REPLACE FUNCTION match_academic_knowledge (
  query_embedding extensions.vector(3072), -- explicit type reference if needed, or rely on search_path
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id bigint,
  content text,
  title text,
  university text,
  similarity float
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions
AS $$
BEGIN
  RETURN QUERY(
    SELECT
      ac.id,
      ac.content,
      ap.title,
      ap.university,
      1 - (ac.embedding <=> query_embedding) as similarity
    FROM
      public.academic_chunks ac
    JOIN
      public.academic_papers ap ON ac.paper_id = ap.id
    WHERE
      1 - (ac.embedding <=> query_embedding) > match_threshold
    ORDER BY
      ac.embedding <=> query_embedding
    LIMIT
      match_count
  );
END;
$$;
