#!/usr/bin/env powershell
# Setup script for unified virtual environment

Write-Host "🚀 Setting up unified virtual environment for regex_invoice_processing..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Python not found. Please install Python 3.12+" -ForegroundColor Red
    exit 1
}

# Remove existing virtual environments
Write-Host "🧹 Cleaning up existing virtual environments..." -ForegroundColor Yellow

if (Test-Path ".venv") {
    Remove-Item -Recurse -Force .venv
    Write-Host "   ✅ Removed .venv" -ForegroundColor Green
}

if (Test-Path "backend\venv") {
    Remove-Item -Recurse -Force backend\venv
    Write-Host "   ✅ Removed backend\venv" -ForegroundColor Green
}

# Create new unified virtual environment
Write-Host "🏗️  Creating new virtual environment..." -ForegroundColor Yellow
python -m venv .venv

# Activate virtual environment
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "⬆️  Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "📦 Installing dependencies from unified requirements.txt..." -ForegroundColor Yellow
pip install -r requirements.txt

# Verify installation
Write-Host "🔍 Verifying key packages..." -ForegroundColor Yellow

$packages = @("fastapi", "sqlalchemy", "pytesseract", "opencv-python", "pytest", "PyMuPDF", "scikit-image")

foreach ($package in $packages) {
    try {
        $version = pip show $package | Select-String "Version:" | ForEach-Object { $_.ToString().Split(":")[1].Trim() }
        if ($version) {
            Write-Host "   ✅ $package $version" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "   ❌ $package not found" -ForegroundColor Red
    }
}

# Setup completion
Write-Host ""
Write-Host "🎉 Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the virtual environment in future sessions:" -ForegroundColor Cyan
Write-Host "   .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To run tests:" -ForegroundColor Cyan
Write-Host "   python -m pytest backend/test_structure_aware_ocr.py -v" -ForegroundColor White
Write-Host ""
Write-Host "To start the application:" -ForegroundColor Cyan
Write-Host "   cd backend && python -m uvicorn app.main:app --reload" -ForegroundColor White
