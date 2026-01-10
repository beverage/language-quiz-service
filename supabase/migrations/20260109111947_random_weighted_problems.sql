-- Add function for weighted random problem selection
-- 
-- This replaces simple LRU ordering with a probabilistic approach that:
-- 1. Favors problems that haven't been served recently (staleness-weighted)
-- 2. Gives never-served problems a configurable "virtual staleness" 
-- 3. Adds randomization so batch-generated problems don't create hotspots
--
-- The weighting formula:
--   weight = staleness_seconds * random_multiplier
--   where random_multiplier is between 0.5 and 1.5
--
-- This means a 6-day-old problem might score anywhere from 259,200 to 777,600,
-- while a never-served problem with 3-day virtual staleness scores 129,600 to 388,800.
-- The ranges overlap, creating probabilistic fairness.

CREATE OR REPLACE FUNCTION get_weighted_random_problem(
    p_problem_type TEXT DEFAULT NULL,
    p_focus TEXT DEFAULT NULL,
    p_topic_tags TEXT[] DEFAULT NULL,
    p_target_language_code TEXT DEFAULT NULL,
    p_virtual_staleness_days FLOAT DEFAULT 3.0
)
RETURNS SETOF problems
LANGUAGE sql
VOLATILE  -- Uses random(), result varies between calls
AS $$
    SELECT *
    FROM problems
    WHERE 
        -- Apply filters (NULL means no filter)
        (p_problem_type IS NULL OR problem_type = p_problem_type::public.problem_type)
        AND (p_focus IS NULL OR metadata->'grammatical_focus' ? p_focus)
        AND (p_topic_tags IS NULL OR topic_tags && p_topic_tags)
        AND (p_target_language_code IS NULL OR target_language_code = p_target_language_code)
    ORDER BY
        -- Weighted random: staleness * random_factor (0.5 to 1.5)
        COALESCE(
            EXTRACT(EPOCH FROM (NOW() - last_served_at)),
            p_virtual_staleness_days * 86400  -- Virtual staleness for never-served
        ) * (0.5 + random())
    DESC
    LIMIT 1;
$$;

-- Add comment for documentation
COMMENT ON FUNCTION get_weighted_random_problem IS 
'Select a problem using weighted random selection that favors staleness while avoiding 
batch hotspots. Problems that have not been served recently have higher probability of 
selection, but randomization ensures variety. Never-served problems are given virtual 
staleness (default 3 days) so they compete fairly with older served problems.

Parameters:
- p_problem_type: Filter by problem type (NULL for any)
- p_focus: Filter by grammar focus via metadata.grammatical_focus (NULL for any)
- p_topic_tags: Filter by topic tags using array overlap (NULL for any)  
- p_target_language_code: Filter by language code (NULL for any)
- p_virtual_staleness_days: How many days of "virtual" staleness to give never-served 
  problems. Higher values favor never-served problems more strongly.';