"""LLM Performance Dashboard - Monitor OpenAI API calls."""

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


def create_llm_total_requests_stat() -> stat.Panel:
    """Total LLM requests in time window."""
    return (
        stat.Panel()
        .title("Total LLM Requests")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum(increase(llm_request_total{environment="$environment"}[$__range]))'
            )
            .legend_format("Total")
            .ref_id("A")
        )
        .color_mode(common.BigValueColorMode.VALUE)
        .graph_mode(common.BigValueGraphMode.AREA)
        .grid_pos(GridPos(x=0, y=0, w=6, h=6))  # x, y, w, h
    )


def create_llm_error_count_stat() -> stat.Panel:
    """Total LLM errors in time window."""
    return (
        stat.Panel()
        .title("LLM Errors")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum(increase(llm_request_total{environment="$environment", status="error"}[$__range]))'
            )
            .legend_format("Errors")
            .ref_id("A")
        )
        .color_mode(common.BigValueColorMode.VALUE)
        .graph_mode(common.BigValueGraphMode.AREA)
        .grid_pos(GridPos(x=6, y=0, w=6, h=6))  # x, y, w, h
    )


def create_llm_avg_latency_stat() -> stat.Panel:
    """Average LLM request latency."""
    return (
        stat.Panel()
        .title("Avg LLM Latency")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Milliseconds)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum(rate(llm_request_duration_milliseconds_sum{environment="$environment"}[5m])) / sum(rate(llm_request_duration_milliseconds_count{environment="$environment"}[5m]))'
            )
            .legend_format("Avg")
            .ref_id("A")
        )
        .color_mode(common.BigValueColorMode.VALUE)
        .graph_mode(common.BigValueGraphMode.AREA)
        .grid_pos(GridPos(x=12, y=0, w=6, h=6))  # x, y, w, h
    )


def create_llm_error_rate_stat() -> stat.Panel:
    """LLM error rate percentage."""
    return (
        stat.Panel()
        .title("Error Rate")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Percent)
        .with_target(
            prometheus.Dataquery()
            .expr(
                '(sum(rate(llm_request_total{environment="$environment", status="error"}[5m])) / sum(rate(llm_request_total{environment="$environment"}[5m]))) * 100'
            )
            .legend_format("Error %")
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
                    Threshold(value=1.0, color="yellow"),
                    Threshold(value=5.0, color="red"),
                ]
            )
        )
        .grid_pos(GridPos(x=18, y=0, w=6, h=6))  # x, y, w, h
    )


def create_llm_request_rate_panel() -> timeseries.Panel:
    """LLM request rate over time."""
    return (
        timeseries.Panel()
        .title("LLM Request Rate")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr('sum(rate(llm_request_total{environment="$environment"}[5m]))')
            .legend_format("Requests/sec")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(10)
        .grid_pos(GridPos(x=0, y=6, w=12, h=8))  # x, y, w, h
    )


def create_llm_error_rate_panel() -> timeseries.Panel:
    """LLM error rate over time."""
    return (
        timeseries.Panel()
        .title("LLM Error Rate")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Percent)
        .min(0)
        .max(100)
        .with_target(
            prometheus.Dataquery()
            .expr(
                '(sum(rate(llm_request_total{environment="$environment", status="error"}[5m])) / sum(rate(llm_request_total{environment="$environment"}[5m]))) * 100'
            )
            .legend_format("Error %")
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
                    Threshold(value=1.0, color="yellow"),
                    Threshold(value=5.0, color="red"),
                ]
            )
        )
        .grid_pos(GridPos(x=12, y=6, w=12, h=8))  # x, y, w, h
    )


def create_llm_latency_percentiles_panel() -> timeseries.Panel:
    """LLM latency percentiles (p50, p95, p99)."""
    return (
        timeseries.Panel()
        .title("LLM Latency Percentiles")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Milliseconds)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'histogram_quantile(0.50, sum(rate(llm_request_duration_milliseconds_bucket{environment="$environment"}[5m])) by (le))'
            )
            .legend_format("p50")
            .ref_id("A")
        )
        .with_target(
            prometheus.Dataquery()
            .expr(
                'histogram_quantile(0.95, sum(rate(llm_request_duration_milliseconds_bucket{environment="$environment"}[5m])) by (le))'
            )
            .legend_format("p95")
            .ref_id("B")
        )
        .with_target(
            prometheus.Dataquery()
            .expr(
                'histogram_quantile(0.99, sum(rate(llm_request_duration_milliseconds_bucket{environment="$environment"}[5m])) by (le))'
            )
            .legend_format("p99")
            .ref_id("C")
        )
        .line_width(2)
        .fill_opacity(10)
        .grid_pos(GridPos(x=0, y=14, w=24, h=8))  # x, y, w, h
    )


def create_llm_status_panel() -> timeseries.Panel:
    """LLM request status distribution."""
    return (
        timeseries.Panel()
        .title("LLM Request Status")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum by (status) (rate(llm_request_total{environment="$environment"}[5m]))'
            )
            .legend_format("{{status}}")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(50)
        .grid_pos(GridPos(x=0, y=22, w=12, h=8))  # x, y, w, h
    )


