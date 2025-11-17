#!/bin/bash
#
# Kafka Topic Migration Script
#
# This script applies Kafka topic definitions from YAML files.
# It creates topics if they don't exist and updates partition counts if needed.
#
# Usage: ./init-topics.sh <bootstrap-servers> <topics-directory>
# Example: ./init-topics.sh kafka:9092 /topics

set -e  # Exit on error

BOOTSTRAP_SERVERS="${1:-kafka:9092}"
TOPICS_DIR="${2:-/topics}"

echo "================================================"
echo "Kafka Topic Migration"
echo "================================================"
echo "Bootstrap servers: $BOOTSTRAP_SERVERS"
echo "Topics directory: $TOPICS_DIR"
echo ""

# Check if topics directory exists
if [ ! -d "$TOPICS_DIR" ]; then
    echo "ERROR: Topics directory not found: $TOPICS_DIR"
    exit 1
fi

# Function to parse YAML (simple implementation for our use case)
parse_yaml() {
    local file="$1"
    local key="$2"
    grep "^${key}:" "$file" | sed "s/^${key}:[[:space:]]*//" | tr -d '"'
}

# Function to create or update topic
apply_topic() {
    local yaml_file="$1"
    
    echo "Processing: $(basename $yaml_file)"
    
    # Parse YAML file
    local topic_name=$(parse_yaml "$yaml_file" "name")
    local partitions=$(parse_yaml "$yaml_file" "partitions")
    local replication_factor=$(parse_yaml "$yaml_file" "replication_factor")
    
    # Parse config options
    local retention_ms=$(grep "retention.ms:" "$yaml_file" | sed 's/.*retention.ms:[[:space:]]*//' | tr -d '"')
    local compression_type=$(grep "compression.type:" "$yaml_file" | sed 's/.*compression.type:[[:space:]]*//' | tr -d '"')
    local cleanup_policy=$(grep "cleanup.policy:" "$yaml_file" | sed 's/.*cleanup.policy:[[:space:]]*//' | tr -d '"')
    local segment_ms=$(grep "segment.ms:" "$yaml_file" | sed 's/.*segment.ms:[[:space:]]*//' | tr -d '"')
    
    echo "  Topic: $topic_name"
    echo "  Partitions: $partitions"
    echo "  Replication Factor: $replication_factor"
    
    # Build config string
    local config_args=""
    [ -n "$retention_ms" ] && config_args="${config_args}--config retention.ms=${retention_ms} "
    [ -n "$compression_type" ] && config_args="${config_args}--config compression.type=${compression_type} "
    [ -n "$cleanup_policy" ] && config_args="${config_args}--config cleanup.policy=${cleanup_policy} "
    [ -n "$segment_ms" ] && config_args="${config_args}--config segment.ms=${segment_ms} "
    
    # Check if topic exists
    if /opt/kafka/bin/kafka-topics.sh --bootstrap-server "$BOOTSTRAP_SERVERS" --list 2>/dev/null | grep -q "^${topic_name}$"; then
        echo "  ✓ Topic already exists"
        
        # Check if we need to increase partition count
        current_partitions=$(/opt/kafka/bin/kafka-topics.sh --bootstrap-server "$BOOTSTRAP_SERVERS" --describe --topic "$topic_name" 2>/dev/null | grep "PartitionCount:" | sed 's/.*PartitionCount: \([0-9]*\).*/\1/')
        
        if [ -n "$current_partitions" ] && [ "$current_partitions" -lt "$partitions" ]; then
            echo "  ⚠️  Increasing partitions from $current_partitions to $partitions"
            /opt/kafka/bin/kafka-topics.sh \
                --bootstrap-server "$BOOTSTRAP_SERVERS" \
                --alter \
                --topic "$topic_name" \
                --partitions "$partitions"
            echo "  ✓ Partitions updated successfully"
        elif [ -n "$current_partitions" ]; then
            echo "  ✓ Partition count is correct ($current_partitions)"
        fi
    else
        echo "  → Creating topic..."
        /opt/kafka/bin/kafka-topics.sh \
            --bootstrap-server "$BOOTSTRAP_SERVERS" \
            --create \
            --topic "$topic_name" \
            --partitions "$partitions" \
            --replication-factor "$replication_factor" \
            $config_args
        echo "  ✓ Topic created successfully"
    fi
    
    echo ""
}

# Process all YAML files in topics directory
topic_count=0
for yaml_file in "$TOPICS_DIR"/*.yaml; do
    if [ -f "$yaml_file" ]; then
        apply_topic "$yaml_file"
        ((topic_count++))
    fi
done

if [ $topic_count -eq 0 ]; then
    echo "⚠️  No topic definition files found in $TOPICS_DIR"
    exit 0
fi

echo "================================================"
echo "✓ Migration complete: $topic_count topic(s) processed"
echo "================================================"

# List all topics for verification
echo ""
echo "Current topics:"
/opt/kafka/bin/kafka-topics.sh --bootstrap-server "$BOOTSTRAP_SERVERS" --list

exit 0

