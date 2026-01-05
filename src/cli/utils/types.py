"""Custom Click types for CLI argument parsing."""

from datetime import UTC, datetime, timedelta

import asyncclick
import pytimeparse
from dateutil import parser as dateutil_parser


class DurationParam(asyncclick.ParamType):
    """
    Click parameter type that parses human-readable duration strings.

    Accepts strings like:
    - "3h" (3 hours)
    - "1d" (1 day)
    - "2w" (2 weeks)
    - "30m" (30 minutes)
    - "1h30m" (1 hour 30 minutes)
    - "1d 3h 25m" (1 day, 3 hours, 25 minutes)

    Returns a timedelta object.
    """

    name = "duration"

    def convert(self, value, param, ctx):
        """Convert a duration string to a timedelta object."""
        if value is None:
            self.fail(
                "Duration is required. Use formats like '3h', '1d', '2w', '30m', or '1h30m'.",
                param,
                ctx,
            )

        if isinstance(value, timedelta):
            return value

        if isinstance(value, str):
            # Parse the duration string using pytimeparse
            seconds = pytimeparse.parse(value)
            if seconds is None:
                self.fail(
                    f"'{value}' is not a valid duration. "
                    "Use formats like '3h', '1d', '2w', '30m', or '1h30m'.",
                    param,
                    ctx,
                )
            return timedelta(seconds=seconds)

        self.fail(
            f"Expected a duration string, got {type(value).__name__}",
            param,
            ctx,
        )


class DateOrDurationParam(asyncclick.ParamType):
    """
    Click parameter type that parses either a date or a duration string.

    Accepts:
    - Relative durations: "7d", "2w", "1h30m" → converted to datetime (now - duration)
    - Absolute dates: "2025-01-01", "2025-01-01T12:00:00" → parsed as datetime

    Returns a datetime object (timezone-aware, UTC).

    Examples:
        --older-than 7d        → datetime 7 days ago
        --newer-than 2025-01-01 → datetime of 2025-01-01 00:00:00 UTC
    """

    name = "date_or_duration"

    def convert(self, value, param, ctx):
        """Convert a date or duration string to a datetime object."""
        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            # First try parsing as a duration (e.g., "7d", "2w")
            seconds = pytimeparse.parse(value)
            if seconds is not None:
                # Duration found - calculate datetime relative to now
                return datetime.now(UTC) - timedelta(seconds=seconds)

            # Try parsing as an absolute date/datetime
            try:
                parsed = dateutil_parser.parse(value)
                # Ensure timezone awareness
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=UTC)
                return parsed
            except (ValueError, dateutil_parser.ParserError):
                pass

            self.fail(
                f"'{value}' is not a valid date or duration. "
                "Use durations like '7d', '2w', '1h30m' or dates like '2025-01-01'.",
                param,
                ctx,
            )

        self.fail(
            f"Expected a date or duration string, got {type(value).__name__}",
            param,
            ctx,
        )
