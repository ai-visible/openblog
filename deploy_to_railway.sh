#!/bin/bash
# Railway Deployment Script
# This script will help deploy OpenBlog to Railway

set -e

echo "🚀 Railway Deployment Script for OpenBlog"
echo "=========================================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
    echo "✅ Railway CLI installed"
else
    echo "✅ Railway CLI already installed"
fi

echo ""
echo "📋 Next Steps:"
echo "1. You'll need to authenticate with Railway (opens browser)"
echo "2. Then we'll create/select a project"
echo "3. Set environment variables"
echo "4. Deploy!"
echo ""
read -p "Press Enter to continue with Railway login..."

# Login to Railway (will open browser)
echo ""
echo "🔐 Logging in to Railway..."
railway login

echo ""
echo "📦 Creating/Selecting Railway project..."
echo "Choose:"
echo "  1) Create new project"
echo "  2) Link to existing project"
read -p "Enter choice (1 or 2): " choice

if [ "$choice" == "1" ]; then
    railway init
else
    railway link
fi

echo ""
echo "🔧 Setting up environment variables..."
echo "You'll need to provide your GEMINI_API_KEY"
read -p "Enter your GEMINI_API_KEY: " gemini_key

if [ -z "$gemini_key" ]; then
    echo "⚠️  No API key provided. You can set it later in Railway Dashboard"
else
    railway variables set GEMINI_API_KEY="$gemini_key"
    echo "✅ GEMINI_API_KEY set"
fi

echo ""
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Get your deployment URL:"
railway domain

echo ""
echo "🔍 Check logs:"
echo "  railway logs"
echo ""
echo "🌐 Open dashboard:"
echo "  railway dashboard"

