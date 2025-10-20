"""Service Overview Dashboard - Golden Signals and Service Health."""

from grafana_foundation_sdk.builders import (
    common as common_builder,
)
from grafana_foundation_sdk.builders import (
    dashboard,
    prometheus,
    stat,
    timeseries,
)
from grafana_foundation_sdk.models import common, units
from grafana_foundation_sdk.models.dashboard import (
    DataSourceRef,
    GridPos,
    Threshold,
    ThresholdsMode,
)

from .base import create_base_dashboard


def create_uptime_stat() -> stat.Panel:
    """Service uptime."""
    return (
        stat.Panel()
        .title("Uptime")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Seconds)
        .with_target(
            prometheus.Dataquery()
            .expr('time() - process_start_time_seconds{environment="$environment"}')
            .legend_format("Uptime")
            .ref_id("A")
        )
        .color_mode(common.BigValueColorMode.VALUE)
        .graph_mode(common.BigValueGraphMode.AREA)
        .grid_pos(GridPos(x=0, y=0, w=6, h=6))  # x, y, w, h
    )


def create_error_count_stat() -> stat.Panel:
    """Total error count in time window."""
    return (
        stat.Panel()
        .title("Error Count")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum(increase(http_server_duration_milliseconds_count{environment="$environment", http_target!="/", http_status_code=~"5.."}[$__range]))'
            )
            .legend_format("Errors")
            .ref_id("A")
        )
        .color_mode(common.BigValueColorMode.VALUE)
        .graph_mode(common.BigValueGraphMode.AREA)
        .grid_pos(GridPos(x=6, y=0, w=6, h=6))  # x, y, w, h
    )


def create_total_requests_stat() -> stat.Panel:
    """Total requests in time window."""
    return (
        stat.Panel()
        .title("Total Requests")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum(increase(http_server_duration_milliseconds_count{environment="$environment", http_target!="/"}[$__range]))'
            )
            .legend_format("Total")
            .ref_id("A")
        )
        .color_mode(common.BigValueColorMode.VALUE)
        .graph_mode(common.BigValueGraphMode.AREA)
        .grid_pos(GridPos(x=12, y=0, w=6, h=6))  # x, y, w, h
    )


def create_avg_latency_stat() -> stat.Panel:
    """Average request latency."""
    return (
        stat.Panel()
        .title("Avg Latency")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Milliseconds)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum(rate(http_server_duration_milliseconds_sum{environment="$environment", http_target!="/"}[5m])) / sum(rate(http_server_duration_milliseconds_count{environment="$environment", http_target!="/"}[5m]))'
            )
            .legend_format("Avg")
            .ref_id("A")
        )
        .color_mode(common.BigValueColorMode.VALUE)
        .graph_mode(common.BigValueGraphMode.AREA)
        .grid_pos(GridPos(x=18, y=0, w=6, h=6))  # x, y, w, h
    )


def create_request_rate_panel() -> timeseries.Panel:
    """Request rate (requests per second)."""
    return (
        timeseries.Panel()
        .title("Request Rate")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum(rate(http_server_duration_milliseconds_count{environment="$environment", http_target!="/"}[5m]))'
            )
            .legend_format("Requests/sec")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(10)
        .grid_pos(GridPos(x=0, y=6, w=12, h=8))  # x, y, w, h
    )


def create_error_rate_panel() -> timeseries.Panel:
    """Error rate (percentage of 5xx responses)."""
    return (
        timeseries.Panel()
        .title("Error Rate")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Percent)
        .min(0)
        .max(100)
        .with_target(
            prometheus.Dataquery()
            .expr("""sum(rate(http_server_duration_milliseconds_count{environment="$environment", http_target!="/", http_status_code=~"5.."}[5m]))
/
sum(rate(http_server_duration_milliseconds_count{environment="$environment", http_target!="/"}[5m]))
* 100""")
            .legend_format("Error %")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(10)
        # Thresholds - the main feature we wanted!
        .thresholds(
            dashboard.ThresholdsConfig()
            .mode(ThresholdsMode.ABSOLUTE)
            .steps(
                [
                    Threshold(value=0.0, color="green"),
                    Threshold(value=1.0, color="yellow"),
                    Threshold(value=5.0, color="red"),
                ]
            )
        )
        .grid_pos(GridPos(x=12, y=6, w=12, h=8))  # x, y, w, h
    )


