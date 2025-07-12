"""
This file makes the 'cli' package runnable as a module.
"""

import os
import sys

from src.cli.console import main

# Add the project root to the Python path
# This allows the CLI to be run as a script from the project root
# and still resolve 'src' imports correctly.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    main(_anyio_backend="asyncio")
