# Dashboard Specification - Service Overview

**Original Implementation:** grafanalib  
**Target Implementation:** grafana-foundation-sdk  
**Purpose:** Capture exact dashboard structure for fresh rewrite

---

## Dashboard Metadata

- **Title:** Language Quiz Service - Overview
- **Description:** Service health overview with Golden Signals (latency, traffic, errors, saturation)
- **UID:** `lqs-service-overview`
- **Tags:** `language-quiz-service`, `overview`, `golden-signals`
- **Time Range:** Last 1 hour (`now-1h` to `now`)
- **Refresh:** 30 seconds
- **Timezone:** Browser
- **Theme:** Dark
- **Shared Crosshair:** Enabled

---

## Template Variables

### 1. Datasource Variable
- **Name:** `datasource`
- **Label:** Datasource
- **Type:** datasource
- **Query:** prometheus
- **Multi:** false
- **Include All:** false

### 2. Environment Variable
- **Name:** `environment`
- **Label:** Environment
- **Type:** query
- **Query:** `label_values(deployment_environment)`
- **Datasource:** `$datasource`
- **Multi:** false
- **Include All:** false
- **Sort:** Alphabetical (1)

---

## Dashboard Layout

### Row 1: Summary Stats
**Panels:** 2 Stat panels, side by side

#### Panel 1.1: Total Requests (Stat)
- **Position:** Left (span 6)
- **Title:** Total Requests
- **Query:** `sum(increase(http_server_duration_milliseconds_count{deployment_environment="$environment"}[$__range]))`
- **Legend:** Total
- **Unit:** Short (number)
- **Color Mode:** value
- **Graph Mode:** area

#### Panel 1.2: Avg Latency (Stat)
- **Position:** Right (span 6)
- **Title:** Avg Latency
- **Query:** `sum(rate(http_server_duration_milliseconds_sum{deployment_environment="$environment"}[5m])) / sum(rate(http_server_duration_milliseconds_count{deployment_environment="$environment"}[5m]))`
- **Legend:** Avg
- **Unit:** Milliseconds
- **Color Mode:** value
- **Graph Mode:** area

---

### Row 2: Traffic & Errors
**Panels:** 2 Graph/TimeSeries panels, side by side

#### Panel 2.1: Request Rate (Graph)
- **Position:** Left (span 6)
- **Title:** Request Rate
- **Query:** `sum(rate(http_server_duration_milliseconds_count{deployment_environment="$environment"}[5m]))`
- **Legend:** Requests/sec
- **Unit:** Short
- **Y-Axis Label:** req/s
- **Line Width:** 2
- **Fill:** 2

#### Panel 2.2: Error Rate (Graph)
- **Position:** Right (span 6)
- **Title:** Error Rate
- **Query:**
  ```promql
  sum(rate(http_server_duration_milliseconds_count{deployment_environment="$environment", http_status_code=~"5.."}[5m]))
  /
  sum(rate(http_server_duration_milliseconds_count{deployment_environment="$environment"}[5m]))
  * 100
  ```
- **Legend:** Error %
- **Unit:** Percent
- **Y-Axis Label:** %
- **Y-Axis Range:** 0-100
- **Line Width:** 2
- **Fill:** 2
- **Thresholds:**
  - 0: green (base)
  - 1: yellow (warning at 1%)
  - 5: red (critical at 5%)

---

### Row 3: Latency
**Panels:** 1 Graph/TimeSeries panel, full width

#### Panel 3.1: Request Latency (Graph)
- **Position:** Full width (span 12)
- **Title:** Request Latency
- **Queries:**
  - **A (p50):** `histogram_quantile(0.50, sum(rate(http_server_duration_milliseconds_bucket{deployment_environment="$environment"}[5m])) by (le))`
  - **B (p95):** `histogram_quantile(0.95, sum(rate(http_server_duration_milliseconds_bucket{deployment_environment="$environment"}[5m])) by (le))`
  - **C (p99):** `histogram_quantile(0.99, sum(rate(http_server_duration_milliseconds_bucket{deployment_environment="$environment"}[5m])) by (le))`
- **Legends:** p50, p95, p99
- **Unit:** Milliseconds
- **Y-Axis Label:** Duration
- **Line Width:** 2
- **Fill:** 2

---

### Row 4: Status Codes & Saturation
**Panels:** 2 Graph/TimeSeries panels, side by side

