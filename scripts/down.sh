#!/bin/bash
set -e

cd "$(dirname "$0")/.." || exit

if command -v poetry >/dev/null 2>&1; then
    POETRY_CMD="poetry"
elif [ -f "$HOME/.local/bin/poetry" ]; then
    POETRY_CMD="$HOME/.local/bin/poetry"
else
    echo "Error: Poetry not found. Please ensure it's installed and in your PATH"
    exit 1
fi

$POETRY_CMD run lqs cloud service down
$POETRY_CMD run lqs cloud database down