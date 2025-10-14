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
    
    # Create datasource variable
    datasource_var = (
        dashboard.DatasourceVariable("datasource")
        .label("Datasource")
        .type("prometheus")
        .regex("")
        .multi(False)
    )
    
    builder = (
        dashboard.Dashboard(title)
        .description(description)
        .uid(uid)
        .tags(tags)
        .editable()
        .timezone("browser")
        .refresh(DEFAULT_REFRESH)
        .time(DEFAULT_TIME_FROM, DEFAULT_TIME_TO)
        .with_variable(datasource_var)
    )
    
    # Add environment filter if requested
    if use_environment_filter:
        query_str = "label_values(deployment_environment)"
        builder = builder.with_variable(
            dashboard.QueryVariable("environment")
            .label("Environment")
            .query(query_str)
            .datasource(DataSourceRef(type_val="prometheus", uid="$datasource"))
            .refresh(VariableRefresh.ON_TIME_RANGE_CHANGED)
            .sort(VariableSort.ALPHABETICAL_ASC)
            .multi(False)
        )
    
    return builder
