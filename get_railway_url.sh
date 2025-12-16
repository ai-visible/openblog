#!/bin/bash
# Get Railway deployment URL

echo "🔍 Finding Railway Deployment URL"
echo "=================================="
echo ""
echo "The URL you shared is the metrics dashboard, not the API endpoint."
echo ""
echo "To get your API URL:"
echo ""
echo "Method 1: Railway Dashboard"
echo "  1. Go to: https://railway.app/project/2f0cb32f-0508-43e1-85ec-1dd4075e4b4d"
echo "  2. Click on 'openblog' service"
echo "  3. Go to 'Settings' tab"
echo "  4. Click 'Generate Domain' (if not already generated)"
echo "  5. Copy the domain (e.g., openblog-production.up.railway.app)"
echo ""
echo "Method 2: Railway CLI"
echo "  railway domain"
echo ""
echo "Once you have the domain, test with:"
echo "  curl https://your-domain.up.railway.app/health"
echo ""

