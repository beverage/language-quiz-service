# Fresh Start Migration Plan

**Date:** October 15, 2025  
**Approach:** Complete replacement (not in-place migration)  
**Risk:** None - not in production, sole user

---

## Overview

Since an in-place migration failed, we'll do a **clean slate replacement**:
1. Document existing dashboard structure ✅ (see `dashboard-specification.md`)
2. Remove ALL grafanalib code
3. Rebuild from scratch with grafana-foundation-sdk
4. Match original appearance exactly

---

## Phase 1: Cleanup (Remove Old Code)

### Step 1.1: Remove grafanalib dependency
```bash
cd /Users/alexbeverage/Code/Apps/language-quiz-service
poetry remove grafanalib
```

### Step 1.2: Delete old dashboard code
```bash
# Backup first (just in case)
cp -r src/observability/dashboards /tmp/dashboards-backup-$(date +%Y%m%d)

# Remove old dashboard files
rm -rf src/observability/dashboards

# Create fresh directory
mkdir -p src/observability/dashboards
touch src/observability/dashboards/__init__.py
```

### Step 1.3: Update deploy.py temporarily
Comment out dashboard imports so the project still runs:
```python
# src/observability/deploy.py
# TEMPORARILY comment out:
# from .dashboards import service_overview

# dashboards = {
#     "service_overview": service_overview.generate(),
# }
dashboards = {}  # Empty for now
```

---

## Phase 2: Install grafana-foundation-sdk

### Step 2.1: Add dependency
```bash
poetry add grafana-foundation-sdk
```

### Step 2.2: Verify installation
```bash
python3 -c "from grafana_foundation_sdk.builders import dashboard; print('✅ SDK installed!')"
```

---

## Phase 3: Create Base Utilities

### Step 3.1: Create new base.py
**File:** `src/observability/dashboards/base.py`

```python
"""Base utilities for Grafana dashboards using grafana-foundation-sdk."""

from grafana_foundation_sdk.builders import dashboard
from grafana_foundation_sdk.models.dashboard import (
    DataSourceRef,
    VariableRefresh,
    VariableSort,
)

# Standard settings
DEFAULT_REFRESH = "30s"
DEFAULT_TIME_FROM = "now-1h"
DEFAULT_TIME_TO = "now"


def create_base_dashboard(
    title: str,
    description: str,
    uid: str,
    tags: list[str] | None = None,
    use_environment_filter: bool = True,
) -> dashboard.Dashboard:
    """
    Create a base dashboard with standard configuration.
    
    Args:
        title: Dashboard title
        description: Dashboard description
        uid: Dashboard UID (for updating existing dashboards)
        tags: List of tags for categorization
        use_environment_filter: Whether to include environment template variable
    
    Returns:
        Dashboard builder ready for panels
    """
    tags = tags or []
    
    builder = (
        dashboard.Dashboard(title)
        .description(description)
        .uid(uid)
        .tags(tags)
        .editable()
        .timezone("browser")
        .refresh(DEFAULT_REFRESH)
        .time(DEFAULT_TIME_FROM, DEFAULT_TIME_TO)
        .with_variable(
            dashboard.DatasourceVariable("datasource")
            .label("Datasource")
            .type("prometheus")
            .multi(False)
        )
    )
    
    # Add environment filter if requested
    if use_environment_filter:
        builder = builder.with_variable(
            dashboard.QueryVariable("environment")
            .label("Environment")
            .query("label_values(deployment_environment)")
            .datasource(DataSourceRef(uid="$datasource"))
            .refresh(VariableRefresh.ON_TIME_RANGE_CHANGED)
            .sort(VariableSort.ALPHABETICAL_ASC)
            .multi(False)
        )
    
    return builder
```

---

## Phase 4: Recreate Service Overview Dashboard

### Step 4.1: Create service_overview.py
**File:** `src/observability/dashboards/service_overview.py`

See full implementation in next section.

### Step 4.2: Panel-by-panel checklist

- [ ] Row 1: Summary Stats
  - [ ] Total Requests (Stat)
  - [ ] Avg Latency (Stat)
- [ ] Row 2: Traffic & Errors
  - [ ] Request Rate (TimeSeries)
  - [ ] Error Rate (TimeSeries with thresholds!)
- [ ] Row 3: Latency
  - [ ] Request Latency (TimeSeries, 3 queries)
- [ ] Row 4: Status Codes & Saturation
  - [ ] Status Codes (TimeSeries, stacked)
  - [ ] Active Requests (TimeSeries)
