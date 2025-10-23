"""Utilities for configuring local Supabase connection."""

import json
import subprocess

import click


def get_local_supabase_config() -> dict[str, str]:
    """
    Get local Supabase configuration by running 'supabase status --output json'.

    Returns a dict with SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and SUPABASE_ANON_KEY.
    Raises ClickException if supabase is not running or CLI is not available.
    """
    try:
        result = subprocess.run(
            ["supabase", "status", "--output", "json"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        status_data = json.loads(result.stdout)

        api_url = status_data.get("API_URL")
        service_role_key = status_data.get("SERVICE_ROLE_KEY")
        anon_key = status_data.get("ANON_KEY")

        # Validate that we got the required keys
        if not service_role_key:
            raise click.ClickException(
                "Could not find SERVICE_ROLE_KEY in supabase status output. "
                "Is local Supabase running? Try: supabase start"
            )

        if not api_url:
            raise click.ClickException(
                "Could not find API_URL in supabase status output. "
                "Is local Supabase running? Try: supabase start"
            )

        return {
            "SUPABASE_URL": api_url,
            "SUPABASE_SERVICE_ROLE_KEY": service_role_key,
            "SUPABASE_ANON_KEY": anon_key
            or service_role_key,  # Use service key if anon not found
        }

    except FileNotFoundError:
        raise click.ClickException(
            "Supabase CLI not found. Install it from: https://supabase.com/docs/guides/cli"
        )
    except subprocess.CalledProcessError as e:
        # supabase status returns non-zero if not running
        raise click.ClickException(
            f"Local Supabase is not running or returned an error.\n"
            f"Try: supabase start\n"
            f"Error: {e.stderr.strip() if e.stderr else 'Unknown error'}"
        )
    except subprocess.TimeoutExpired:
        raise click.ClickException(
            "Timeout while checking Supabase status. Is the supabase CLI installed correctly?"
        )
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Could not parse supabase status JSON output: {e}")
