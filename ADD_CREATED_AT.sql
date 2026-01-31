
-- ADD_CREATED_AT.sql
-- Fixes "column paper_positions.created_at does not exist" error.

ALTER TABLE public.paper_positions 
ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL;

-- Backfill existing rows if needed (though default handles new ones)
-- UPDATE public.paper_positions SET created_at = now() WHERE created_at IS NULL;
