# Testing the Observability Stack

Quick reference guide for testing the dashboard-as-code implementation.

## 🚀 Quick Test (5 minutes)

```bash
# 1. Install dependencies
poetry install

# 2. Start observability stack
docker-compose up -d grafana prometheus otel-collector

# 3. Start application
docker-compose up -d app

# 4. Wait for services to be ready (30 seconds)
sleep 30

# 5. Generate some traffic
for i in {1..100}; do 
  curl -s http://localhost:8000/health > /dev/null
  sleep 0.1
done

# 6. Validate dashboard definitions
make dashboards-validate

# 7. Deploy dashboards to local Grafana
make dashboards-deploy

# 8. Open Grafana and view dashboard
open http://localhost:3000
# Login: lqs / test
```

## ✅ Verification Checklist

### 1. Services Running
```bash
docker-compose ps
```
Expected: All services should be "Up"

### 2. OpenTelemetry Configured
```bash
docker logs language-quiz-service-local | grep -i "opentelemetry\|otel"
```
Expected:
```
✅ OpenTelemetry configured (traces + metrics) - sending to http://otel-collector:4318
✅ FastAPI instrumented with OpenTelemetry
```

### 3. Metrics Reaching Prometheus
```bash
# Check Prometheus has metrics
curl -s 'http://localhost:9090/api/v1/query?query=http_server_duration_milliseconds_count' | jq '.data.result | length'
```
Expected: Number > 0

### 4. OTEL Collector Working
```bash
# Check collector is receiving OTLP
docker logs otel-collector | tail -20
```
Expected: No error messages, should show metrics being processed

### 5. Dashboard Validation
```bash
make dashboards-validate
```
Expected:
```
✅ service_overview: Valid
✅ All dashboards valid!
```

### 6. Dashboard Deployment
```bash
make dashboards-deploy
```
Expected:
```
✅ Deployed successfully!
🔗 URL: http://localhost:3000/d/.../language-quiz-service-overview
```

### 7. Dashboard Visible in Grafana
1. Open http://localhost:3000
2. Login with `lqs` / `test`
3. Navigate to Dashboards → Language Quiz Service
4. Open "Language Quiz Service - Overview"

### 8. Panels Showing Data
After generating traffic, all panels should display data:
- [ ] Uptime stat shows ~100%
- [ ] Total Requests shows count
- [ ] Request Rate graph shows activity
- [ ] Latency graph shows p50/p95/p99
- [ ] Status Codes shows 200s
- [ ] Requests by Endpoint shows /health

## 🧪 Detailed Tests

### Test 1: Basic Metric Collection

```bash
# Generate traffic
curl http://localhost:8000/health

# Check Prometheus
curl -s 'http://localhost:9090/api/v1/query?query=http_server_duration_milliseconds_count' | jq
```

Expected: Metric exists with labels (http_method, http_status_code, etc.)

### Test 2: Rate Calculation

```bash
# Query rate in Prometheus
curl -s 'http://localhost:9090/api/v1/query?query=rate(http_server_duration_milliseconds_count[5m])' | jq
```

Expected: Rate value > 0

### Test 3: Percentile Calculation

```bash
# Query p95 latency
curl -s 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,%20rate(http_server_duration_milliseconds_bucket[5m]))' | jq
```

Expected: Latency value in seconds

### Test 4: Environment Filter

In Grafana dashboard:
1. Use environment dropdown at top
2. Select "local"
3. Verify data still shows
4. Select non-existent environment
5. Verify no data shows

### Test 5: Dashboard Export

```bash
make dashboards-export
ls dashboards/
```

Expected: `service_overview.json` exists and is valid JSON

### Test 6: Cloud Deployment (if credentials configured)

```bash
# Set cloud credentials
export GRAFANA_CLOUD_INSTANCE_ID=yourinstance
export GRAFANA_CLOUD_API_KEY=glc_xxx

# Deploy to cloud
make dashboards-deploy
```

Expected: Dashboard deployed to Grafana Cloud

## 🐛 Troubleshooting

