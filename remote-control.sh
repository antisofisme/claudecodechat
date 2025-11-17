#!/bin/bash
# Helper script untuk Claude remote control server
# Simpan URL dan SECRET sebagai environment variables

# Configuration (will be set after user provides info)
REMOTE_URL="${REMOTE_URL:-}"
REMOTE_SECRET="${REMOTE_SECRET:-}"

if [ -z "$REMOTE_URL" ] || [ -z "$REMOTE_SECRET" ]; then
    echo "⚠️  Please set REMOTE_URL and REMOTE_SECRET environment variables"
    echo "Example:"
    echo "  export REMOTE_URL='https://your-server.ngrok.io'"
    echo "  export REMOTE_SECRET='your-secret-key'"
    exit 1
fi

# Function to call remote API
remote_call() {
    local endpoint=$1
    local method=${2:-GET}
    local data=${3:-}

    if [ -n "$data" ]; then
        curl -s -X "$method" "$REMOTE_URL$endpoint" \
            -H "Authorization: Bearer $REMOTE_SECRET" \
            -H "Content-Type: application/json" \
            -d "$data"
    else
        curl -s -X "$method" "$REMOTE_URL$endpoint" \
            -H "Authorization: Bearer $REMOTE_SECRET"
    fi
}

# Export function for use in scripts
export -f remote_call

# Test connection
echo "Testing connection to $REMOTE_URL..."
response=$(remote_call "/health")
echo "$response"

if echo "$response" | grep -q "ok"; then
    echo "✅ Connection successful!"
else
    echo "❌ Connection failed!"
    exit 1
fi