def create_latency_panel() -> timeseries.Panel:
    """Request latency percentiles (aggregate)."""
    return (
        timeseries.Panel()
        .title("Request Latency")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Milliseconds)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'histogram_quantile(0.50, sum(rate(http_server_duration_milliseconds_bucket{environment="$environment", http_target!="/"}[5m])) by (le))'
            )
            .legend_format("p50")
            .ref_id("A")
        )
        .with_target(
            prometheus.Dataquery()
            .expr(
                'histogram_quantile(0.95, sum(rate(http_server_duration_milliseconds_bucket{environment="$environment", http_target!="/"}[5m])) by (le))'
            )
            .legend_format("p95")
            .ref_id("B")
        )
        .with_target(
            prometheus.Dataquery()
            .expr(
                'histogram_quantile(0.99, sum(rate(http_server_duration_milliseconds_bucket{environment="$environment", http_target!="/"}[5m])) by (le))'
            )
            .legend_format("p99")
            .ref_id("C")
        )
        .line_width(2)
        .fill_opacity(10)
        .grid_pos(GridPos(x=0, y=14, w=24, h=8))  # x, y, w, h - full width
    )


def create_p90_latency_by_endpoint_panel() -> timeseries.Panel:
    """p90 latency by endpoint."""
    return (
        timeseries.Panel()
        .title("p90 Latency by Endpoint")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Milliseconds)
        .min(0)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'histogram_quantile(0.90, sum by (http_target, le) (rate(http_server_duration_milliseconds_bucket{environment="$environment", http_target!="/"}[5m])))'
            )
            .legend_format("{{http_target}}")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(10)
        .grid_pos(GridPos(x=0, y=30, w=12, h=8))  # x, y, w, h - left
    )


def create_status_code_panel() -> timeseries.Panel:
    """HTTP status code distribution (stacked)."""
    return (
        timeseries.Panel()
        .title("Status Codes")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum by (http_status_code) (rate(http_server_duration_milliseconds_count{environment="$environment", http_target!="/"}[5m]))'
            )
            .legend_format("{{http_status_code}}")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(50)  # Higher fill for stacked
        .stacking(common_builder.StackingConfig().mode(common.StackingMode.NORMAL))
        .grid_pos(GridPos(x=0, y=38, w=12, h=8))  # x, y, w, h - left below
    )


def create_p50_latency_by_endpoint_panel() -> timeseries.Panel:
    """p50 (median) latency by endpoint."""
    return (
        timeseries.Panel()
        .title("p50 Latency by Endpoint")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Milliseconds)
        .min(0)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'histogram_quantile(0.50, sum by (http_target, le) (rate(http_server_duration_milliseconds_bucket{environment="$environment", http_target!="/"}[5m])))'
            )
            .legend_format("{{http_target}}")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(10)
        .grid_pos(GridPos(x=0, y=22, w=24, h=8))  # x, y, w, h - full width
    )


def create_request_by_endpoint_panel() -> timeseries.Panel:
    """Request rate by endpoint."""
    return (
        timeseries.Panel()
        .title("Requests by Endpoint")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum by (http_target) (rate(http_server_duration_milliseconds_count{environment="$environment", http_target!="/"}[5m]))'
            )
            .legend_format("{{http_target}}")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(10)
        .grid_pos(GridPos(x=12, y=38, w=12, h=8))  # x, y, w, h - right
    )


def create_p95_latency_by_endpoint_panel() -> timeseries.Panel:
    """p95 latency by endpoint."""
    return (
        timeseries.Panel()
        .title("p95 Latency by Endpoint")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Milliseconds)
        .min(0)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'histogram_quantile(0.95, sum by (http_target, le) (rate(http_server_duration_milliseconds_bucket{environment="$environment", http_target!="/"}[5m])))'
            )
            .legend_format("{{http_target}}")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(10)
        .grid_pos(GridPos(x=12, y=30, w=12, h=8))  # x, y, w, h - right
    )


def create_db_query_duration_panel() -> timeseries.Panel:
    """Database query duration."""
    return (
        timeseries.Panel()
        .title("Database Query Duration (p95)")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Seconds)
        .min(0)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'histogram_quantile(0.95, sum(rate(db_client_operation_duration_bucket{environment="$environment"}[5m])) by (le))'
            )
            .legend_format("p95")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(10)
        .grid_pos(GridPos(x=0, y=46, w=12, h=8))  # x, y, w, h
    )


def create_db_operations_panel() -> timeseries.Panel:
    """Database operations per second."""
    return (
        timeseries.Panel()
        .title("Database Operations")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .min(0)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum(rate(db_client_operation_duration_count{environment="$environment"}[5m]))'
            )
            .legend_format("ops/sec")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(10)
        .grid_pos(GridPos(x=12, y=46, w=12, h=8))  # x, y, w, h
    )


