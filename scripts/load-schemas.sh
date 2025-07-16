#!/bin/bash

# Load database schemas into Supabase
# This script runs all SQL files in ./sql directory in order
# Then loads test data from ./sql/test directory

set -e  # Exit on any error

echo "🔄 Loading database schemas into Supabase..."

# Get the project root directory (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SQL_DIR="$PROJECT_ROOT/sql"
TEST_SQL_DIR="$PROJECT_ROOT/sql/test"

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

# Load test data if test directory exists
if [ -d "$TEST_SQL_DIR" ]; then
    echo ""
    echo "🧪 Loading test data..."
    
    # Get all test SQL files in order
    TEST_SQL_FILES=$(ls "$TEST_SQL_DIR"/*.sql 2>/dev/null | sort)
    
    if [ -n "$TEST_SQL_FILES" ]; then
        echo "📁 Found test SQL files:"
        for file in $TEST_SQL_FILES; do
            echo "  - $(basename "$file")"
        done
        
        # Execute each test SQL file
        for sql_file in $TEST_SQL_FILES; do
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
        
        echo "🎉 All test data loaded successfully!"
    else
        echo "📁 No test SQL files found in $TEST_SQL_DIR"
    fi
else
    echo "📁 No test directory found at $TEST_SQL_DIR - skipping test data"
fi 