def create_llm_latency_by_operation_panel() -> timeseries.Panel:
    """LLM p95 latency by operation."""
    return (
        timeseries.Panel()
        .title("p95 Latency by Operation")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Milliseconds)
        .min(0)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'histogram_quantile(0.95, sum by (operation, le) (rate(llm_request_duration_milliseconds_bucket{environment="$environment"}[5m])))'
            )
            .legend_format("{{operation}}")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(10)
        .grid_pos(GridPos(x=12, y=22, w=12, h=8))  # x, y, w, h
    )


def create_token_usage_panel() -> timeseries.Panel:
    """Token usage over time (input, output, total)."""
    return (
        timeseries.Panel()
        .title("Token Usage")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr('sum(rate(llm_tokens_input_total{environment="$environment"}[5m]))')
            .legend_format("Input tokens/sec")
            .ref_id("A")
        )
        .with_target(
            prometheus.Dataquery()
            .expr('sum(rate(llm_tokens_output_total{environment="$environment"}[5m]))')
            .legend_format("Output tokens/sec")
            .ref_id("B")
        )
        .line_width(2)
        .fill_opacity(10)
        .grid_pos(GridPos(x=0, y=30, w=12, h=8))  # x, y, w, h
    )


def create_token_usage_by_operation_panel() -> timeseries.Panel:
    """Total token usage by operation."""
    return (
        timeseries.Panel()
        .title("Token Usage by Operation")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum by (operation) (rate(llm_tokens_total{environment="$environment"}[5m]))'
            )
            .legend_format("{{operation}}")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(10)
        .grid_pos(GridPos(x=12, y=30, w=12, h=8))  # x, y, w, h
    )


def create_insufficient_funds_alert() -> stat.Panel:
    """Critical alert for OpenAI insufficient funds errors (0 = Ok, >0 = Insufficient)."""
    return (
        stat.Panel()
        .title("⚠️ OpenAI Insufficient Funds (0 = Ok)")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum(llm_errors_total{environment="$environment", error_type="insufficient_funds"}) or vector(0)'
            )
            .legend_format("Errors")
            .ref_id("A")
        )
        .color_mode(common.BigValueColorMode.VALUE)
        .graph_mode(common.BigValueGraphMode.NONE)  # No sparkline for status
        .thresholds(
            dashboard.ThresholdsConfig()
            .mode(ThresholdsMode.ABSOLUTE)
            .steps(
                [
                    Threshold(value=0.0, color="green"),
                    Threshold(value=0.1, color="red"),  # ANY insufficient funds = RED
                ]
            )
        )
        .grid_pos(GridPos(x=0, y=38, w=12, h=8))  # After token usage panels
    )


def create_llm_error_types_panel() -> timeseries.Panel:
    """LLM errors by type (insufficient_funds, timeout, rate_limit, etc)."""
    return (
        timeseries.Panel()
        .title("LLM Error Types")
        .datasource(DataSourceRef(uid="$datasource"))
        .unit(units.Short)
        .with_target(
            prometheus.Dataquery()
            .expr(
                'sum by (error_type) (rate(llm_errors_total{environment="$environment"}[5m]))'
            )
            .legend_format("{{error_type}}")
            .ref_id("A")
        )
        .line_width(2)
        .fill_opacity(50)
        .grid_pos(GridPos(x=12, y=38, w=12, h=8))
    )


def generate() -> dashboard.Dashboard:
    """
    Generate the LLM Performance dashboard.

    This dashboard monitors OpenAI API calls with HTTP metrics:
    - Request rates and volumes
    - Latency distribution (p50, p95, p99)
    - Error rates and status codes
    - Performance by endpoint
    - Critical alerts (insufficient funds, error types)

    Returns:
        Complete dashboard builder ready to build()
    """
    return (
        create_base_dashboard(
            title="LLM Performance",
            description="Monitor OpenAI API call performance and reliability",
            uid="lqs-llm-performance",
            tags=["language-quiz-service", "llm", "openai", "performance"],
            use_environment_filter=True,
        )
        # All panels use absolute grid positioning (no rows)
        # Grid: 24 units wide, panels positioned with (x, y, width, height)
        .with_panel(create_llm_total_requests_stat())  # (0, 0, 6, 6)
        .with_panel(create_llm_error_count_stat())  # (6, 0, 6, 6)
        .with_panel(create_llm_avg_latency_stat())  # (12, 0, 6, 6)
        .with_panel(create_llm_error_rate_stat())  # (18, 0, 6, 6)
        .with_panel(create_llm_request_rate_panel())  # (0, 6, 12, 8)
        .with_panel(create_llm_error_rate_panel())  # (12, 6, 12, 8)
        .with_panel(create_llm_latency_percentiles_panel())  # (0, 14, 24, 8)
        .with_panel(create_llm_status_panel())  # (0, 22, 12, 8)
        .with_panel(create_llm_latency_by_operation_panel())  # (12, 22, 12, 8)
        .with_panel(create_token_usage_panel())  # (0, 30, 12, 8)
        .with_panel(create_token_usage_by_operation_panel())  # (12, 30, 12, 8)
        # NEW: Production safety panels
        .with_panel(create_insufficient_funds_alert())  # (0, 38, 12, 6)
        .with_panel(create_llm_error_types_panel())  # (12, 38, 12, 8)
    )
