# Observability Setup Guide

This guide walks through setting up and testing the observability stack for the Language Quiz Service.

## 🎯 Overview

The observability stack provides:
- **Metrics**: Service performance, HTTP requests, database queries
- **Dashboards**: Pre-built Grafana dashboards (Infrastructure as Code)
- **Local Testing**: Full observability stack in Docker Compose
- **Cloud Integration**: Seamless deployment to Grafana Cloud

## 🏗️ Architecture

### Local Development Stack
```
Service (FastAPI) → OTLP/HTTP → OTEL Collector → Prometheus (scrapes port 8889) → Grafana
```

Components:
- **OTEL Collector**: Receives OTLP on ports 4317/4318, exposes Prometheus metrics on port 8889
- **Prometheus**: Scrapes OTEL Collector every 10 seconds, stores metrics
- **Grafana**: Queries Prometheus, displays dashboards

### Production Stack
```
Service (FastAPI) → OTLP/HTTPS → Grafana Cloud
Dashboards → Grafana API → Grafana Cloud
```

## 📋 Prerequisites

1. **Docker & Docker Compose** - For local stack
2. **Poetry** - Python dependency management
3. **Grafana Cloud Account** (optional) - For cloud deployment

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
# Install grafanalib and other dependencies
poetry install
```

### 2. Configure Environment

```bash
# Copy example environment file
cp env.example .env

# Edit .env with your credentials
# For local development, the defaults work fine:
GRAFANA_USER=lqs
GRAFANA_PASSWORD=test
GRAFANA_URL=http://localhost:3000
```

### 3. Start the Observability Stack

```bash
# Start all observability services
docker-compose up -d grafana prometheus otel-collector

# Verify services are running
docker-compose ps
```

**Expected Services:**
- `grafana` - http://localhost:3000 (UI)
- `prometheus` - http://localhost:9090 (UI)
- `otel-collector` - ports 4317/4318 (OTLP), 8889 (Prometheus metrics)

### 4. Start the Application

```bash
# Start the application (sends OTLP to otel-collector)
docker-compose up -d app

# Check application logs
docker-compose logs -f app
```

You should see:
```
✅ OpenTelemetry configured (traces + metrics) - sending to http://otel-collector:4318
✅ FastAPI instrumented with OpenTelemetry
```

### 5. Generate Traffic

Generate some traffic to populate metrics:

```bash
# Health check
curl http://localhost:8000/health

# Random verb (requires API key)
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/verbs/random

# Or use a simple loop
for i in {1..100}; do curl http://localhost:8000/health; sleep 0.1; done
```

### 6. Verify Metrics are Being Collected

**Check Prometheus:**
```bash
# Open Prometheus UI
open http://localhost:9090

# Try these queries in the Prometheus UI:
# - http_server_duration_milliseconds_count
# - rate(http_server_duration_milliseconds_count[5m])
# - histogram_quantile(0.95, rate(http_server_duration_milliseconds_bucket[5m]))
```

**Check OTEL Collector:**
```bash
# Check collector is receiving metrics
curl http://localhost:8889/metrics | head -20

# Check collector logs
docker logs otel-collector
```

### 7. Access Grafana

```bash
# Open Grafana
open http://localhost:3000

# Login credentials:
# Username: lqs
# Password: test
```

### 8. Validate Dashboard Definitions

Before deploying, validate that dashboard definitions are correct:

```bash
make dashboards-validate
```

Expected output:
```
🔍 Validating dashboard definitions...
   ✅ service_overview: Valid
✅ All dashboards valid!
```

### 9. Deploy Dashboards to Local Grafana

```bash
make dashboards-deploy
```

Expected output:
```
🚀 Deploying dashboards...
   🌍 Environment: local
   🔗 API URL: http://localhost:3000
   🔌 Testing connection...
   ✅ Connected!

📊 Deploying service_overview...
   ✅ Deployed successfully!
   🔗 URL: http://localhost:3000/d/xxx/language-quiz-service-overview

