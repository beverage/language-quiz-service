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
  ENABLE_WORKER = "true"
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

## Topics

The worker automatically creates topics on first use with default settings:
- `problem-generation-requests`: Job queue for problem generation

## Troubleshooting

### Kafka won't start

1. Check logs: `flyctl logs --app language-quiz-kafka-staging`
2. Verify volume is mounted: `flyctl ssh console -C "ls -la /var/lib/kafka/data"`
3. Check environment variables in Fly.io dashboard

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

