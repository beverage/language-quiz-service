# Generation Requests Tracking API

**Status:** Design / Not Implemented  
**Priority:** Medium  
**Effort:** 2-3 days

## Problem Statement

When using async generation via Kafka (`POST /problems/generate`), users receive a 202 response with request IDs but have no way to:
- Track generation status (pending, processing, completed, failed)
- Retrieve generated entities after the fact
- Understand partial failures (requested 10, got 7)
- Poll for completion

This is especially important as we move to thinking models with 20-30 second generation times.

## Proposed Solution

Create a **generic generation tracking system** that works across all LLM-generated entities (problems, sentences, vocabulary, etc.).

### API Design

#### Core Endpoint
```http
GET /generation-requests/{request_id}
```

**Response:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "entity_type": "problem",
  "status": "completed",
  "requested_at": "2025-11-16T10:30:00Z",
  "completed_at": "2025-11-16T10:32:15Z",
  "requested_count": 10,
  "generated_count": 10,
  "failed_count": 0,
  "entities": [
    { /* full problem object */ },
    { /* full problem object */ }
  ]
}
```

**Status Values:**
- `pending` - Request created, not yet picked up by worker
- `processing` - Worker actively generating
- `completed` - All requested entities generated successfully
- `partial` - Some entities generated, some failed
- `failed` - Complete failure, no entities generated

#### Future: List/Search Endpoint (Admin/Analytics)
```http
GET /generation-requests?entity_type=problem&status=completed&limit=20
```

### Database Schema

#### New Table: `generation_requests`
```sql
CREATE TABLE generation_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type TEXT NOT NULL,           -- 'problem', 'sentence', 'vocabulary'
  status TEXT NOT NULL,                -- 'pending', 'processing', 'completed', 'partial', 'failed'
  requested_count INT NOT NULL,
  generated_count INT DEFAULT 0,
  failed_count INT DEFAULT 0,
  requested_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  constraints JSONB,                   -- Original request constraints
  metadata JSONB,                      -- Additional context
  error_message TEXT,                  -- If status = failed
  
  CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'partial', 'failed'))
);

CREATE INDEX idx_generation_requests_status ON generation_requests(status);
CREATE INDEX idx_generation_requests_entity_type ON generation_requests(entity_type);
CREATE INDEX idx_generation_requests_requested_at ON generation_requests(requested_at DESC);
```

#### Add Column to Entities
```sql
-- Problems
ALTER TABLE problems 
  ADD COLUMN generation_request_id UUID REFERENCES generation_requests(id);

CREATE INDEX idx_problems_generation_request_id ON problems(generation_request_id);

-- Future: Same pattern for sentences, vocabulary, etc.
ALTER TABLE sentences 
  ADD COLUMN generation_request_id UUID REFERENCES generation_requests(id);
```

**Note:** Rename existing `request_id` column (from migration 20251111000000) to `generation_request_id`.

### Request Limits

To prevent abuse and ensure reasonable response times:

- **Default count:** 1 entity per request
- **Hard limit:** 10 entities per request
- **Enforced at:** API level and CLI level

Rationale:
- Prevents overwhelming LLM APIs
- Keeps response sizes manageable (~12KB for 10 problems)
- Thinking models may take 20-30s per entity (10 entities = 5 minutes max)

### Workflow Changes

#### API: POST /problems/generate
```json
// Request
{
  "count": 5,
  "constraints": { ... }
}

// Response (202 Accepted)
{
  "message": "Generation request created",
  "request_id": "550e8400-...",  // NEW: Single request ID, not array
  "count": 5,
  "status": "pending"
}
```

**Changes:**
1. Create `generation_requests` record with status='pending'
2. Publish Kafka message with `generation_request_id`
3. Return single `request_id` (not array - one request, potentially many entities)

#### Worker: Problem Generation Handler
```python
async def handle(self, message: dict):
    request_id = message['generation_request_id']
    
    # Update status to 'processing'
    await update_generation_request(request_id, status='processing', started_at=now())
    
    for i in range(message['count']):
        try:
            # Generate problem
            problem = await generate_problem(...)
            problem.generation_request_id = request_id
            await save_problem(problem)
            
            # Increment generated_count
            await increment_generated_count(request_id)
        except Exception as e:
            # Increment failed_count
            await increment_failed_count(request_id)
            logger.error(f"Failed to generate entity {i+1}: {e}")
    
    # Update final status
    req = await get_generation_request(request_id)
    if req.generated_count == req.requested_count:
        status = 'completed'
    elif req.generated_count > 0:
        status = 'partial'
    else:
        status = 'failed'
    
    await update_generation_request(
        request_id, 
        status=status, 
        completed_at=now()
    )
```

### CLI Commands

New `lqs generation` command group:

```bash
# Get status of generation request
lqs generation get <request-id>

# Future: List generation requests
lqs generation list --status=completed --entity-type=problem
```

### Implementation Phases

#### Phase 1: Core Infrastructure
- [ ] Create `generation_requests` table migration
- [ ] Rename `problems.request_id` → `generation_request_id`
- [ ] Update `QueueService.publish_problem_generation_request()` to create request record
- [ ] Update worker to track status in `generation_requests` table
- [ ] Add `GET /generation-requests/{id}` endpoint

#### Phase 2: CLI Integration
- [ ] Add `lqs generation get` command
- [ ] Update `lqs problems generate` to show request ID and polling instructions

#### Phase 3: Polish
- [ ] Add request count limits (default=1, max=10)
- [ ] Add timeout handling (mark as failed after X minutes)
- [ ] Add retry logic for failed entities
- [ ] Consider dead-letter queue for permanent failures

#### Phase 4: Expand to Other Entities
- [ ] Add to sentences generation
- [ ] Add to future vocabulary generation
- [ ] Create `GET /generation-requests` list endpoint

## Benefits

1. **Transparency:** Users can track long-running generations (20-30s with thinking models)
2. **Reliability:** Can identify and retry failed generations
3. **Debugging:** Full audit trail of generation requests
4. **Scalability:** Generic pattern works for all async LLM operations
5. **User Experience:** Clear status updates instead of "202 and hope for the best"

## Open Questions

1. **Cleanup policy:** How long to keep completed requests? Auto-delete after 7 days?
2. **Pagination:** Should `entities` array be paginated if >100 results? (Not possible with current 10 limit)
3. **Webhooks:** Should we support webhook callbacks when request completes?
4. **Idempotency:** Should we deduplicate identical requests within a time window?

## Future Enhancements

- **Real-time updates:** WebSocket support for live status updates
- **Batch cancellation:** `DELETE /generation-requests/{id}` to cancel in-progress requests
- **Metrics:** Track average generation times, success rates, failure reasons
- **Priority queues:** VIP users get faster processing


