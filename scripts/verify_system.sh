#!/bin/bash

echo "🔍 Verifying UI-Scraper System Status..."
echo "========================================"

# Check services
echo -e "\n📊 Service Status:"
echo "----------------"

# Check MongoDB
if curl -s http://localhost:27017 > /dev/null 2>&1; then
    echo "✅ MongoDB: Running on port 27017"
else
    echo "❌ MongoDB: Not accessible"
fi

# Check Redis
if nc -zv localhost 6379 2>&1 | grep -q succeeded; then
    echo "✅ Redis: Running on port 6379"
else
    echo "❌ Redis: Not accessible"
fi

# Check Backend API
if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    echo "✅ Backend API: Running on port 8000"
else
    echo "❌ Backend API: Not accessible"
fi

# Check Frontend
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ | grep -q "200"; then
    echo "✅ Frontend: Running on port 3000"
else
    echo "❌ Frontend: Not accessible"
fi

# Test API Endpoints
echo -e "\n🧪 API Endpoint Tests:"
echo "--------------------"

# Health check
echo -n "Health Check: "
if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    echo "✅ Working"
else
    echo "❌ Failed"
fi

# Dashboard stats
echo -n "Dashboard Stats: "
if curl -s http://localhost:8000/api/dashboard/stats | grep -q "total_businesses"; then
    echo "✅ Working"
else
    echo "❌ Failed"
fi

# Jobs endpoint
echo -n "Jobs Endpoint: "
response=$(curl -s http://localhost:8000/api/jobs/)
if [[ "$response" == "["* ]] || [[ "$response" == "{"* ]]; then
    echo "✅ Working"
else
    echo "❌ Failed"
fi

# Businesses endpoint
echo -n "Businesses Endpoint: "
response=$(curl -s http://localhost:8000/api/businesses/)
if [[ "$response" == "["* ]] || [[ "$response" == "{"* ]]; then
    echo "✅ Working"
else
    echo "❌ Failed"
fi

echo -e "\n✨ System verification complete!"
echo "================================"
echo ""
echo "🌐 You can now access:"
echo "  - Frontend: http://localhost:3000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "📝 To configure your API key:"
echo "  1. Go to http://localhost:3000/settings"
echo "  2. Enter your Google Gemini API key"
echo "  3. Click 'Save API Key'"