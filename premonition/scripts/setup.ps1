# PREMONITION One-Command Setup (Windows PowerShell)
# Usage: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

Write-Host "=== PREMONITION Setup (Windows) ===" -ForegroundColor Cyan

# 1. Check Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error "Python not found. Install Python 3.10+ from https://python.org"
}
$version = python --version
Write-Host "Found $version"

# 2. Create virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}
Write-Host "Activating .venv..."
& .\.venv\Scripts\Activate.ps1

# 3. Install dependencies
Write-Host "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements-dev.txt

# 4. Create .env
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from template"
}

# 5. Create directories
$dirs = @(
    "data/raw", "data/processed", "models/artifacts",
    "reports", "logs/predictions", "backups"
)
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}

# 6. Verify dataset
if (-not (Test-Path "data/raw/dataset.csv")) {
    Write-Warning "dataset.csv not found in data/raw/. Place your dataset there."
}

# 7. Run tests
Write-Host "Running tests..."
python -m pytest tests/ -v --tb=short

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  python scripts/train.py --tier t1     # Train models"
Write-Host "  python scripts/explain.py             # Generate SHAP reports"
Write-Host "  make train                            # (if GNU Make installed)"
