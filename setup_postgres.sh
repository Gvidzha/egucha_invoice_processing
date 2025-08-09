#!/bin/bash

# PostgreSQL datubāzes un lietotāja izveides skripts
# Palaidīt ar PostgreSQL admin tiesībām

echo "=== PostgreSQL datubāzes setup ==="

# Izveidot datubāzi un lietotāju
psql -U postgres -c "CREATE DATABASE invoice_processing_db;"
psql -U postgres -c "CREATE USER invoice_user WITH ENCRYPTED PASSWORD 'invoice_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE invoice_processing_db TO invoice_user;"
psql -U postgres -c "ALTER USER invoice_user CREATEDB;"

echo "Datubāze 'invoice_processing_db' un lietotājs 'invoice_user' izveidoti veiksmīgi!"

echo ""
echo "=== Connection string ==="
echo "postgresql://invoice_user:invoice_password@localhost:5432/invoice_processing_db"

echo ""
echo "=== Nākamie soļi ==="
echo "1. Pārbaudi connection string failā backend/app/config.py"
echo "2. Palaid: cd backend && alembic upgrade head"
echo "3. Palaid backend: uvicorn app.main:app --reload"
