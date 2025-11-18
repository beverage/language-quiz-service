-- Create generation_requests table for tracking async entity generation
CREATE TABLE generation_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type TEXT NOT NULL,
  status TEXT NOT NULL,
  requested_count INT NOT NULL,
  generated_count INT DEFAULT 0,
  failed_count INT DEFAULT 0,
  requested_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  constraints JSONB,
  metadata JSONB,
  error_message TEXT,
  
  CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'partial', 'failed'))
);

-- Create indexes for efficient querying
CREATE INDEX idx_generation_requests_status ON generation_requests(status);
CREATE INDEX idx_generation_requests_entity_type ON generation_requests(entity_type);
CREATE INDEX idx_generation_requests_requested_at ON generation_requests(requested_at DESC);

-- Add comment for documentation
COMMENT ON TABLE generation_requests IS 'Tracks async entity generation requests (problems, sentences, etc.) with status and results';

-- Drop the old request_id column from problems table
ALTER TABLE problems DROP COLUMN IF EXISTS request_id;

-- Add generation_request_id column to problems table
-- Use ON DELETE SET NULL to allow cleanup of old generation_requests without affecting problems
ALTER TABLE problems ADD COLUMN generation_request_id UUID;

-- Add foreign key constraint with ON DELETE SET NULL
ALTER TABLE problems 
  ADD CONSTRAINT problems_generation_request_id_fkey 
  FOREIGN KEY (generation_request_id) 
  REFERENCES generation_requests(id) 
  ON DELETE SET NULL;

-- Add index for efficient lookup by generation_request_id
CREATE INDEX idx_problems_generation_request_id ON problems(generation_request_id);

-- Add comment for documentation
COMMENT ON COLUMN problems.generation_request_id IS 'UUID of the generation request that created this problem. Links to generation_requests table for tracking and querying batch results. Set to NULL if generation request is deleted.';

