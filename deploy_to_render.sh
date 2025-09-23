#!/bin/bash
# Deploy BTEB Results API to Render

echo "🚀 Preparing BTEB Results API for Render deployment..."
echo "======================================================"

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the bteb_results directory."
    exit 1
fi

echo "✅ Found app.py"
echo "✅ Found requirements.txt"
echo "✅ Found Procfile"
echo "✅ Found render.yaml"

echo ""
echo "📋 Next Steps:"
echo "1. Go to https://render.com and sign up/login"
echo "2. Click 'New +' → 'Web Service'"
echo "3. Connect your GitHub repository"
echo "4. Select the bteb_results folder as the root directory"
echo "5. Use these settings:"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: gunicorn app:app --bind 0.0.0.0:\$PORT"
echo "   - Health Check Path: /health"
echo ""
echo "🔐 Environment Variables to set in Render:"
echo "   - SUPABASE_PRIMARY_URL=https://hddphaneexloretrisiy.supabase.co"
echo "   - SUPABASE_PRIMARY_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
echo "   - SUPABASE_SECONDARY_URL=https://ncjleyktzilulflbjfdg.supabase.co"
echo "   - SUPABASE_SECONDARY_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
echo ""
echo "📱 After deployment, update your mobile app's API URL to:"
echo "   https://your-app-name.onrender.com"
echo ""
echo "🎯 Ready for deployment!"
