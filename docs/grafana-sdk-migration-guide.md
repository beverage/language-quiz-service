# Grafana Foundation SDK Migration Guide

**Quick Reference** for migrating from grafanalib to grafana-foundation-sdk

## Quick Start

```bash
# 1. Install the SDK
poetry add grafana-foundation-sdk

# 2. Create a test branch
git checkout -b feature/grafana-foundation-sdk-migration

# 3. Run validation to ensure current dashboards work
make dashboards-validate

# 4. Start migration!
```

## Common Patterns Cheat Sheet

### Import Statements

```python
# OLD (grafanalib)
from grafanalib.core import (
    Dashboard,
    Graph,
    Row,
    Stat,
    Target,
    Template,
    Templating,
    YAxes,
    YAxis,
    MILLISECONDS_FORMAT,
)

# NEW (foundation-sdk)
from grafana_foundation_sdk.builders import (
    dashboard,
    timeseries,
    stat,
    prometheus,
)
from grafana_foundation_sdk.models import (
    common,
    units,
)
from grafana_foundation_sdk.models.dashboard import (
    DataSourceRef,
    Threshold,
    ThresholdsMode,
    VariableRefresh,
    VariableSort,
)
```

### Dashboard Creation

```python
# OLD
dashboard = Dashboard(
    title="My Dashboard",
    description="Description",
    tags=["tag1"],
    rows=[row1, row2],
)

# NEW
dashboard_builder = (
    dashboard.Dashboard("My Dashboard")
    .description("Description")
    .uid("my-dashboard-uid")
    .tags(["tag1"])
    .with_row(row1)
    .with_row(row2)
)
```

### Template Variables

```python
# OLD - Datasource Variable
Template(
    name="datasource",
    type="datasource",
    query="prometheus",
)

# NEW - Datasource Variable
dashboard.DatasourceVariable("datasource")
    .label("Data source")
    .type("prometheus")
    .multi(False)

# OLD - Query Variable
Template(
    name="environment",
    query="label_values(deployment_environment)",
    dataSource="$datasource",
    type="query",
)

# NEW - Query Variable
dashboard.QueryVariable("environment")
    .label("Environment")
    .query("label_values(deployment_environment)")
    .datasource(DataSourceRef(uid="$datasource"))
    .refresh(VariableRefresh.ON_TIME_RANGE_CHANGED)
    .sort(VariableSort.ALPHABETICAL_ASC)
```

### Panel Types

#### TimeSeries (formerly Graph)

```python
# OLD
Graph(
    title="Request Rate",
    dataSource="$datasource",
    targets=[
        Target(
            expr='sum(rate(http_requests[5m]))',
            legendFormat="Requests",
            refId="A",
        ),
    ],
    yAxes=YAxes(
        left=YAxis(format=SHORT_FORMAT, label="req/s"),
    ),
    span=6,
)

# NEW
timeseries.Panel()
    .title("Request Rate")
    .datasource(DataSourceRef(uid="$datasource"))
    .unit(units.Short)
    .with_target(
        prometheus.Dataquery()
        .expr('sum(rate(http_requests[5m]))')
        .legend_format("Requests")
        .ref_id("A")
    )
    .span(6)
    .height(8)
```

#### Stat Panel

```python
# OLD
Stat(
    title="Total Requests",
    dataSource="$datasource",
    targets=[
        Target(
            expr='sum(http_requests)',
            refId="A",
        ),
    ],
    format=SHORT_FORMAT,
    span=6,
)

# NEW
stat.Panel()
    .title("Total Requests")
    .datasource(DataSourceRef(uid="$datasource"))
    .unit(units.Short)
    .with_target(
        prometheus.Dataquery()
        .expr('sum(http_requests)')
        .ref_id("A")
    )
    .span(6)
    .height(4)
```

### Thresholds (The Big Win! 🎉)

```python
# OLD - Confusing dictionary syntax
Graph(
    thresholds=[
        {"value": 1, "colorMode": "critical", "op": "gt", "fill": True, "line": True},
        {"value": 5, "colorMode": "critical", "op": "gt", "fill": True, "line": True},
    ],
)

# NEW - Type-safe, clear API
from grafana_foundation_sdk.builders import common as common_builder

timeseries.Panel()
    .thresholds(
        dashboard.ThresholdsConfig()
        .mode(ThresholdsMode.ABSOLUTE)
        .steps([
            Threshold(value=0.0, color="green"),
            Threshold(value=1.0, color="yellow"),
            Threshold(value=5.0, color="red"),
        ])
    )
    .thresholds_style(
        common_builder.GraphThresholdsStyleConfig()
        .mode(common.GraphThresholdsStyleMode.LINE)
    )
```

