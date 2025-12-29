# Async Problem Generation - Phase 1 Implementation

## Overview

Phase 1 implements the foundational infrastructure for async problem generation using Kafka and background workers. This allows the service to decouple problem retrieval from problem generation, improving latency and enabling background job processing.

## What Was Implemented

### 1. Database Schema Updates ✅

**Migration**: `20251110131244_add_problems_last_served_at.sql`

- Added `last_served_at` column to `problems` table
- Added index for efficient querying by last usage time
- Enables LRU (Least Recently Used) problem serving

### 2. Docker Compose Integration ✅

**File**: `docker-compose.yml`

- Added Kafka service using KRaft mode (no Zookeeper required)
- Configured single-node Kafka for local development
- Added health checks and proper networking
- Updated app service to connect to Kafka

**Environment Variables**:
```yaml
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ENABLE_WORKER=true
```

### 3. Worker Infrastructure ✅

**Structure**:
```
src/worker/
├── __init__.py              # Worker lifecycle management
├── config.py                # Worker configuration
├── consumer.py              # Kafka consumer implementation
├── metrics.py               # OpenTelemetry metrics
└── handlers/
    ├── __init__.py
    └── test_handler.py      # Test message handler
```

**Key Features**:
- Async Kafka consumer using `aiokafka`
- Automatic reconnection on errors
- Manual offset commits for reliability
- Configurable via environment variables
- Graceful startup/shutdown

### 4. Service Integration ✅

**File**: `src/main.py`

- Worker starts automatically if `ENABLE_WORKER=true`
- Runs as background asyncio task alongside FastAPI
- Graceful shutdown on service termination
- Non-blocking startup (service continues if worker fails)

### 5. Observability ✅

**Metrics** (`src/worker/metrics.py`):
- `worker.messages.processed` - Counter of successful messages
- `worker.messages.failed` - Counter of failed messages
- `worker.message.processing_duration` - Histogram of processing time
- `worker.queue.length` - Gauge of current queue backlog
- `worker.tasks.active` - Gauge of active worker tasks

**Dashboard** (`src/observability/dashboards/service_overview.py`):

Added "Worker Health" section with:
- Messages Processed/sec (stat)
- Active Worker Tasks (stat)
- Queue Length (stat with thresholds)
- Worker Error Rate (stat with thresholds)
- Processing Duration (timeseries with p50/p95/p99)
- Worker Throughput (timeseries by topic)

### 6. Fly.io Deployment Configuration ✅

**Structure**:
```
infra/kafka/
├── fly.toml         # Kafka app configuration
├── Dockerfile       # KRaft-enabled Kafka image
└── README.md        # Deployment instructions
```

**Features**:
- Single-node Kafka deployment
- Persistent volume for message retention
- Internal-only networking (not exposed publicly)
- Must deploy with `--ha=false` for single instance

### 7. Dependencies ✅

**Added to `pyproject.toml`**:
- `aiokafka = "^0.11.0"` - Async Kafka client

## Testing Phase 1

### Local Development

1. **Start the stack**:
```bash
make compose-up
```

2. **Verify Kafka is running**:
```bash
docker exec kafka-local kafka-topics.sh --bootstrap-server localhost:9092 --list
```

3. **Generate test traffic**:
```bash
# Send 10 test messages
./scripts/test-kafka-traffic.sh 10

# Or manually:
docker exec -it kafka-local /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server kafka:9092 \
  --topic problem-generation-requests
```

Enter a JSON message:
```json
{"test": "hello worker"}
```

4. **Check worker logs**:
```bash
docker logs language-quiz-service-local | grep "worker"
```

You should see:
```
📨 Received test message: {'test': 'hello worker'}
✅ Processed test message successfully
```

### Verify Metrics

1. **Open Grafana**: http://localhost:3000
2. **Navigate to**: Service Overview dashboard
3. **Scroll to**: Worker Health section (bottom)
4. **Generate test traffic**:
   ```bash
   ./scripts/test-kafka-traffic.sh 20
   ```
5. **Check metrics** (should populate within 15-30 seconds):
   - Messages Processed/sec should show activity (~0.3-1.0 ops/sec)
   - Active Worker Tasks should show 0 or 1
   - Queue Length should be 0 (no backlog)
   - Worker Error Rate should be 0%
   - Processing Duration should show ~0.1s
   - Worker Throughput should show activity by topic

**Note**: Metrics export every 15 seconds, so you may need to wait briefly after sending messages.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka connection string |
| `ENABLE_WORKER` | `false` | Enable background worker |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | - | OpenTelemetry endpoint (enables metrics) |

### Kafka Topics

- `problem-generation-requests` - Queue for problem generation jobs

Topic is auto-created on first use with default settings (1 partition, replication factor 1).

## Architecture

```
┌─────────────────────────────────────────┐
│          FastAPI Service                │
│                                         │
│  ┌────────────┐      ┌──────────────┐ │
│  │  API       │      │   Worker     │ │
│  │  Handlers  │      │   (asyncio)  │ │
│  └────────────┘      └──────────────┘ │
│        │                     │         │
│        │                     │         │
└────────┼─────────────────────┼─────────┘
         │                     │
         │                     │
    ┌────▼─────┐          ┌───▼────────┐
    │ Supabase │          │   Kafka    │
    │   DB     │          │  (KRaft)   │
    └──────────┘          └────────────┘
```

