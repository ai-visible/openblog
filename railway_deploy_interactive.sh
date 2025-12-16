#!/bin/bash
# Interactive Railway Deployment

set -e

echo "🚀 Railway Deployment for OpenBlog"
echo "==================================="
echo ""

# Step 1: Login
echo "Step 1/5: Logging in to Railway..."
echo "� browser will open for authentication"
railway login

echo ""
echo "✅ Logged in!"
echo ""

# Step 2: Initialize project
echo "Step 2/5: Setting up project..."
echo "Choose:"
echo "  1) Create new Railway project"
echo "  2) Link to existing project"
read -p "Enter choice (1 or 2): " choice

if [ "$choice" == "1" ]; then
    echo "Creating new project..."
    railway init --name openblog
else
    echo "Linking to existing project..."
    railway link
fi

echo ""
echo "✅ Project ready!"
echo ""

# Step 3: Set environment variable
echo "Step 3/5: Setting environment variables..."
read -p "Enter your GEMINI_API_KEY: " gemini_key

if [ -z "$gemini_key" ]; then
    echo "⚠️  Skipping API key (set manually in Railway Dashboard → Variables)"
else
    railway variables set GEMINI_API_KEY="$gemini_key"
    echo "✅ GEMINI_API_KEY set!"
fi

echo ""
echo "Step 4/5: Deploying..."
railway up

echo ""
echo "✅ Deployment complete!"
echo ""

# Step 5: Get URL
echo "Step 5/5: Getting deployment URL..."
DOMAIN=$(railway domain 2>/dev/null || echo "Check Railway Dashboard")
echo ""
echo "🌐 Your app is live at:"
echo "   $DOMAIN"
echo ""
echo "📊 Useful commands:"
echo "   railway logs          # View logs"
echo "   railway dashboard     # Open dashboard"
echo "   railway variables     # Manage env vars"
echo ""

