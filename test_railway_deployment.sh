#!/bin/bash
# Test Railway Deployment Script

# Get Railway URL from user or use default
RAILWAY_URL="${1:-}"

if [ -z "$RAILWAY_URL" ]; then
    echo "Usage: ./test_railway_deployment.sh <your-railway-url>"
    echo ""
    echo "Example: ./test_railway_deployment.sh https://openblog-production.up.railway.app"
    echo ""
    echo "Or get your URL from Railway Dashboard → Settings → Domains"
    exit 1
fi

echo "🧪 Testing Railway Deployment: $RAILWAY_URL"
echo "=========================================="
echo ""

# Test 1: Health Check
echo "1️⃣ Testing Health Endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$RAILWAY_URL/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$HEALTH_RESPONSE" | grep -v "HTTP_CODE")

if [ "$HTTP_CODE" == "200" ]; then
    echo "✅ Health check passed!"
    echo "Response: $BODY"
else
    echo "❌ Health check failed (HTTP $HTTP_CODE)"
    echo "Response: $BODY"
fi

echo ""
echo "2️⃣ Testing Blog Write Endpoint (requires GEMINI_API_KEY)..."
echo "   This will test if the API accepts requests"
echo ""

# Test 2: Blog Write (will fail without API key, but tests endpoint)
WRITE_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -X POST "$RAILWAY_URL/blog/write" \
    -H "Content-Type: application/json" \
    -d '{
        "primary_keyword": "test",
        "company_url": "https://example.com"
    }')

WRITE_HTTP_CODE=$(echo "$WRITE_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
WRITE_BODY=$(echo "$WRITE_RESPONSE" | grep -v "HTTP_CODE" | head -5)

echo "Response (HTTP $WRITE_HTTP_CODE):"
echo "$WRITE_BODY" | head -10

if [ "$WRITE_HTTP_CODE" == "200" ] || [ "$WRITE_HTTP_CODE" == "422" ] || [ "$WRITE_HTTP_CODE" == "500" ]; then
    echo "✅ Endpoint is responding (error expected without API key)"
else
    echo "⚠️  Unexpected response code"
fi

echo ""
echo "3️⃣ Available Endpoints:"
echo "   GET  $RAILWAY_URL/health"
echo "   GET  $RAILWAY_URL/docs (Swagger UI)"
echo "   GET  $RAILWAY_URL/redoc (ReDoc)"
echo "   POST $RAILWAY_URL/blog/write"
echo ""

echo "✅ Testing complete!"
echo ""
echo "📚 View API docs: $RAILWAY_URL/docs"