### Metrics not showing
```bash
# Check entire pipeline
echo "1. Checking app is sending OTLP..."
docker logs language-quiz-service-local | grep -i otel

echo "2. Checking OTEL Collector is receiving..."
docker logs otel-collector | tail

echo "3. Checking Prometheus has metrics..."
curl -s http://localhost:9090/api/v1/label/__name__/values | jq '.data[]' | grep http_server

echo "4. Checking Grafana can query Prometheus..."
curl -s -u lqs:test http://localhost:3000/api/health
```

### Dashboard deployment fails
```bash
# Check Grafana is accessible
curl -u lqs:test http://localhost:3000/api/health

# Check definitions are valid
make dashboards-validate

# Check logs
docker logs grafana
```

### No data in panels
```bash
# Verify time range covers data
# Verify environment filter matches
# Generate more traffic
for i in {1..1000}; do curl -s http://localhost:8000/health > /dev/null; done
```

## 📊 Load Testing

### Generate sustained load
```bash
# Install apache bench
brew install apache2  # or apt-get install apache2-utils

# Generate 10,000 requests with 100 concurrent
ab -n 10000 -c 100 http://localhost:8000/health

# Watch metrics in real-time
watch -n 1 'curl -s "http://localhost:9090/api/v1/query?query=rate(http_server_duration_milliseconds_count[1m])" | jq ".data.result[0].value[1]"'
```

### Monitor dashboard during load
1. Open dashboard in Grafana
2. Set auto-refresh to 5s
3. Run load test
4. Watch panels update in real-time

## 🔬 Advanced Testing

### Test Custom Labels
```bash
# Query with label filter
curl -s 'http://localhost:9090/api/v1/query?query=http_server_duration_milliseconds_count{http_route="/health"}' | jq
```

### Test Histogram Buckets
```bash
# Check bucket distribution
curl -s 'http://localhost:9090/api/v1/query?query=http_server_duration_milliseconds_bucket' | jq '.data.result[] | select(.metric.le == "0.1")'
```

### Test Exemplars
```bash
# Query with exemplars (requires recent Prometheus)
curl -s 'http://localhost:9090/api/v1/query_exemplars?query=http_server_duration_milliseconds_bucket&start=2024-01-01T00:00:00Z&end=2024-12-31T23:59:59Z' | jq
```

## 📝 Test Report Template

After testing, document results:

```markdown
## Observability Stack Test Results

**Date:** YYYY-MM-DD
**Tester:** Your Name
**Branch:** branch-name

### Environment
- [ ] Docker Compose services running
- [ ] Application configured with OTLP
- [ ] Grafana accessible
- [ ] Prometheus collecting metrics

### Dashboard Validation
- [ ] Definitions validate successfully
- [ ] Dashboard deploys to local Grafana
- [ ] All panels defined correctly
- [ ] Environment filter works

### Data Flow
- [ ] Metrics reach Prometheus
- [ ] Grafana can query Prometheus
- [ ] Panels show data after traffic generation
- [ ] Real-time updates work (auto-refresh)

### Functionality
- [ ] Request rate panel shows traffic
- [ ] Error rate panel shows 5xx percentage
- [ ] Latency panel shows p50/p95/p99
- [ ] Status codes panel shows distribution
- [ ] Endpoint breakdown shows routes
- [ ] Database panels show query metrics

### Performance
- [ ] Dashboard loads quickly (< 5s)
- [ ] Queries execute fast (< 2s)
- [ ] No query errors
- [ ] Auto-refresh works smoothly

### Issues Found
- None / List issues here

### Screenshots
- Attach screenshots of dashboard with data

### Sign-off
Tested by: ___________  
Date: ___________
```

## 🎯 Success Criteria

Implementation is successful when:
- ✅ All services start and run without errors
- ✅ Metrics flow through: App → Agent → Prometheus → Grafana
- ✅ Dashboard validates and deploys successfully
- ✅ All panels show data after generating traffic
- ✅ Environment filter works correctly
- ✅ Dashboard is readable and useful
- ✅ Documentation is clear and complete
- ✅ Cloud deployment works (if configured)

## 📚 References

- [Main Observability Setup Guide](./observability_setup.md)
- [Observability README](../src/observability/README.md)
- [Prometheus Querying Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/)

