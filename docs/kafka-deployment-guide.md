# Kafka Deployment Guide

## Overview

Kafka is deployed separately from the main application as critical infrastructure. This guide covers deployment methods and best practices.

## Why Separate Deployment?

- **Different Lifecycles**: App deploys frequently, Kafka rarely changes
- **Risk Management**: Kafka changes affect all services
- **Intentional Control**: Manual deployment prevents accidental changes
- **Production Safety**: Requires explicit confirmation for production

## Deployment Methods

### 1. Makefile (Recommended for Local)

```bash
# Deploy to staging
make kafka-deploy ENV=staging

# Deploy to production (includes safety prompt)
make kafka-deploy ENV=production
```

**Features**:
- ✅ Interactive confirmation for production
- ✅ Quick and simple
- ✅ Documented in `make help`

### 2. GitHub Actions (Recommended for Teams)

1. Navigate to **Actions** → **Deploy Kafka**
2. Click **Run workflow**
3. Select environment: `staging` or `production`
4. For production: Type `yes` in confirmation field
5. Click **Run workflow**

**Features**:
- ✅ Audit trail in GitHub
- ✅ Team visibility
- ✅ Environment protection rules
- ✅ No local Flyctl setup needed

### 3. Direct Flyctl (Advanced)

```bash
flyctl deploy \
  --config infra/kafka/fly.staging.toml \
  --app language-quiz-kafka-staging \
  --ha=false
```

## Management Commands

### Status & Logs

```bash
# Check Kafka status
make kafka-status ENV=staging

# View real-time logs
make kafka-logs ENV=staging

# SSH into instance
make kafka-ssh ENV=staging
```

### Inside Kafka Container

Once SSH'd in:

```bash
# Check broker status
/opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server kafka:9092

# List topics
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list

# View topic details
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --describe --topic problem-generation-requests

# Check consumer groups
/opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server kafka:9092 --list

# View consumer lag
/opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --group problem-generator-workers
```

## When to Deploy Kafka

### Deploy When:
- ✅ Initial setup (first time)
- ✅ Configuration changes (retention, replication)
- ✅ Kafka version updates
- ✅ Resource changes (memory, CPU)

### Don't Deploy When:
- ❌ Worker code changes (deploy app instead)
- ❌ Topic schema changes (topics auto-create)
- ❌ Application logic changes

## Production Deployment Checklist

Before deploying to production:

- [ ] Test changes in staging first
- [ ] Verify staging Kafka is stable
- [ ] Review configuration changes
- [ ] Notify team of deployment window
- [ ] Have rollback plan ready
- [ ] Monitor after deployment

## Troubleshooting

### Deployment Fails

```bash
# Check app exists
flyctl apps list | grep kafka

# Verify volume exists
flyctl volumes list --app language-quiz-kafka-staging

# Check Dockerfile builds locally
docker build -f infra/kafka/Dockerfile -t test-kafka .
```

### Kafka Not Reachable from App

```bash
# Verify internal DNS
flyctl ssh console --app language-quiz-app-staging -C "nslookup language-quiz-kafka-staging.internal"

# Check Kafka is listening
make kafka-ssh ENV=staging
# Inside: netstat -tlnp | grep 9092
```

### Consumer Not Connecting

```bash
# Check worker logs in app
flyctl logs --app language-quiz-app-staging | grep -i kafka

# Check Kafka logs
make kafka-logs ENV=staging
```

## Architecture

```
┌─────────────────────────────────────┐
│   language-quiz-app-staging         │
│   (FastAPI + Worker)                │
│                                     │
│   - Reads: Supabase                 │
│   - Writes: Kafka messages          │
│   - Consumes: Kafka messages        │
└─────────────────────────────────────┘
              │
              │ Internal network
              │ (Fly.io .internal DNS)
              ▼
┌─────────────────────────────────────┐
│   language-quiz-kafka-staging       │
│   (Kafka KRaft - Single Node)      │
│                                     │
│   - Broker on :9092                 │
│   - Controller on :9093             │
│   - Persistent volume               │
└─────────────────────────────────────┘
```

## Cost Monitoring

Kafka runs continuously and costs approximately:
- **Compute**: ~$8/month (1GB RAM, shared CPU)
- **Storage**: ~$1.50/month (10GB volume)
- **Total**: ~$10/month per environment

Monitor costs:
```bash
flyctl billing --app language-quiz-kafka-staging
```

## References

- **Kafka README**: `infra/kafka/README.md`
- **Fly.io Config**: `infra/kafka/fly.staging.toml`
- **Makefile**: `Makefile` (search for "Kafka")
- **GitHub Workflow**: `.github/workflows/deploy-kafka.yml`

