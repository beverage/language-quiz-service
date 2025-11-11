-- Add request_id column to problems table for tracking generation requests
-- This allows correlation between API requests and generated problems

ALTER TABLE problems ADD COLUMN request_id UUID;

-- Add index for efficient lookup by request_id
CREATE INDEX idx_problems_request_id ON problems(request_id);

-- Add comment for documentation
COMMENT ON COLUMN problems.request_id IS 'UUID of the generation request that created this problem. Used for tracking and debugging problem generation through the async pipeline.';


