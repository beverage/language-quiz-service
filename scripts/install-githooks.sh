#!/bin/bash
#
# Installs all git hooks from the githooks directory into the .git/hooks directory.

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INSTALL-HOOKS]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Get the root directory of the git repository
GIT_ROOT=$(git rev-parse --show-toplevel)
HOOKS_DIR="$GIT_ROOT/githooks"
GIT_HOOKS_DIR="$GIT_ROOT/.git/hooks"

# Check if the githooks directory exists
if [ ! -d "$HOOKS_DIR" ]; then
    print_error "githooks directory not found at $HOOKS_DIR"
    exit 1
fi

print_status "Installing git hooks from $HOOKS_DIR to $GIT_HOOKS_DIR..."

# Create the .git/hooks directory if it doesn't exist
mkdir -p "$GIT_HOOKS_DIR"

# Copy each hook from the githooks directory to .git/hooks
# and make them executable.
hook_count=0
for hook in "$HOOKS_DIR"/*; do
    # Skip if it's not a file
    if [ ! -f "$hook" ]; then
        continue
    fi
    
    hook_name=$(basename "$hook")
    cp "$hook" "$GIT_HOOKS_DIR/$hook_name"
    chmod +x "$GIT_HOOKS_DIR/$hook_name"
    print_status "Installed $hook_name"
    hook_count=$((hook_count + 1))
done

echo ""
print_success "Successfully installed $hook_count git hook(s)!"
echo ""
print_status "Installed hooks:"
echo "  • pre-commit  - Auto-fixes linting and formatting before commit"
echo "  • pre-push    - Runs lint, format-check, and test-cov before push"
echo "" 