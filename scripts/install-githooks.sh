#!/bin/sh
#
# Installs all git hooks from the githooks directory into the .git/hooks directory.

# Get the root directory of the git repository
GIT_ROOT=$(git rev-parse --show-toplevel)
HOOKS_DIR="$GIT_ROOT/githooks"
GIT_HOOKS_DIR="$GIT_ROOT/.git/hooks"

# Check if the githooks directory exists
if [ ! -d "$HOOKS_DIR" ]; then
    echo "Error: githooks directory not found."
    exit 1
fi

echo "Installing git hooks from $HOOKS_DIR to $GIT_HOOKS_DIR..."

# Create the .git/hooks directory if it doesn't exist
mkdir -p "$GIT_HOOKS_DIR"

# Copy each hook from the githooks directory to .git/hooks
# and make them executable.
for hook in "$HOOKS_DIR"/*; do
    hook_name=$(basename "$hook")
    cp "$hook" "$GIT_HOOKS_DIR/$hook_name"
    chmod +x "$GIT_HOOKS_DIR/$hook_name"
    echo "  Installed $hook_name"
done

echo "Git hooks installed successfully." 