#!/bin/bash
# Quick test script for creator discovery tool

echo "🎬 The Channel - Creator Discovery Test"
echo "========================================="
echo ""

# Check environment
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   Copy .env.template and add your API keys"
    exit 1
fi

# Check dependencies
if ! python -c "import groq" 2>/dev/null; then
    echo "⚠️  Installing dependencies..."
    pip install -r requirements.txt
fi

echo "✅ Environment ready"
echo ""

# Run dry-run test (no database writes)
echo "🔍 Running discovery test (dry-run, max 10 creators)..."
echo ""

python discover_creators.py --dry-run --max 10

echo ""
echo "========================================="
echo "✅ Test complete!"
echo ""
echo "Next steps:"
echo "1. Review discovered creators above"
echo "2. Run real discovery: python discover_creators.py --max 50"
echo "3. Check database: SELECT COUNT(*) FROM channel_creators;"
