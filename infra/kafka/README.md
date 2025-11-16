# Kafka Deployment on Fly.io

This directory contains the configuration for deploying a single-node Kafka instance on Fly.io using KRaft mode (no Zookeeper required).

## Architecture

- **Mode**: KRaft (Kafka Raft) - Zookeeper-free Kafka
- **Nodes**: Single instance (combined broker + controller)
- **Replication**: Factor of 1 (single instance)
- **Networking**: Fly.io internal network only (not exposed publicly)

## Deployment

### Initial Setup

1. **Create the Fly app** (one-time):

```bash
# Staging
flyctl apps create language-quiz-kafka-staging --org personal

# Production
flyctl apps create language-quiz-kafka-production --org personal
```

2. **Create persistent volume** (one-time):

```bash
# Staging
flyctl volumes create kafka_data --region ams --size 10 --app language-quiz-kafka-staging

# Production
flyctl volumes create kafka_data --region ams --size 20 --app language-quiz-kafka-production
```

### Deploy Kafka

**Option 1: Using Makefile** (Recommended for local deployment)

```bash
# Staging
make kafka-deploy ENV=staging

# Production (includes safety confirmation)
make kafka-deploy ENV=production
```

**Option 2: Using GitHub Actions** (Recommended for team deployments)

1. Go to GitHub Actions → "Deploy Kafka"
2. Click "Run workflow"
3. Select environment (staging/production)
4. For production, type "yes" in the confirmation field
5. Click "Run workflow"

**Option 3: Direct Flyctl** (Manual deployment)

```bash
# Staging
flyctl deploy --config infra/kafka/fly.staging.toml --app language-quiz-kafka-staging --ha=false

# Production (create fly.production.toml from fly.staging.toml first)
flyctl deploy --config infra/kafka/fly.production.toml --app language-quiz-kafka-production --ha=false
```

**Important**: Always use `--ha=false` to ensure single-instance deployment.

### Connect from Main Service

Update your main service's `fly.toml`:

```toml
[env]
  KAFKA_BOOTSTRAP_SERVERS = "language-quiz-kafka-staging.internal:9092"
  WORKER_COUNT = "2"  # Number of concurrent Kafka consumers (max 10)
```

Fly.io's internal DNS will resolve `language-quiz-kafka-staging.internal` to the Kafka instance.

## Monitoring

### Using Makefile (Quick access)

```bash
# Check status
make kafka-status ENV=staging

# View logs
make kafka-logs ENV=staging

# SSH into instance
make kafka-ssh ENV=staging
```

### Manual Commands

```bash
# View logs
flyctl logs --app language-quiz-kafka-staging

# SSH into Kafka instance
flyctl ssh console --app language-quiz-kafka-staging

# Inside container, check broker status
/opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server kafka:9092

# List topics
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list

# Check consumer groups
/opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server kafka:9092 --list
```

### Metrics

Kafka exposes JMX metrics on port 9999 (not exposed externally). For production monitoring, consider:
- Prometheus JMX Exporter
- Kafka Manager / AKHQ
- Grafana dashboards

## Topic Management

Topics are managed using a **database migration pattern** with declarative YAML definitions.

### Current Topics

- `problem-generation-requests`: Job queue for problem generation (10 partitions, 1 replication factor)

### Topic Migration Pattern

Topic configurations are stored as YAML files in `infra/kafka/topics/` and applied automatically during deployment.

**Example topic definition** (`topics/problem-generation-requests.yaml`):
```yaml
name: problem-generation-requests
partitions: 10
replication_factor: 1
config:
  retention.ms: "604800000"  # 7 days
  compression.type: "lz4"
```

### Applying Topic Migrations

**Local (docker-compose):**
Topic migrations run automatically via the `kafka-init` service when you start the stack:
```bash
docker compose up
```

The `kafka-init` service runs once per `docker compose up` and:
- Creates topics if they don't exist
- Increases partition count if needed (safe operation)
- Validates configuration

**Production (Fly.io):**
Run migrations manually after deploying Kafka:
```bash
flyctl ssh console -a language-quiz-kafka-staging -C \
  "/opt/kafka/migration-scripts/init-topics.sh localhost:9092 /opt/kafka/topics"
```

### Adding New Topics

1. Create YAML file in `infra/kafka/topics/`:
   ```yaml
   name: my-new-topic
   partitions: 5
   replication_factor: 1
   config:
     retention.ms: "86400000"  # 1 day
   ```

2. Migrations run automatically on next deployment

### Partition Management

**Important**: Partitions determine max parallel consumers. For `problem-generation-requests`:
- 10 partitions = max 10 concurrent workers
- Adding partitions is safe and automatic
- Reducing partitions requires topic recreation (data loss)

### Verification

List all topics:
```bash
# Local
docker exec kafka-local /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list

# Fly.io
flyctl ssh console -a language-quiz-kafka-staging -C \
  "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list"
```

Describe a topic:
```bash
# Local
docker exec kafka-local /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka:9092 \
  --describe --topic problem-generation-requests

# Fly.io
flyctl ssh console -a language-quiz-kafka-staging -C \
  "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 \
  --describe --topic problem-generation-requests"
```

