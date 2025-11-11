#!/bin/bash
# Test script to generate Kafka traffic for dashboard verification
# Usage: ./scripts/test-kafka-traffic.sh [count]

set -e

COUNT=${1:-10}
TOPIC="problem-generation-requests"

echo "📨 Sending $COUNT test messages to Kafka..."
echo ""

for i in $(seq 1 $COUNT); do
    MESSAGE=$(cat <<EOF
{"test": "traffic test $i", "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)", "iteration": $i}
EOF
)
    
    docker exec -i kafka-local /opt/kafka/bin/kafka-console-producer.sh \
        --bootstrap-server kafka:9092 \
        --topic $TOPIC <<< "$MESSAGE"
    
    echo "  ✓ Sent message $i/$COUNT"
    sleep 0.3
done

echo ""
echo "✅ Sent $COUNT test messages"
echo ""
echo "📊 View metrics:"
echo "   - Grafana: http://localhost:3000/d/lqs-service-overview"
echo "   - Worker logs: docker logs language-quiz-service-local | grep '📨\\|✅'"
echo "   - Prometheus: http://localhost:9090/graph?g0.expr=worker_messages_processed_total"

