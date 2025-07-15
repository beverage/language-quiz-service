#!/bin/bash

# Load database schemas into Supabase
# This script runs all SQL files in ./sql directory in order

set -e  # Exit on any error

echo "🔄 Loading database schemas into Supabase..."

# Get the project root directory (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SQL_DIR="$PROJECT_ROOT/sql"

# Check if SQL directory exists
if [ ! -d "$SQL_DIR" ]; then
    echo "❌ SQL directory not found: $SQL_DIR"
    exit 1
fi

# Get database URL from Supabase status
DB_URL=$(supabase status --output json | jq -r '.DB_URL')

if [ -z "$DB_URL" ] || [ "$DB_URL" = "null" ]; then
    echo "❌ Could not get database URL from Supabase status"
    echo "Make sure Supabase is running with 'make start-supabase'"
    exit 1
fi

echo "🔗 Using database: $DB_URL"

# Get all SQL files in order (numbered files only, not recursive)
SQL_FILES=$(ls "$SQL_DIR"/*.sql 2>/dev/null | sort)

if [ -z "$SQL_FILES" ]; then
    echo "❌ No SQL files found in $SQL_DIR"
    exit 1
fi

echo "📁 Found SQL files:"
for file in $SQL_FILES; do
    echo "  - $(basename "$file")"
done

# Execute each SQL file
for sql_file in $SQL_FILES; do
    filename=$(basename "$sql_file")
    echo "🔄 Executing $filename..."
    
    # Use psql to execute the SQL file
    psql "$DB_URL" -f "$sql_file" -q
    
    if [ $? -eq 0 ]; then
        echo "✅ $filename executed successfully"
    else
        echo "❌ Failed to execute $filename"
        exit 1
    fi
done

echo "🎉 All database schemas loaded successfully!" 