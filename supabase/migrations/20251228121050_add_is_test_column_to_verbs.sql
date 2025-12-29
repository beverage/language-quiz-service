-- Add is_test column to verbs table
-- Test verbs are excluded from random selection during problem generation

ALTER TABLE verbs ADD COLUMN IF NOT EXISTS is_test BOOLEAN NOT NULL DEFAULT false;

-- Index for filtering out test verbs efficiently
CREATE INDEX IF NOT EXISTS idx_verbs_is_test ON verbs (is_test) WHERE is_test = false;

-- Drop and recreate the get_random_verb_simple function to exclude test verbs
DROP FUNCTION IF EXISTS get_random_verb_simple(text);

CREATE FUNCTION get_random_verb_simple(p_target_language text DEFAULT 'eng')
RETURNS SETOF verbs
LANGUAGE sql
STABLE
AS $$
    SELECT *
    FROM verbs
    WHERE target_language_code = p_target_language
      AND is_test = false
    ORDER BY random()
    LIMIT 1;
$$;

COMMENT ON COLUMN verbs.is_test IS 'Flag to mark test data verbs that should be excluded from production queries';