## Scaling Workers

The main service supports configurable concurrent Kafka consumers via `WORKER_COUNT`:

**Local (docker-compose.yml):**
```yaml
environment:
  - WORKER_COUNT=2  # Run 2 concurrent workers
```

**Production (fly.toml):**
```toml
[env]
  WORKER_COUNT = "5"  # Run 5 concurrent workers
```

### Worker-to-Partition Relationship

All workers join the same consumer group (`problem-generator-workers`). Kafka automatically distributes partitions:

| Partitions | Workers | Partitions per Worker | Notes |
|------------|---------|----------------------|--------|
| 10 | 1 | 10 | One worker handles all partitions |
| 10 | 2 | 5 | Each worker gets 5 partitions |
| 10 | 5 | 2 | Each worker gets 2 partitions |
| 10 | 10 | 1 | Each worker gets 1 partition (max efficiency) |
| 10 | 15 | varies | 5 workers will be **idle** (no partitions) |

**Recommendations:**
- Set `WORKER_COUNT` ≤ partition count to avoid idle workers
- For `problem-generation-requests` (10 partitions): Use 1-10 workers
- Start with 2-3 workers for development, scale up in production as needed
- Monitor Kafka lag to determine if more workers are needed

## Troubleshooting

### Kafka won't start - "lost+found" error

**Error:** `Found directory /var/lib/kafka/data/lost+found, 'lost+found' is not in the form of topic-partition`

**Cause:** Fly.io volumes are ext4 filesystems that automatically create a `lost+found` directory. Kafka scans the log directory and treats it as a malformed topic directory.

**Solution:** We use a subdirectory for Kafka logs (`KAFKA_LOG_DIRS = '/var/lib/kafka/data/kafka-logs'`) so `lost+found` is not scanned.

If you have an existing volume with data in `/var/lib/kafka/data` directly, you need to move it:

```bash
# SSH into Kafka instance
flyctl ssh console -a language-quiz-kafka-staging

# Move existing data to subdirectory (if any exists)
mkdir -p /var/lib/kafka/data/kafka-logs
mv /var/lib/kafka/data/__* /var/lib/kafka/data/kafka-logs/ 2>/dev/null || true
# Don't move lost+found!

# Restart the instance
exit
flyctl apps restart language-quiz-kafka-staging
```

### Kafka won't start - general

1. Check logs: `flyctl logs --app language-quiz-kafka-staging`
2. Verify volume is mounted: `flyctl ssh console -C "ls -la /var/lib/kafka/data"`
3. Check environment variables in Fly.io dashboard
4. Verify `KAFKA_LOG_DIRS` points to `/var/lib/kafka/data/kafka-logs` (not `/var/lib/kafka/data`)

### Can't connect from main service

1. Verify internal DNS: `flyctl ssh console --app language-quiz-app-staging -C "nslookup language-quiz-kafka-staging.internal"`
2. Check Kafka is listening: `flyctl ssh console --app language-quiz-kafka-staging -C "netstat -tlnp | grep 9092"`
3. Test connection: Use the worker logs in the main service

### Reset Kafka completely

**WARNING**: This deletes all messages and topics!

```bash
# Delete and recreate volume
flyctl volumes delete kafka_data --app language-quiz-kafka-staging
flyctl volumes create kafka_data --region ams --size 10 --app language-quiz-kafka-staging

# Redeploy
flyctl deploy --config infra/kafka/fly.toml --app language-quiz-kafka-staging --ha=false
```

## Cost Optimization

Kafka instance costs approximately $20-30/month on Fly.io:
- 1GB RAM, 1 shared CPU: ~$8/month
- 10GB volume: ~$1.50/month
- Data transfer: minimal (internal only)

To reduce costs:
- Use smaller volume if message retention is short
- Consider pausing Kafka when not actively developing (not recommended for production)

## Production Deployment

When ready to deploy to production:

1. **Create production config**:
   ```bash
   cp infra/kafka/fly.staging.toml infra/kafka/fly.production.toml
   ```

2. **Update app name and hostnames** in `fly.production.toml`:
   - Line 6: `app = 'language-quiz-kafka-production'`
   - Line 16: `KAFKA_CONTROLLER_QUORUM_VOTERS = "1@language-quiz-kafka-production.internal:9093"`
   - Line 18: `KAFKA_ADVERTISED_LISTENERS = "PLAINTEXT://language-quiz-kafka-production.internal:9092"`

3. **Generate new CLUSTER_ID**:
   ```bash
   docker run --rm apache/kafka:3.8.0 /opt/kafka/bin/kafka-storage.sh random-uuid
   ```
   Update line 29 with the new UUID.

4. **Deploy**:
   ```bash
   flyctl deploy --config infra/kafka/fly.production.toml --app language-quiz-kafka-production --ha=false
   ```

## Production Considerations

For production, consider:
1. **Larger volume**: 20GB+ for message retention
2. **More memory**: 2GB+ for better throughput
3. **Monitoring**: Add Prometheus JMX exporter
4. **Backups**: Regular volume snapshots
5. **Alerting**: Monitor disk usage, lag, error rates
6. **Topic configuration**: Explicit topic creation with proper retention policies

