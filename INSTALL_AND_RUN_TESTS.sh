#!/bin/bash
# BLKOUT Research Agent - Test Installation and Execution Script

set -e  # Exit on error

echo "=================================================="
echo "BLKOUT Research Agent - Test Setup"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "Error: main.py not found. Please run this from the research-agent directory."
    exit 1
fi

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install test dependencies
echo ""
echo "Installing test dependencies..."
echo "This may take a few minutes..."
pip install -r requirements-dev.txt --quiet

echo ""
echo "=================================================="
echo "Test Installation Complete!"
echo "=================================================="

echo ""
echo "You can now run tests with:"
echo ""
echo "  pytest tests/ -v                                    # Run all tests"
echo "  pytest tests/test_agents.py -v                      # Run agent tests"
echo "  pytest tests/test_date_extraction.py -v             # Run date extraction tests"
echo "  pytest tests/test_search_filtering.py -v            # Run filtering tests"
echo "  pytest tests/ --cov=src --cov-report=html           # Run with coverage report"
echo ""
echo "For more information, see:"
echo "  - TESTING.md - Quick start guide"
echo "  - tests/README.md - Complete testing documentation"
echo "  - TEST_SUITE_SUMMARY.md - Overview of the test suite"
echo ""
