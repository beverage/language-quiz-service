-- Migration: Enhanced weighted random problem selection with indexed metadata filters
-- 
-- This migration:
-- 1. Adds partial expression indexes on JSONB metadata fields for grammar problems
-- 2. Updates get_weighted_random_problem to use explicit parameters for known filter fields
--    (enabling index usage) while retaining a generic JSONB fallback for edge cases
--
-- Performance notes:
-- - Partial indexes only cover rows where problem_type = 'grammar', keeping them small
-- - Expression indexes on (metadata->'field') allow the ?| operator to use GIN
-- - Problems are immutable, so index maintenance cost is insert-only

-- ============================================================================
-- STEP 1: Create partial expression indexes for grammar problem filters
-- ============================================================================

-- Index for grammatical_focus filtering (e.g., "pronouns", "conjugation", "agreement")
CREATE INDEX IF NOT EXISTS idx_problems_grammatical_focus 
ON problems USING GIN ((metadata->'grammatical_focus'))
WHERE problem_type = 'grammar';

-- Index for tenses_used filtering (e.g., "présent", "futur_simple", "subjonctif_présent")
CREATE INDEX IF NOT EXISTS idx_problems_tenses_used 
ON problems USING GIN ((metadata->'tenses_used'))
WHERE problem_type = 'grammar';

-- General GIN index on metadata for fallback queries and ad-hoc filtering
-- This helps with the generic p_metadata_array_filters parameter
CREATE INDEX IF NOT EXISTS idx_problems_metadata_gin 
ON problems USING GIN (metadata);

-- Index to support the ORDER BY on last_served_at for staleness weighting
-- NULLS FIRST because never-served problems have NULL last_served_at
CREATE INDEX IF NOT EXISTS idx_problems_last_served_at 
ON problems (last_served_at NULLS FIRST);

-- ============================================================================
-- STEP 2: Update get_weighted_random_problem function
-- ============================================================================

-- Drop ALL existing function signatures (handles function overloading)
-- CASCADE ensures dependent objects are handled, but this function shouldn't have any
DROP FUNCTION IF EXISTS get_weighted_random_problem CASCADE;

-- Create the function with new signature
-- Using CREATE (not CREATE OR REPLACE) since we've already dropped all versions
CREATE FUNCTION get_weighted_random_problem(
    -- Core filters
    p_problem_type TEXT DEFAULT NULL,
    p_topic_tags TEXT[] DEFAULT NULL,
    p_target_language_code TEXT DEFAULT NULL,
    
    -- Explicit grammar metadata filters (CAN use expression indexes)
    -- These are the primary filter dimensions for grammar problems
    p_grammatical_focus TEXT[] DEFAULT NULL,  -- e.g., ARRAY['pronouns', 'conjugation']
    p_tenses_used TEXT[] DEFAULT NULL,        -- e.g., ARRAY['futur_simple', 'imparfait']
    
    -- Generic fallback for rare/future filter fields (won't use indexes efficiently)
    -- Format: {"field_name": ["value1", "value2"]} with OR logic within each field
    p_metadata_array_filters JSONB DEFAULT NULL,
    
    -- Staleness weighting configuration
    p_virtual_staleness_days FLOAT DEFAULT 3.0
)
RETURNS SETOF problems
LANGUAGE sql
VOLATILE  -- Uses random(), result varies between calls
AS $$
    SELECT p.*
    FROM problems p
    WHERE 
        -- Core column filters (use standard indexes)
        (p_problem_type IS NULL OR p.problem_type = p_problem_type::problem_type)
        AND (p_topic_tags IS NULL OR p.topic_tags && p_topic_tags)
        AND (p_target_language_code IS NULL OR p.target_language_code = p_target_language_code)
        
        -- Explicit metadata array filters (CAN use partial expression indexes)
        -- Using ?| operator: returns true if the array contains ANY of the specified values
        AND (
            p_grammatical_focus IS NULL 
            OR (p.metadata->'grammatical_focus') ?| p_grammatical_focus
        )
        AND (
            p_tenses_used IS NULL 
            OR (p.metadata->'tenses_used') ?| p_tenses_used
        )
        
        -- Generic metadata array filters (fallback for fields without explicit indexes)
        -- Each key in the JSONB is a metadata field name, value is array of acceptable values
        -- Logic: AND between fields, OR within each field's values
        AND (
            p_metadata_array_filters IS NULL
            OR (
                SELECT bool_and(
                    CASE 
                        -- Field must exist and be an array to match
                        WHEN p.metadata ? elem.key 
                             AND jsonb_typeof(p.metadata->elem.key) = 'array'
                        THEN (p.metadata->elem.key) ?| ARRAY(
                            SELECT jsonb_array_elements_text(elem.value)
                        )
                        -- Field missing or not an array = no match
                        ELSE false
                    END
                )
                FROM jsonb_each(p_metadata_array_filters) AS elem
            )
        )
    ORDER BY
        -- Weighted random selection: staleness_seconds * random_factor
        -- Higher staleness = more likely to be selected (but not deterministic)
        -- random_factor range [0.5, 1.5] adds controlled randomness
        COALESCE(
            EXTRACT(EPOCH FROM (NOW() - p.last_served_at)),
            p_virtual_staleness_days * 86400  -- Virtual staleness for never-served problems
        ) * (0.5 + random())
    DESC
    LIMIT 1;
$$;

-- ============================================================================
-- STEP 3: Add helpful comments
-- ============================================================================

COMMENT ON FUNCTION get_weighted_random_problem IS 
'Selects a single problem using weighted random selection that favors staleness.

Parameters:
  - p_problem_type: Filter by problem type (grammar, functional, vocabulary)
  - p_topic_tags: Filter by topic tags (array overlap / OR logic)
  - p_target_language_code: Filter by target language
  - p_grammatical_focus: Filter grammar problems by focus areas (OR logic, uses index)
  - p_tenses_used: Filter grammar problems by tenses (OR logic, uses index)
  - p_metadata_array_filters: Generic JSONB filter for other array fields
  - p_virtual_staleness_days: Staleness value for never-served problems (default 3 days)

Returns: Single problem row, or empty set if no matches

Example usage:
  -- Get any grammar problem about pronouns or conjugation
  SELECT * FROM get_weighted_random_problem(
    p_problem_type := ''grammar'',
    p_grammatical_focus := ARRAY[''pronouns'', ''conjugation'']
  );
  
  -- Get a futur_simple problem (any grammatical focus)
  SELECT * FROM get_weighted_random_problem(
    p_problem_type := ''grammar'',
    p_tenses_used := ARRAY[''futur_simple'']
  );
  
  -- Combine filters: pronouns in present or imparfait
  SELECT * FROM get_weighted_random_problem(
    p_problem_type := ''grammar'',
    p_grammatical_focus := ARRAY[''pronouns''],
    p_tenses_used := ARRAY[''présent'', ''imparfait'']
  );
';

-- ============================================================================
-- STEP 4: Verify indexes were created
-- ============================================================================

-- You can run this after the migration to verify:
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'problems';