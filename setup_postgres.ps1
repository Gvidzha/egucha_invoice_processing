# PostgreSQL datubāzes un lietotāja izveides skripts Windows
# Palaidīt ar PostgreSQL admin tiesībām

Write-Host "=== PostgreSQL datubāzes setup ===" -ForegroundColor Green

# Pārbaudīt vai psql ir pieejams
try {
    $psqlVersion = psql --version
    Write-Host "PostgreSQL atrasts: $psqlVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: psql nav atrasts PATH! Pārliecinieties, ka PostgreSQL ir instalēts un pievienots PATH." -ForegroundColor Red
    exit 1
}

# Izveidot datubāzi un lietotāju
Write-Host "Veidoju datubāzi..." -ForegroundColor Yellow
psql -U postgres -c "CREATE DATABASE invoice_processing_db;"

Write-Host "Veidoju lietotāju..." -ForegroundColor Yellow  
psql -U postgres -c "CREATE USER invoice_user WITH ENCRYPTED PASSWORD 'invoice_password';"

Write-Host "Piešķiru tiesības..." -ForegroundColor Yellow
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE invoice_processing_db TO invoice_user;"
psql -U postgres -c "ALTER USER invoice_user CREATEDB;"

Write-Host ""
Write-Host "✅ Datubāze 'invoice_processing_db' un lietotājs 'invoice_user' izveidoti veiksmīgi!" -ForegroundColor Green

Write-Host ""
Write-Host "=== Connection string ===" -ForegroundColor Cyan
Write-Host "postgresql://invoice_user:invoice_password@localhost:5432/invoice_processing_db"

Write-Host ""
Write-Host "=== Nākamie soļi ===" -ForegroundColor Cyan
Write-Host "1. Pārbaudi connection string failā backend\app\config.py"
Write-Host "2. Palaid backend direktorijā:"
Write-Host "   pip install -r requirements.txt"
Write-Host "   alembic upgrade head"
Write-Host "3. Palaid backend: uvicorn app.main:app --reload"

Write-Host ""
Write-Host "=== Vides mainīgais (optional) ===" -ForegroundColor Cyan
Write-Host "Vari iestatīt vides mainīgo DATABASE_URL:"
Write-Host '$env:DATABASE_URL="postgresql://invoice_user:invoice_password@localhost:5432/invoice_processing_db"'
