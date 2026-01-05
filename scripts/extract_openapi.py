#!/usr/bin/env python
"""
Extract OpenAPI documentation from the Language Quiz Service without running it.

This script imports the FastAPI app and extracts the OpenAPI schema directly,
bypassing the lifespan (which requires database connections).

Usage:
    python scripts/extract_openapi.py                    # Print JSON to stdout
    python scripts/extract_openapi.py -o openapi.json   # Write to file
    python scripts/extract_openapi.py --yaml            # Output as YAML
    python scripts/extract_openapi.py --yaml -o openapi.yaml
"""

import argparse
import json
import sys
from pathlib import Path

# Add the project root to the path so we can import src
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def extract_openapi_schema():
    """
    Extract the OpenAPI schema from the FastAPI app.

    The app.openapi() method generates the schema from route definitions
    without invoking the lifespan context manager.
    """
    from src.main import app

    return app.openapi()


def main():
    parser = argparse.ArgumentParser(
        description="Extract OpenAPI documentation from the Language Quiz Service"
    )
    parser.add_argument(
        "-o", "--output", type=str, help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--yaml", action="store_true", help="Output as YAML instead of JSON"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print the output (default: True)",
    )

    args = parser.parse_args()

    # Extract the schema
    schema = extract_openapi_schema()

    # Format output
    if args.yaml:
        try:
            import yaml

            output = yaml.dump(schema, default_flow_style=False, sort_keys=False)
        except ImportError:
            print(
                "Error: PyYAML is required for YAML output. Install with: pip install pyyaml",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        indent = 2 if args.pretty else None
        output = json.dumps(schema, indent=indent)

    # Write output
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(output)
        print(f"OpenAPI schema written to: {output_path}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
