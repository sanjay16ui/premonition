#!/usr/bin/env bash
# PREMONITION One-Command Setup (Linux/macOS)
# Usage: bash scripts/setup.sh

set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== PREMONITION Setup (Linux/macOS) ==="

# 1. Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.10+."
    exit 1
fi
echo "Found $(python3 --version)"

# 2. Virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

# 3. Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements-dev.txt

# 4. Create .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from template"
fi

# 5. Create directories
mkdir -p data/raw data/processed models/artifacts reports logs/predictions backups

# 6. Verify dataset
if [ ! -f "data/raw/dataset.csv" ]; then
    echo "WARNING: dataset.csv not found in data/raw/"
fi

# 7. Run tests
echo "Running tests..."
python -m pytest tests/ -v --tb=short

echo ""
echo "=== Setup Complete ==="
echo "Next steps:"
echo "  make train          # Train models"
echo "  make explain        # Generate SHAP reports"
