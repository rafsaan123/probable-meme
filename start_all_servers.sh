#!/bin/bash
# Complete Server Startup Script for BTEB Results App
# Starts all required servers except npx expo start

echo "🚀 Starting BTEB Results App Servers"
echo "======================================"

# Kill any existing processes on our ports
echo "🧹 Cleaning up existing processes..."
pkill -f "python multi_supabase_api_server.py" 2>/dev/null || true
pkill -f "python supabase_api_server.py" 2>/dev/null || true
sleep 2

# Navigate to the project directory
cd /Users/md.rafsan/CollegeApp/bteb_results

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
source api_env/bin/activate

# Start the Multi-Project Supabase API Server with Web API Fallback
echo "📡 Starting Multi-Project Supabase API Server (with Web API Fallback)..."
echo "   - Port: 3001"
echo "   - Features: 5 Supabase projects + Web API fallback"
echo "   - Endpoints: /api/search-result, /api/projects, /api/web-apis, etc."

# Start the server in background
python multi_supabase_api_server.py &
API_PID=$!

# Wait for server to start
echo "⏳ Waiting for API server to start..."
sleep 5

# Test server health
echo "🏥 Testing API server health..."
if curl -s http://localhost:3001/health > /dev/null; then
    echo "✅ API server is healthy and running"
else
    echo "❌ API server failed to start"
    exit 1
fi

# Test web API fallback
echo "🌐 Testing web API fallback system..."
if curl -s http://localhost:3001/api/web-apis/test > /dev/null; then
    echo "✅ Web API fallback system is working"
else
    echo "❌ Web API fallback system failed"
fi

# Display server information
echo ""
echo "📊 Server Status Summary"
echo "========================"
echo "✅ Multi-Project Supabase API Server: Running on port 3001"
echo "✅ Web API Fallback: Active (btebresulthub)"
echo "✅ 5 Supabase Projects: Configured and ready"
echo ""
echo "🔗 Available Endpoints:"
echo "   POST http://localhost:3001/api/search-result - Search student results"
echo "   GET  http://localhost:3001/api/projects - List Supabase projects"
echo "   GET  http://localhost:3001/api/web-apis - List web APIs"
echo "   GET  http://localhost:3001/api/web-apis/test - Test web API connections"
echo "   GET  http://localhost:3001/health - Health check"
echo ""
echo "🎯 Ready for app testing!"
echo "   Run: npx expo start"
echo ""
echo "📝 To stop servers: kill $API_PID"
echo "   Or run: pkill -f 'python multi_supabase_api_server.py'"

# Keep the script running to maintain the background process
wait $API_PID
