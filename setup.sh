#!/bin/bash
# BLKOUT Research Agent - Setup Script

set -e

echo "=========================================="
echo "BLKOUT Research Agent Setup"
echo "=========================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$PYTHON_VERSION" < "3.10" ]]; then
    echo "Error: Python 3.10+ required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "[1/5] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[2/5] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[3/5] Installing Playwright browser..."
playwright install chromium

echo "[4/5] Setting up environment file..."
if [ ! -f .env ]; then
    cp .env.template .env
    echo "Created .env file - please edit with your API keys"
else
    echo ".env file already exists"
fi

echo "[5/5] Verifying installation..."
python -c "from src.agents import PlanningAgent; print('Agents: OK')"
python -c "from src.scheduler import DiscoveryScheduler; print('Scheduler: OK')"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys:"
echo "   - GROQ_API_KEY (get free at https://console.groq.com)"
echo "   - SUPABASE_URL"
echo "   - SUPABASE_SERVICE_ROLE_KEY"
echo ""
echo "2. Test the agent:"
echo "   python main.py --test"
echo ""
echo "3. Run discovery:"
echo "   python main.py --run-now daily"
echo ""
echo "4. Run as daemon:"
echo "   python main.py"
echo ""
