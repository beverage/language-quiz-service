"""Custom Click types for CLI argument parsing."""

from datetime import timedelta

import asyncclick
import pytimeparse


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
