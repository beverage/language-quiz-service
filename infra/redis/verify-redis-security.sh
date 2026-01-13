#!/bin/bash
# Verify Redis instances are not publicly accessible
# Language Quiz Service

set -e

echo "🔒 Verifying Redis Security Configuration"
echo "=========================================="
echo ""

check_public_access() {
    local app_name=$1
    local env=$2
    
    echo "Checking $app_name ($env)..."
    
    # Check if app exists
    if ! flyctl status -a "$app_name" > /dev/null 2>&1; then
        echo "  ⚠️  App not deployed yet"
        return 0
    fi
    
    # Check for public IPs
    public_ips=$(flyctl ips list -a "$app_name" 2>/dev/null | grep -v "private" | grep -E "^(v4|v6)" || true)
    
    if [ -n "$public_ips" ]; then
        echo "  ❌ SECURITY ISSUE: Public IPs found!"
        echo "$public_ips"
        return 1
    else
        echo "  ✅ No public IPs (flycast only)"
    fi
    
    # Check for private IPs
    private_ips=$(flyctl ips list -a "$app_name" 2>/dev/null | grep "private" || true)
    
    if [ -z "$private_ips" ]; then
        echo "  ⚠️  Warning: No private IP allocated. Flycast may not work."
        echo "     Run: flyctl ips allocate-v6 --private -a $app_name"
    else
        echo "  ✅ Private IP allocated for flycast"
    fi
    
    return 0
}

# Check staging
echo ""
check_public_access "lqs-redis-staging" "staging"

# Check production
echo ""
check_public_access "lqs-redis-production" "production"

echo ""
echo "=========================================="
echo "✅ Security verification complete"
echo ""
echo "Redis instances should only be accessible via:"
echo "  - lqs-redis-staging.flycast:6379"
echo "  - lqs-redis-production.flycast:6379"
echo ""
echo "If any public IPs were found, remove them with:"
echo "  flyctl ips release <ip-address> -a <app-name>"
