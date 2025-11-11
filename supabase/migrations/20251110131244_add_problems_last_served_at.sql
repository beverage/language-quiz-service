-- Add last_served_at column to problems table for tracking problem usage
ALTER TABLE problems ADD COLUMN last_served_at TIMESTAMPTZ;

-- Add composite index for efficient LRU querying
-- Order: last_served_at ASC NULLS FIRST, then created_at ASC (oldest first)
CREATE INDEX idx_problems_lru ON problems(last_served_at ASC NULLS FIRST, created_at ASC);

-- Add comment for documentation
COMMENT ON COLUMN problems.last_served_at IS 'Timestamp when this problem was last served to a user via GET /problems/random. NULL indicates never served. Queries order by last_served_at (NULLS FIRST) then created_at for deterministic LRU selection.';