# ============================================================================
# Production Safety Panels
# ============================================================================


def create_quiz_requests_per_minute() -> timeseries.Panel:
    """Quiz generation requests per minute (proxy for website usage)."""
    return (
        timeseries.Panel()
        .title("Quiz Requests per Minute")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum(rate(http_server_duration_milliseconds_count{environment="$environment", http_target=~"/api/v1/problems.*"}[1m])) * 60'
            )
            .legend_format("Requests/min")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(10)
        .grid_pos(GridPos(x=0, y=54, w=12, h=8))
    )


def create_rate_limit_violations() -> stat.Panel:
    """Rate limit violations (429 responses) - indicates we're throttling our own website."""
    return (
        stat.Panel()
        .title("Rate Limit Hits (Website Throttled)")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum(increase(http_server_duration_milliseconds_count{environment="$environment", http_status_code="429"}[1h]))'
            )
            .legend_format("429s/hour")
            .ref_id("A")
        )
        .color_mode(common.BigValueColorMode.VALUE)
        .graph_mode(common.BigValueGraphMode.AREA)
        .thresholds(
            dashboard.ThresholdsConfig()
            .mode(ThresholdsMode.ABSOLUTE)
            .steps(
                [
                    Threshold(value=0.0, color="green"),
                    Threshold(value=5.0, color="yellow"),
                    Threshold(value=10.0, color="red"),  # Need to increase limits
                ]
            )
        )
        .grid_pos(GridPos(x=12, y=54, w=6, h=8))
    )


def create_quiz_response_time_p95() -> timeseries.Panel:
    """p95 response time for quiz endpoint (UX metric)."""
    return (
        timeseries.Panel()
        .title("Quiz Response Time (p95)")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Milliseconds)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'histogram_quantile(0.95, sum(rate(http_server_duration_milliseconds_bucket{environment="$environment", http_target=~"/api/v1/problems.*"}[5m])) by (le))'
            )
            .legend_format("p95")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(10)
        .thresholds(
            dashboard.ThresholdsConfig()
            .mode(ThresholdsMode.ABSOLUTE)
            .steps(
                [
                    Threshold(value=0.0, color="green"),
                    Threshold(value=5000.0, color="yellow"),  # 5s
                    Threshold(value=10000.0, color="red"),  # 10s - poor UX
                ]
            )
        )
        .grid_pos(GridPos(x=18, y=54, w=6, h=8))
    )


def create_problem_generation_success_rate() -> stat.Panel:
    """Problem generation success rate (% of successful generations)."""
    return (
        stat.Panel()
        .title("Problem Generation Success Rate")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Percent)
        .with_target(
            prometheus.Dataquery()
            .expr(
                '(sum(rate(http_server_duration_milliseconds_count{environment="$environment", http_target=~"/api/v1/problems.*", http_status_code="200"}[5m])) / sum(rate(http_server_duration_milliseconds_count{environment="$environment", http_target=~"/api/v1/problems.*"}[5m]))) * 100'
            )
            .legend_format("Success %")
            .ref_id("A")
        )
        .color_mode(common.BigValueColorMode.VALUE)
        .graph_mode(common.BigValueGraphMode.AREA)
        .thresholds(
            dashboard.ThresholdsConfig()
            .mode(ThresholdsMode.ABSOLUTE)
            .steps(
                [
                    Threshold(value=0.0, color="red"),
                    Threshold(value=90.0, color="yellow"),
                    Threshold(value=95.0, color="green"),  # Target: >95%
                ]
            )
        )
        .grid_pos(GridPos(x=0, y=62, w=8, h=6))
    )


def create_input_tokens_today() -> stat.Panel:
    """Input tokens in last 24h (cheaper: $0.150/1M for gpt-4o-mini)."""
    return (
        stat.Panel()
        .title("Input Tokens (24h)")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum(increase(llm_tokens_input_total{environment="$environment"}[24h]))'
            )
            .legend_format("Input")
            .ref_id("A")
        )
        .color_mode(common.BigValueColorMode.VALUE)
        .graph_mode(common.BigValueGraphMode.AREA)
        .grid_pos(GridPos(x=8, y=62, w=4, h=6))
    )


