#!/bin/bash
# Railway deployment script with fresh API key

echo "🚀 Deploying openblog with fresh API key..."

# Set environment variables for deployment
export GEMINI_API_KEY=***REMOVED***
export SERPER_API_KEY=***REMOVED***
export DATAFORSEO_LOGIN=tech@scaile.it
export DATAFORSEO_PASSWORD=***REMOVED***

echo "✅ Environment variables set"

# Deploy to Railway
railway up --detach

echo "🎯 Deployment initiated"