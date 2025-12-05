#!/bin/bash
# Test API service blog generation

echo "Testing API Service..."
echo ""

# Test health endpoint
echo "1. Testing health endpoint..."
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    echo "$HEALTH"
    exit 1
fi

echo ""
echo "2. Testing blog generation (this will take ~90 seconds)..."
echo ""

# Test blog generation
RESPONSE=$(curl -s -X POST http://localhost:8000/write \
  -H "Content-Type: application/json" \
  -d '{
    "primary_keyword": "AI customer service automation",
    "company_url": "https://example.com",
    "company_name": "Example Corp"
  }')

# Check if successful
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "✅ Blog generation successful"
    echo ""
    echo "$RESPONSE" | python3 -m json.tool | head -30
else
    echo "❌ Blog generation failed"
    echo "$RESPONSE"
    exit 1
fi