### Rows

```python
# OLD
Row(panels=[panel1, panel2])

# NEW
dashboard.Row("Row Title")
    .with_panel(panel1)
    .with_panel(panel2)
```

### Units (Format)

```python
# OLD
from grafanalib.core import (
    SHORT_FORMAT,
    MILLISECONDS_FORMAT,
    SECONDS_FORMAT,
    PERCENT_FORMAT,
)

yAxes=YAxes(left=YAxis(format=SHORT_FORMAT))

# NEW
from grafana_foundation_sdk.models import units

.unit(units.Short)        # req/s, ops/s, etc.
.unit(units.Milliseconds) # ms
.unit(units.Seconds)      # s
.unit(units.Percent)      # %
```

### Deployment Changes

```python
# OLD - Generate JSON
from grafanalib._gen import DashboardEncoder
json_data = json.dumps(dashboard.to_json_data(), cls=DashboardEncoder)

# NEW - Generate JSON
from grafana_foundation_sdk.cog.encoder import JSONEncoder
dashboard_builder = service_overview.generate()
json_data = JSONEncoder(sort_keys=True, indent=2).encode(dashboard_builder.build())
```

## Step-by-Step Migration

### 1. Update `base.py`

Create new base utilities alongside old ones:

```python
# src/observability/dashboards/base_sdk.py
"""Base utilities for grafana-foundation-sdk dashboards."""

from grafana_foundation_sdk.builders import dashboard
from grafana_foundation_sdk.models.dashboard import (
    DataSourceRef,
    VariableRefresh,
    VariableSort,
)

COLORS = {
    "green": "green",
    "yellow": "yellow",
    "orange": "orange",
    "red": "red",
    "blue": "blue",
    "purple": "purple",
}

def create_base_dashboard(
    title: str,
    description: str,
    uid: str,
    tags: list[str] | None = None,
    use_environment_filter: bool = True,
) -> dashboard.Dashboard:
    """Create a base dashboard with standard configuration."""
    tags = tags or []
    
    builder = (
        dashboard.Dashboard(title)
        .description(description)
        .uid(uid)
        .tags(tags)
        .editable()
        .timezone("browser")
        .refresh("30s")
        .time("now-1h", "now")
        # Datasource variable
        .with_variable(
            dashboard.DatasourceVariable("datasource")
            .label("Datasource")
            .type("prometheus")
            .multi(False)
        )
    )
    
    # Optionally add environment filter
    if use_environment_filter:
        builder = builder.with_variable(
            dashboard.QueryVariable("environment")
            .label("Environment")
            .query("label_values(deployment_environment)")
            .datasource(DataSourceRef(uid="$datasource"))
            .refresh(VariableRefresh.ON_TIME_RANGE_CHANGED)
            .sort(VariableSort.ALPHABETICAL_ASC)
        )
    
    return builder
```

### 2. Migrate One Panel at a Time

Start with a simple panel (e.g., request rate):

```python
# src/observability/dashboards/service_overview_sdk.py
"""Service Overview Dashboard using grafana-foundation-sdk."""

from grafana_foundation_sdk.builders import timeseries, stat, prometheus
from grafana_foundation_sdk.models import common, units
from grafana_foundation_sdk.models.dashboard import DataSourceRef

from .base_sdk import create_base_dashboard

def create_request_rate_panel() -> timeseries.Panel:
    """Request rate (requests per second)."""
    return (
        timeseries.Panel()
        .title("Request Rate")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr('sum(rate(http_server_duration_milliseconds_count{deployment_environment="$environment"}[5m]))')
            .legend_format("Requests/sec")
            .ref_id("A")
        )
        .span(6)
        .height(8)
    )

# Test it!
def generate():
    """Generate the Service Overview dashboard."""
    return (
        create_base_dashboard(
            title="Language Quiz Service - Overview (SDK)",
            description="Service health overview with Golden Signals (using foundation-sdk)",
            uid="lqs-service-overview-sdk",
            tags=["language-quiz-service", "overview", "foundation-sdk"],
            use_environment_filter=True,
        )
        .with_row(
            dashboard.Row("Traffic")
            .with_panel(create_request_rate_panel())
        )
    )
```

### 3. Test Locally

```bash
# Add to deploy.py temporarily
dashboards = {
    "service_overview": service_overview.generate(),  # OLD
    "service_overview_sdk": service_overview_sdk.generate(),  # NEW
}

# Deploy both
make dashboards-deploy

# Compare in Grafana UI at http://localhost:3000
```

