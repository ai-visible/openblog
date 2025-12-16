#!/bin/bash
# Quick test - replace with your actual Railway domain

RAILWAY_DOMAIN="${1:-}"

if [ -z "$RAILWAY_DOMAIN" ]; then
    echo "Usage: ./quick_test.sh <your-railway-domain>"
    echo ""
    echo "Example: ./quick_test.sh openblog-production-xxxx.up.railway.app"
    echo ""
    echo "Get your domain from Railway Dashboard → Settings → Domains"
    exit 1
fi

echo "🧪 Testing Railway Deployment"
echo "Domain: $RAILWAY_DOMAIN"
echo ""

# Test health
echo "1. Health Check:"
curl -s "https://$RAILWAY_DOMAIN/health" | python3 -m json.tool 2>/dev/null || curl -s "https://$RAILWAY_DOMAIN/health"
echo ""
echo ""

# Test docs
echo "2. API Documentation:"
echo "   Swagger UI: https://$RAILWAY_DOMAIN/docs"
echo "   ReDoc: https://$RAILWAY_DOMAIN/redoc"
echo ""

echo "✅ Test complete!"