✨ All dashboards deployed successfully!
```

### 10. View the Dashboard

Navigate to the deployed dashboard URL or:
1. Go to http://localhost:3000
2. Click "Dashboards" in the sidebar
3. Navigate to "Language Quiz Service" folder
4. Open "Language Quiz Service - Overview"

## 📊 Dashboard Panels

The Service Overview dashboard includes:

### Key Metrics (Stats)
- **Uptime (24h)** - Service availability percentage
- **Total Requests** - Request count in time window
- **Avg Latency** - Mean request duration
- **Total Errors** - Error count in time window

### Traffic
- **Request Rate** - Requests per second over time
- **Error Rate** - Percentage of 5xx responses

### Latency
- **Request Latency** - p50, p95, p99 percentiles

### Breakdown
- **Status Codes** - Distribution of HTTP status codes
- **Active Requests** - Current concurrent requests
- **Requests by Endpoint** - Traffic per API route
- **p95 Latency by Endpoint** - Slowest endpoints

### Database
- **Database Query Duration** - p95 query latency
- **Database Operations** - Ops per second

## 🔍 Troubleshooting

### No metrics in Prometheus

**Check OTEL Collector logs:**
```bash
docker logs otel-collector
```

**Verify OTLP endpoint:**
```bash
# Check app environment
docker exec language-quiz-service-local env | grep OTEL

# Should show:
# OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
```

**Restart services:**
```bash
docker-compose restart app otel-collector
```

### Dashboard shows "No Data"

**Verify time range:**
- Check that dashboard time range covers when you generated traffic
- Try "Last 1 hour" or "Last 15 minutes"

**Check PromQL queries:**
1. Open Grafana Explore (compass icon)
2. Select "Prometheus" datasource
3. Try query: `http_server_duration_milliseconds_count`
4. If empty, metrics aren't reaching Prometheus

**Verify metrics exist:**
```bash
# Query Prometheus API directly
curl 'http://localhost:9090/api/v1/query?query=http_server_duration_milliseconds_count'
```

### OTEL Collector not receiving data

**Check collector config:**
```bash
# Verify config is loaded
docker exec otel-collector cat /etc/otelcol-contrib/config.yaml
```

**Check if collector is receiving metrics:**
```bash
# Check internal metrics
curl http://localhost:8888/metrics | grep otelcol_receiver_accepted_metric_points

# If count is increasing, collector is receiving data
```

**Test OTLP endpoint:**
```bash
# Verify ports are exposed
docker port otel-collector
```

### Dashboard deployment fails

**Check Grafana API:**
```bash
# Test authentication
curl -u lqs:test http://localhost:3000/api/health

# List existing dashboards
curl -u lqs:test http://localhost:3000/api/search
```

**Validate definitions first:**
```bash
make dashboards-validate
```

**Check environment variables:**
```bash
# Should be set for local deployment
echo $GRAFANA_USER      # lqs
echo $GRAFANA_PASSWORD  # test
echo $GRAFANA_URL       # http://localhost:3000
```

### Grafana shows "401 Unauthorized"

**Reset Grafana admin password:**
```bash
# Stop Grafana
docker-compose stop grafana

# Remove Grafana data (resets password)
docker volume rm language-quiz-service_grafana-data

# Start again
docker-compose up -d grafana
```

New credentials will be: `lqs` / `test` (from docker-compose.yml)

## 📈 Generating Load for Testing

### Simple Health Check Loop
```bash
# Generate steady traffic
while true; do
  curl -s http://localhost:8000/health > /dev/null
  sleep 0.1
done
```

### Multiple Endpoints
```bash
# Create test-load.sh
cat > test-load.sh << 'EOF'
#!/bin/bash
API_KEY="your-api-key-here"

while true; do
  # Health check
  curl -s http://localhost:8000/health > /dev/null
  
  # Random verb
  curl -s -H "X-API-Key: $API_KEY" \
    http://localhost:8000/api/v1/verbs/random > /dev/null
  
  # Simulate some errors (invalid endpoint)
  curl -s http://localhost:8000/invalid > /dev/null
  
  sleep 0.5
done
EOF

chmod +x test-load.sh
./test-load.sh
```

### Using Apache Bench
```bash
# Install apache bench
brew install apache2  # macOS