#### Panel 4.1: Status Codes (Graph - Stacked)
- **Position:** Left (span 6)
- **Title:** Status Codes
- **Query:** `sum by (http_status_code) (rate(http_server_duration_milliseconds_count{deployment_environment="$environment"}[5m]))`
- **Legend:** `{{http_status_code}}`
- **Unit:** Short
- **Y-Axis Label:** req/s
- **Line Width:** 2
- **Stack:** true
- **Fill:** 5

#### Panel 4.2: Active Requests (Graph)
- **Position:** Right (span 6)
- **Title:** Active Requests
- **Query:** `sum(http_server_active_requests{deployment_environment="$environment"})`
- **Legend:** Active
- **Unit:** Short
- **Y-Axis Label:** Requests
- **Y-Axis Min:** 0
- **Line Width:** 2
- **Fill:** 2

---

### Row 5: By Endpoint
**Panels:** 2 Graph/TimeSeries panels, side by side

#### Panel 5.1: Requests by Endpoint (Graph)
- **Position:** Left (span 6)
- **Title:** Requests by Endpoint
- **Query:** `sum by (http_route) (rate(http_server_duration_milliseconds_count{deployment_environment="$environment"}[5m]))`
- **Legend:** `{{http_route}}`
- **Unit:** Short
- **Y-Axis Label:** req/s
- **Line Width:** 2
- **Fill:** 2

#### Panel 5.2: p95 Latency by Endpoint (Graph)
- **Position:** Right (span 6)
- **Title:** p95 Latency by Endpoint
- **Query:** `histogram_quantile(0.95, sum by (http_route, le) (rate(http_server_duration_milliseconds_bucket{deployment_environment="$environment"}[5m])))`
- **Legend:** `{{http_route}}`
- **Unit:** Seconds
- **Y-Axis Label:** Duration
- **Line Width:** 2
- **Fill:** 2

---

### Row 6: Database Performance
**Panels:** 2 Graph/TimeSeries panels, side by side

#### Panel 6.1: Database Query Duration (Graph)
- **Position:** Left (span 6)
- **Title:** Database Query Duration (p95)
- **Query:** `histogram_quantile(0.95, sum(rate(db_client_operation_duration_bucket{deployment_environment="$environment"}[5m])) by (le))`
- **Legend:** p95
- **Unit:** Seconds
- **Y-Axis Label:** Duration
- **Y-Axis Min:** 0
- **Line Width:** 2
- **Fill:** 2

#### Panel 6.2: Database Operations (Graph)
- **Position:** Right (span 6)
- **Title:** Database Operations
- **Query:** `sum(rate(db_client_operation_duration_count{deployment_environment="$environment"}[5m]))`
- **Legend:** ops/sec
- **Unit:** Short
- **Y-Axis Label:** ops/s
- **Y-Axis Min:** 0
- **Line Width:** 2
- **Fill:** 2

---

## Panel Styling Defaults

All Graph/TimeSeries panels:
- **Line Width:** 2
- **Fill Opacity:** 2 (or 5 for stacked)
- **Datasource:** `$datasource`

All panels:
- **Datasource:** `$datasource` (variable reference)
- **Editable:** true

---

## Metrics Summary

### HTTP Server Metrics (FastAPI)
- `http_server_duration_milliseconds_count` - Request counter
- `http_server_duration_milliseconds_sum` - Request duration sum
- `http_server_duration_milliseconds_bucket` - Request duration histogram
- `http_server_active_requests` - Current active requests

**Labels:**
- `deployment_environment` - Environment filter
- `http_status_code` - HTTP status code (200, 404, 500, etc.)
- `http_route` - Route template

### Database Metrics (AsyncPG)
- `db_client_operation_duration_count` - Query counter
- `db_client_operation_duration_bucket` - Query duration histogram

**Labels:**
- `deployment_environment` - Environment filter

---

## Total Panel Count

- **2 Stat panels** (summary stats)
- **8 Graph/TimeSeries panels** (time-series visualizations)
- **6 Rows** (organizing panels)
- **2 Template variables** (datasource, environment)

---

## Special Features

1. **Error Rate Threshold** - Only panel with thresholds:
   - Green: < 1%
   - Yellow: 1-5%
   - Red: > 5%

2. **Stacked Graph** - Status Codes panel is stacked (fill=5)

3. **Multi-Query Panel** - Request Latency has 3 queries (p50, p95, p99)

4. **Legend Templates** - Several panels use template variables in legends:
   - `{{http_status_code}}`
   - `{{http_route}}`

---

This specification captures all the details needed to recreate the dashboard exactly using grafana-foundation-sdk.