### 4. Migrate Remaining Panels

Continue panel by panel:
- ✅ Request Rate
- ✅ Error Rate (with thresholds!)
- ✅ Latency
- ✅ Status Codes
- ✅ Active Requests
- etc.

### 5. Switch Over

Once all panels are migrated and tested:

```python
# In deploy.py
dashboards = {
    "service_overview": service_overview_sdk.generate(),  # NEW
}

# Remove old files
# rm src/observability/dashboards/base.py
# rm src/observability/dashboards/service_overview.py
# mv src/observability/dashboards/base_sdk.py src/observability/dashboards/base.py
# mv src/observability/dashboards/service_overview_sdk.py src/observability/dashboards/service_overview.py
```

### 6. Update Dependencies

```bash
# Remove grafanalib
poetry remove grafanalib

# Commit changes
git add .
git commit -m "Migrate to grafana-foundation-sdk"
```

## Troubleshooting

### Issue: Import errors

```python
# Make sure you have the right imports
from grafana_foundation_sdk.builders import dashboard, timeseries, stat, prometheus
from grafana_foundation_sdk.models import common, units
from grafana_foundation_sdk.models.dashboard import DataSourceRef, Threshold
```

### Issue: Panel not showing in dashboard

```python
# Make sure you're calling .build() on the dashboard
dashboard_builder = service_overview.generate()
dashboard_json = JSONEncoder().encode(dashboard_builder.build())  # <-- .build() is required
```

### Issue: Thresholds not working

```python
# Correct threshold configuration
from grafana_foundation_sdk.builders import dashboard, common as common_builder
from grafana_foundation_sdk.models.dashboard import Threshold, ThresholdsMode
from grafana_foundation_sdk.models import common

panel.thresholds(
    dashboard.ThresholdsConfig()
    .mode(ThresholdsMode.ABSOLUTE)  # Use enum, not string
    .steps([
        Threshold(value=0.0, color="green"),  # Must have base threshold at 0
        Threshold(value=1.0, color="yellow"),
    ])
)
```

### Issue: "Builder" type errors

The SDK uses a builder pattern. Methods return `Self`, so you can chain:

```python
# ✅ GOOD - Chained
panel = (
    timeseries.Panel()
    .title("Test")
    .unit(units.Short)
    .with_target(...)
)

# ❌ BAD - Not chained
panel = timeseries.Panel()
panel.title("Test")  # This won't work
```

## Testing Checklist

- [ ] Dashboard deploys without errors
- [ ] All panels render correctly
- [ ] Thresholds display with correct colors
- [ ] Template variables work (datasource, environment)
- [ ] Queries return data
- [ ] Time range controls work
- [ ] Refresh works
- [ ] Panel tooltips show
- [ ] Legends display correctly
- [ ] Units display correctly (ms, %, req/s, etc.)

## Migration Validation

### Visual Comparison Script

```bash
#!/bin/bash
# Compare old vs new dashboard JSON

# Export old dashboard
make dashboards-export
mv dashboards/service_overview.json dashboards/service_overview_old.json

# Migrate and export new dashboard
# ... do migration ...
make dashboards-export
mv dashboards/service_overview.json dashboards/service_overview_new.json

# Compare (ignoring version/timestamp fields)
jq 'del(.version, .id, .time)' dashboards/service_overview_old.json > /tmp/old.json
jq 'del(.version, .id, .time)' dashboards/service_overview_new.json > /tmp/new.json
diff -u /tmp/old.json /tmp/new.json
```

## Need Help?

- **SDK Examples:** https://github.com/grafana/grafana-foundation-sdk/tree/main/examples/python
- **SDK Issues:** https://github.com/grafana/grafana-foundation-sdk/issues
- **Grafana Docs:** https://grafana.com/docs/

## Quick Reference: Panel Builder Methods

```python
# Common methods available on most panels
.title(str)                          # Panel title
.description(str)                    # Panel description
.datasource(DataSourceRef)           # Data source
.unit(units.*)                       # Y-axis unit
.min(float)                          # Y-axis minimum
.max(float)                          # Y-axis maximum
.span(int)                           # Panel width (1-12)
.height(int)                         # Panel height
.with_target(Dataquery)              # Add query target
.thresholds(ThresholdsConfig)        # Threshold values
.thresholds_style(GraphThresholdsStyleConfig)  # Threshold display
.legend(VizLegendOptions)            # Legend configuration
.tooltip(VizTooltipOptions)          # Tooltip configuration
```

---

Good luck with the migration! 🚀
