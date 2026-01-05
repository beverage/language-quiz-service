-- Add 'expired' status to the valid_status check constraint
-- This status is used by expire_stale_pending_requests to mark old PENDING
-- requests that were never processed (e.g., due to service crash or rebalance)

-- Drop the existing constraint and recreate with 'expired' included
ALTER TABLE generation_requests
  DROP CONSTRAINT IF EXISTS valid_status;

ALTER TABLE generation_requests
  ADD CONSTRAINT valid_status CHECK (
    status IN ('pending', 'processing', 'completed', 'partial', 'failed', 'expired')
  );

