#!/bin/bash
# First-time setup for local development environment

set -e

echo "🔧 Language Quiz Service - Local Environment Setup"
echo "=================================================="
echo ""

# Check if .env already exists
if [ -f .env ]; then
    echo "✅ .env file already exists"
    echo ""
    
    # Check if Grafana variables are already configured
    if grep -q "GRAFANA_CLOUD_API_KEY=" .env && ! grep -q "your-grafana-api-key" .env; then
        echo "✅ Grafana Cloud credentials already configured"
        echo "   Your .env file is ready to use"
        echo ""
        echo "To update Grafana credentials, manually edit .env"
        exit 0
    fi
    
    echo "📊 Grafana Cloud observability is not yet configured"
    echo "   (This is optional for local development)"
    # Will prompt for Grafana setup below
else
    # Create .env from example
    if [ ! -f env.example ]; then
        echo "❌ Error: env.example not found"
        echo "   This file should be in the project root"
        exit 1
    fi
    
    echo "📝 Creating .env from env.example..."
    cp env.example .env
    echo "✅ .env created"
    echo ""
fi

# Check if Grafana credentials need to be added
if ! grep -q "GRAFANA_CLOUD_API_KEY=" .env 2>/dev/null; then
    echo "📝 Adding Grafana Cloud variables to .env..."
    cat >> .env << 'EOF'

# ============================================================================
# Observability - Grafana Cloud (Optional)
# ============================================================================
GRAFANA_CLOUD_OTLP_ENDPOINT=your-grafana-otlp-endpoint
GRAFANA_CLOUD_INSTANCE_ID=your-instance-id
GRAFANA_CLOUD_API_KEY=your-grafana-api-key

# OpenTelemetry configuration
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_RESOURCE_ATTRIBUTES=service.name=language-quiz-service,service.namespace=language-learning,deployment.environment=local
EOF
    echo "✅ Grafana variables added to .env"
    echo ""
fi

# Check if Grafana credentials are placeholder values
if grep -q "your-grafana-api-key" .env 2>/dev/null; then
    # Prompt for Grafana Cloud setup
    echo "📊 Grafana Cloud Setup (Optional)"
    echo "────────────────────────────────"
    echo "Grafana Cloud provides observability (traces, logs, metrics)"
    echo "for local development. This is optional but recommended."
    echo ""
    read -p "Set up Grafana Cloud observability? (y/N) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Get your credentials from: https://beverage.grafana.net"
        echo "  1. Click 'Connections' → 'Add new connection'"
        echo "  2. Search for 'OpenTelemetry'"
        echo "  3. Click 'Create Access Token'"
        echo ""
        
        read -p "Grafana Cloud Instance ID (e.g., 1403830): " INSTANCE_ID
        read -sp "Grafana Cloud API Key: " API_KEY
        echo
        read -p "Grafana OTLP Endpoint (e.g., https://otlp-gateway-prod-eu-west-2.grafana.net/otlp): " ENDPOINT
        
        # Update .env with Grafana credentials (macOS compatible)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|GRAFANA_CLOUD_INSTANCE_ID=.*|GRAFANA_CLOUD_INSTANCE_ID=$INSTANCE_ID|" .env
            sed -i '' "s|GRAFANA_CLOUD_API_KEY=.*|GRAFANA_CLOUD_API_KEY=$API_KEY|" .env
            sed -i '' "s|GRAFANA_CLOUD_OTLP_ENDPOINT=.*|GRAFANA_CLOUD_OTLP_ENDPOINT=$ENDPOINT|" .env
        else
            sed -i "s|GRAFANA_CLOUD_INSTANCE_ID=.*|GRAFANA_CLOUD_INSTANCE_ID=$INSTANCE_ID|" .env
            sed -i "s|GRAFANA_CLOUD_API_KEY=.*|GRAFANA_CLOUD_API_KEY=$API_KEY|" .env
            sed -i "s|GRAFANA_CLOUD_OTLP_ENDPOINT=.*|GRAFANA_CLOUD_OTLP_ENDPOINT=$ENDPOINT|" .env
        fi
        
        echo ""
        echo "✅ Grafana Cloud credentials saved to .env"
        echo "   You can now run: make dev-monitored"
    else
        echo ""
        echo "⏭️  Skipped Grafana Cloud setup"
        echo "   You can still run: make dev (without monitoring)"
        echo "   To add observability later, edit .env and run: make dev-monitored"
    fi
else
    echo "✅ Grafana Cloud credentials already configured"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API keys:"
echo "     - OPENAI_API_KEY"
echo "     - SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, etc."
echo ""
echo "  2. Start development:"
echo "     make dev              # Fast start, no monitoring"
echo "     make dev-monitored    # With Grafana Cloud observability"
echo ""
echo "  3. Run CLI commands:"
echo "     lqs verb random       # Test the CLI"
echo ""
echo "For more info, see: README.md"

