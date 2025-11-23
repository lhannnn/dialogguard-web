#!/bin/bash

echo "🛡️ Starting DialogGuard Web Interface..."
echo "==========================================="
echo ""

cd "$(dirname "$0")/backend" || exit 1

echo "📦 Checking dependencies..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "⚠️  Dependencies not found. Installing..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed!"
fi

echo ""
echo "🚀 Starting server on http://localhost:8000"
echo "   - Press Ctrl+C to stop"
echo "   - API documentation: http://localhost:8000/docs"
echo ""
echo "💡 Tip: Open http://localhost:8000 in your browser"
echo ""

python app.py