def create_output_tokens_today() -> stat.Panel:
    """Output tokens in last 24h (expensive: $0.600/1M for gpt-4o-mini)."""
    return (
        stat.Panel()
        .title("Output Tokens (24h)")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum(increase(llm_tokens_output_total{environment="$environment"}[24h]))'
            )
            .legend_format("Output")
            .ref_id("A")
        )
        .color_mode(common.BigValueColorMode.VALUE)
        .graph_mode(common.BigValueGraphMode.AREA)
        .thresholds(
            dashboard.ThresholdsConfig()
            .mode(ThresholdsMode.ABSOLUTE)
            .steps(
                [
                    Threshold(value=0.0, color="green"),
                    Threshold(value=50000.0, color="yellow"),  # 50k tokens
                    Threshold(value=100000.0, color="orange"),  # 100k tokens
                ]
            )
        )
        .grid_pos(GridPos(x=12, y=62, w=4, h=6))
    )


def create_http_error_rate_gauge() -> stat.Panel:
    """HTTP 5xx error rate as percentage gauge."""
    return (
        stat.Panel()
        .title("HTTP Error Rate")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Percent)
        .with_target(
            prometheus.Dataquery()
            .expr(
                '(sum(rate(http_server_duration_milliseconds_count{environment="$environment", http_target!="/", http_status_code=~"5.."}[5m])) / sum(rate(http_server_duration_milliseconds_count{environment="$environment", http_target!="/"}[5m]))) * 100'
            )
            .legend_format("Error %")
            .ref_id("A")
        )
        .color_mode(common.BigValueColorMode.VALUE)
        .thresholds(
            dashboard.ThresholdsConfig()
            .mode(ThresholdsMode.ABSOLUTE)
            .steps(
                [
                    Threshold(value=0.0, color="green"),
                    Threshold(value=1.0, color="yellow"),
                    Threshold(value=5.0, color="red"),  # >5% error rate
                ]
            )
        )
        .grid_pos(GridPos(x=16, y=62, w=8, h=6))
    )


def generate() -> dashboard.Dashboard:
    """
    Generate the Service Overview dashboard.

    This dashboard provides a high-level view of service health using the Golden Signals:
    - Latency: How long requests take
    - Traffic: Request rate
    - Errors: Error rate and count
    - Saturation: Active requests and database performance
    - Production Safety: Rate limiting, quiz metrics, error tracking

    Returns:
        Complete dashboard builder ready to build()
    """
    return (
        create_base_dashboard(
            title="Service Overview",
            description="Service health overview with Golden Signals (latency, traffic, errors, saturation)",
            uid="lqs-service-overview",
            tags=["language-quiz-service", "overview", "golden-signals"],
            use_environment_filter=True,
        )
        # All panels use absolute grid positioning (no rows)
        # Grid: 24 units wide, panels positioned with (x, y, width, height)
        .with_panel(create_uptime_stat())  # (0, 0, 6, 6)
        .with_panel(create_error_count_stat())  # (6, 0, 6, 6)
        .with_panel(create_total_requests_stat())  # (12, 0, 6, 6)
        .with_panel(create_avg_latency_stat())  # (18, 0, 6, 6)
        .with_panel(create_request_rate_panel())  # (0, 6, 12, 8)
        .with_panel(create_error_rate_panel())  # (12, 6, 12, 8)
        .with_panel(create_latency_panel())  # (0, 14, 24, 8) - aggregate p50/p95/p99
        .with_panel(
            create_p50_latency_by_endpoint_panel()
        )  # (0, 22, 24, 8) - full width
        .with_panel(create_p90_latency_by_endpoint_panel())  # (0, 30, 12, 8) - left
        .with_panel(create_p95_latency_by_endpoint_panel())  # (12, 30, 12, 8) - right
        .with_panel(create_status_code_panel())  # (0, 38, 12, 8) - left
        .with_panel(create_request_by_endpoint_panel())  # (12, 38, 12, 8) - right
        .with_panel(create_db_query_duration_panel())  # (0, 46, 12, 8)
        .with_panel(create_db_operations_panel())  # (12, 46, 12, 8)
        # NEW: Production safety panels
        .with_panel(create_quiz_requests_per_minute())  # (0, 54, 12, 8)
        .with_panel(create_rate_limit_violations())  # (12, 54, 6, 8)
        .with_panel(create_quiz_response_time_p95())  # (18, 54, 6, 8)
        .with_panel(create_problem_generation_success_rate())  # (0, 62, 8, 6)
        .with_panel(create_input_tokens_today())  # (8, 62, 4, 6)
        .with_panel(create_output_tokens_today())  # (12, 62, 4, 6)
        .with_panel(create_http_error_rate_gauge())  # (16, 62, 8, 6)
    )