- [ ] Row 5: By Endpoint
  - [ ] Requests by Endpoint (TimeSeries)
  - [ ] p95 Latency by Endpoint (TimeSeries)
- [ ] Row 6: Database Performance
  - [ ] Database Query Duration (TimeSeries)
  - [ ] Database Operations (TimeSeries)

---

## Phase 5: Update Deployment Script

### Step 5.1: Modify deploy.py
```python
# src/observability/deploy.py

# OLD imports (remove these):
# from grafanalib._gen import DashboardEncoder

# NEW imports:
from grafana_foundation_sdk.cog.encoder import JSONEncoder

# Update generate_dashboard_json method:
def generate_dashboard_json(self, dashboard_builder) -> dict:
    """
    Generate JSON from grafana-foundation-sdk dashboard builder.
    
    Args:
        dashboard_builder: grafana-foundation-sdk Dashboard builder
    
    Returns:
        Dashboard JSON dict
    """
    json_str = JSONEncoder(sort_keys=True, indent=2).encode(dashboard_builder.build())
    return json.loads(json_str)

# Re-enable dashboard import:
from .dashboards import service_overview

dashboards = {
    "service_overview": service_overview.generate(),
}
```

---

## Phase 6: Testing & Validation

### Step 6.1: Validate dashboard generation
```bash
make dashboards-validate
```

Expected output:
```
🔍 Validating dashboard definitions...
   ✅ service_overview: Valid
✅ All dashboards valid!
```

### Step 6.2: Export dashboard JSON
```bash
make dashboards-export
```

Check `dashboards/service_overview.json` for correctness.

### Step 6.3: Deploy to local Grafana
```bash
# Start Grafana stack if not running
docker-compose up -d grafana prometheus grafana-agent

# Deploy dashboard
make dashboards-deploy
```

### Step 6.4: Visual verification
1. Open http://localhost:3000
2. Login (username: `lqs`, password: `test`)
3. Navigate to "Language Quiz Service - Overview" dashboard
4. Check all panels:
   - [ ] All 10 panels render
   - [ ] Queries execute without errors
   - [ ] Units display correctly (ms, req/s, %, ops/s)
   - [ ] Legends show correct labels
   - [ ] Thresholds on Error Rate panel (green/yellow/red)
   - [ ] Status Codes panel is stacked
   - [ ] Template variables work (datasource, environment)
   - [ ] Time range controls work
   - [ ] Refresh works

---

## Phase 7: Cleanup & Documentation

### Step 7.1: Remove backup
```bash
# Only after successful deployment and verification
rm -rf /tmp/dashboards-backup-*
```

### Step 7.2: Update README
Update `src/observability/README.md`:
- Change "grafanalib" to "grafana-foundation-sdk"
- Update installation instructions
- Update code examples

### Step 7.3: Commit changes
```bash
git add .
git commit -m "Replace grafanalib with grafana-foundation-sdk

- Remove grafanalib dependency
- Fresh implementation using grafana-foundation-sdk
- Recreated Service Overview dashboard with identical layout
- Fixed threshold support (proper type-safe API)
- All 10 panels working: 2 stats, 8 timeseries
"
```

---

## Rollback Plan

If something goes wrong:

### Option 1: Restore from backup
```bash
# Restore old dashboard code
cp -r /tmp/dashboards-backup-*/dashboards src/observability/

# Restore grafanalib
poetry add grafanalib@^0.7.1

# Revert deploy.py changes
git checkout src/observability/deploy.py
```

### Option 2: Use git
```bash
# Discard all changes
git reset --hard HEAD

# Or revert specific commit
git revert <commit-hash>
```

---

## Success Criteria

✅ **Complete when:**
1. grafanalib removed from dependencies
2. All panels render in Grafana UI
3. Thresholds work on Error Rate panel
4. No errors in dashboard validation
5. No errors in deployment logs
6. Visual appearance matches original
7. Code is cleaner and more maintainable

---

## Estimated Timeline

- **Phase 1 (Cleanup):** 10 minutes
- **Phase 2 (Install SDK):** 5 minutes
- **Phase 3 (Base utilities):** 15 minutes
- **Phase 4 (Dashboard):** 90 minutes (most time here)
- **Phase 5 (Deploy script):** 15 minutes
- **Phase 6 (Testing):** 30 minutes
- **Phase 7 (Cleanup):** 10 minutes

**Total:** ~3 hours (vs. 6-7 hours for in-place migration)

---

## Next Steps

Ready to execute? Let's start with Phase 1:

```bash
cd /Users/alexbeverage/Code/Apps/language-quiz-service
poetry remove grafanalib
```

Then we'll rebuild everything fresh! 🚀
