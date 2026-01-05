-- Migration: Add generation_trace column to problems table
-- Purpose: Store full generation metadata including reasoning traces, prompts, and quality info
-- 
-- This enables:
-- 1. Debugging bizarre outputs by examining the reasoning process
-- 2. Pattern discovery across generations
-- 3. Quality tracking and future self-review mechanisms
-- 4. Cost analysis via token usage tracking

-- Add generation_trace JSONB column
ALTER TABLE problems ADD COLUMN IF NOT EXISTS generation_trace JSONB;

-- Add comment documenting the expected structure
COMMENT ON COLUMN problems.generation_trace IS 'Full generation metadata including:
{
  "model": "gpt-5-nano-2025-08-07",
  "prompt_version": "2.0",
  "generation_time_ms": 4500,
  "response_id": "chatcmpl-abc123",
  
  // Token usage
  "prompt_tokens": 1250,
  "completion_tokens": 312,
  "total_tokens": 1562,
  "reasoning_tokens": 2847,
  
  // The reasoning trace
  "reasoning_content": "First, I need to consider...",
  
  // Full prompt for reproducibility
  "prompt_text": "You are a French grammar expert...",
  
  // Quality tracking
  "quality_status": "approved|pending_review|rejected",
  "quality_issues": []
}';

-- Index for querying by model (useful for comparing model performance)
CREATE INDEX IF NOT EXISTS idx_problems_generation_trace_model 
  ON problems ((generation_trace->>'model'));

-- Index for querying by quality status (useful for review workflows)
CREATE INDEX IF NOT EXISTS idx_problems_generation_trace_quality_status 
  ON problems ((generation_trace->>'quality_status'));

-- Index for querying by prompt version (useful for A/B testing prompts)
CREATE INDEX IF NOT EXISTS idx_problems_generation_trace_prompt_version 
  ON problems ((generation_trace->>'prompt_version'));

-- Partial index for problems needing review (efficient for review queue)
CREATE INDEX IF NOT EXISTS idx_problems_pending_review 
  ON problems ((generation_trace->>'quality_status'))
  WHERE generation_trace->>'quality_status' = 'pending_review';
