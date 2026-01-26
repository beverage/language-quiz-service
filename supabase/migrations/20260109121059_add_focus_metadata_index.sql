-- Add expression index for filtering by grammatical_focus in metadata
-- This enables efficient queries like: WHERE metadata->>'grammatical_focus' @> '["conjugation"]'
-- 
-- This index replaces the previous approach of duplicating focus values in topic_tags.
-- Focus is now stored only in metadata.grammatical_focus, keeping topic_tags for
-- semantic content tags only (food, travel, etc.)

CREATE INDEX IF NOT EXISTS idx_problems_grammatical_focus 
ON problems USING GIN ((metadata->'grammatical_focus'));

COMMENT ON INDEX idx_problems_grammatical_focus IS 
'GIN index on metadata.grammatical_focus for efficient focus-based filtering';