**Flow**:
1. FastAPI and Worker start together in same process
2. Worker subscribes to Kafka topic
3. Messages arrive → Worker processes them
4. Metrics are emitted via OpenTelemetry
5. Grafana displays real-time metrics

## Next Steps (Phase 2+)

### Phase 2: Real Problem Generation
- [ ] Create `ProblemGenerationHandler` to replace test handler
- [ ] Update GET `/problems/random` to check pool health
- [ ] Add POST `/problems/generate-bulk` endpoint
- [ ] Implement queue publisher service

### Phase 3: Production Hardening
- [ ] LLM validation in worker
- [ ] Problem pool management (track "fresh" problems)
- [ ] Dead Letter Queue for failed jobs
- [ ] Retry logic with exponential backoff
- [ ] Circuit breaker for external dependencies

### Phase 4: Scaling
- [ ] Multi-worker support (consumer groups)
- [ ] Kafka monitoring (lag, partition health)
- [ ] Auto-scaling based on queue depth
- [ ] Rate limiting for problem generation

## Troubleshooting

### Worker Won't Start

**Check logs**:
```bash
docker logs language-quiz-service-local | grep -i "worker\|kafka"
```

**Common issues**:
- Kafka not ready: Wait for health check to pass
- Wrong env var: Verify `ENABLE_WORKER=true`
- Missing dependency: Run `poetry install`

### No Messages Processing

**Verify topic exists**:
```bash
docker exec kafka-local kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic problem-generation-requests
```

**Check consumer group**:
```bash
docker exec kafka-local kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group problem-generator-workers
```

### Metrics Not Showing

**Check OpenTelemetry**:
- Verify `OTEL_EXPORTER_OTLP_ENDPOINT` is set
- Check OTEL collector logs: `docker logs otel-collector`
- Verify Prometheus scraping: http://localhost:9090/targets

## Files Changed/Created

### Created
- `supabase/migrations/20251110131244_add_problems_last_served_at.sql`
- `src/worker/__init__.py`
- `src/worker/config.py`
- `src/worker/consumer.py`
- `src/worker/metrics.py`
- `src/worker/handlers/__init__.py`
- `src/worker/handlers/test_handler.py`
- `infra/kafka/fly.staging.toml`
- `infra/kafka/Dockerfile`
- `infra/kafka/README.md`
- `docs/async-problem-generation-phase1.md` (this file)
- `docs/kafka-deployment-guide.md`
- `scripts/test-kafka-traffic.sh`
- `tests/worker/test_worker_config.py` (unit tests)
- `tests/worker/test_worker_lifecycle.py` (unit tests)
- `tests/worker/test_worker_metrics.py` (unit tests)
- `tests/acceptance/test_kafka_infrastructure.py` (acceptance tests)

### Modified
- `docker-compose.yml` - Added Kafka service + app-venv volume
- `src/main.py` - Added worker startup/shutdown
- `pyproject.toml` - Added aiokafka and testcontainers[kafka] dependencies
- `src/observability/dashboards/service_overview.py` - Added worker metrics panels
- `tests/acceptance/conftest.py` - Added Kafka testcontainer fixtures
- `Makefile` - Added Kafka deployment targets
- `.github/workflows/deploy-kafka.yml` - Manual Kafka deployment workflow
- `infra/kafka/README.md` - Updated deployment documentation

### Deleted
- `infra/lqs-task.json` - Obsolete ECS configuration
- `infra/README.md` - Obsolete ECS documentation

## Testing

### Unit Tests (Fast - 13 tests, ~1s)

Run with main test suite:
```bash
make test  # ~12s total, includes worker unit tests
```

Tests in `tests/worker/`:
- **Configuration**: Environment variable parsing, defaults
- **Lifecycle**: Worker startup/shutdown, error handling  
- **Metrics**: Counter/histogram/gauge recording

**Coverage**: 81.42% overall, worker module well-covered

### Acceptance Tests (Slower - 4 tests, ~14s)

Run separately or in pre-push/CI:
```bash
pytest -m acceptance tests/acceptance/test_kafka_infrastructure.py
```

Tests in `tests/acceptance/test_kafka_infrastructure.py`:
- **Connection**: Consumer connects to Kafka
- **Message Processing**: End-to-end message flow
- **Offset Commit**: Reliable message processing
- **Error Handling**: Invalid JSON handling

Uses **testcontainers** for real Kafka instance (KRaft mode).

**Why Acceptance?**
- Infrastructure tests (not business logic)
- Expensive container spinup (~10s)
- aiokafka library is well-tested
- Manual E2E verification already done
- Phase 2 will add real business logic tests

## Summary

Phase 1 successfully establishes:
- ✅ Kafka infrastructure (local + Fly.io ready)
- ✅ Worker framework with test handler
- ✅ Full observability (metrics + dashboard)
- ✅ Production-ready deployment config
- ✅ Comprehensive test coverage (unit + acceptance)
- ✅ Fast test suite (~12s for main tests)

**Ready for Phase 2**: Implement real problem generation logic!