# Generate load
ab -n 1000 -c 10 http://localhost:8000/health
```

### Using wrk
```bash
# Install wrk
brew install wrk  # macOS

# Generate load for 30 seconds
wrk -t 4 -c 100 -d 30s http://localhost:8000/health
```

## 🌍 Deploying to Grafana Cloud

### Dashboard Deployment

1. **Get Grafana Cloud API credentials:**
   - Go to https://grafana.com
   - Navigate to your stack  
   - Go to "Administration" → "API Keys"
   - Create a new API key with "Editor" role

2. **Add credentials to .env:**
   ```bash
   GRAFANA_CLOUD_INSTANCE_ID=yourinstance
   GRAFANA_CLOUD_API_KEY=glc_xxx...
   ```

3. **Deploy dashboards:**
   ```bash
   make dashboards-deploy
   ```

The deployment script automatically detects cloud credentials and deploys there.

### Metrics to Cloud (Optional)

To send metrics directly to Grafana Cloud (bypassing local stack):

1. **Get OTLP endpoint:**
   - Go to your Grafana Cloud stack
   - Navigate to "Connections" → "OpenTelemetry"
   - Copy the OTLP endpoint URL

2. **Update .env:**
   ```bash
   OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-XX.grafana.net/otlp
   ```

3. **Restart service:**
   ```bash
   docker-compose restart app
   ```

**Note:** For local development, keep the local stack. Cloud metrics are for production/staging.

### GitHub Actions (CI/CD)

**Add secrets to GitHub:**
1. Go to repository Settings → Secrets and variables → Actions
2. Add secrets:
   - `GRAFANA_CLOUD_INSTANCE_ID`
   - `GRAFANA_CLOUD_API_KEY`

**Automatic deployment:**
- Dashboards are validated on every PR
- Deployed to staging on push to `staging` branch
- Deployed to production on push to `main` branch

## 🧪 Testing Checklist

- [ ] All services start successfully
- [ ] Application logs show OpenTelemetry configured
- [ ] Prometheus shows metrics: `http_server_duration_milliseconds_count`
- [ ] Dashboard definitions validate successfully
- [ ] Dashboard deploys to local Grafana
- [ ] Dashboard visible in Grafana UI
- [ ] All panels show data after generating traffic
- [ ] Environment filter works (local/staging/production)
- [ ] Exported dashboards as JSON
- [ ] Cloud deployment works (if configured)

## 📚 Next Steps

1. **Add Custom Metrics** - Business-specific metrics (verbs, problems, LLM usage)
2. **Additional Dashboards** - API Performance, Database, Business Metrics, Errors
3. **Alerting Rules** - Define alerts for critical metrics
4. **Log Shipping** - Add structured logging with trace correlation
5. **Cost Tracking** - LLM token usage and cost estimation

## 🔗 Useful Links

- **Local Grafana**: http://localhost:3000
- **Local Prometheus**: http://localhost:9090
- **OTEL Collector Metrics**: http://localhost:8889/metrics (app metrics)
- **OTEL Collector Internal**: http://localhost:8888/metrics (collector metrics)
- **Application**: http://localhost:8000

## 💡 Tips

1. **Use environment filter** - Always filter by environment to avoid mixing local/staging/production data
2. **Time ranges matter** - Metrics are only as old as your traffic generation
3. **Refresh dashboards** - Click the refresh button or set auto-refresh
4. **Explore mode** - Use Grafana Explore to test PromQL queries before adding to dashboards
5. **Panel inspect** - Click panel title → Inspect → Query to debug
6. **Export JSON** - Use `make dashboards-export` to backup dashboard definitions

## 🐛 Common Issues

### Issue: "No data" in all panels
**Solution:** Generate traffic and ensure time range covers the traffic period.

### Issue: OTEL Collector shows "connection refused"  
**Solution:** Ensure Prometheus is running: `docker-compose ps prometheus`

### Issue: Dashboard deployment returns 500
**Solution:** Check Grafana logs: `docker logs grafana`

### Issue: Metrics show up in Prometheus but not Grafana
**Solution:** Check datasource configuration: http://localhost:3000/connections/datasources

For more help, see the main [Observability README](../src/observability/README.md).

