#!/usr/bin/env python3
"""
PostgreSQL savienojuma un tabulu tests
Palaidīt ar: python test_db.py
"""

import sys
import os
from pathlib import Path

# Pievienot app ceļu
sys.path.append(str(Path(__file__).parent / "app"))

from app.database import engine, create_tables, SessionLocal
from app.models import Supplier, Invoice
from app.config import DATABASE_URL
from sqlalchemy import text

def test_connection():
    """Testē datubāzes savienojumu"""
    print("🔍 Testējam PostgreSQL savienojumu...")
    print(f"📍 Database URL: {DATABASE_URL}")
    
    try:
        # Testēt savienojumu
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL savienojums veiksmīgs!")
            print(f"📊 PostgreSQL versija: {version}")
            return True
            
    except Exception as e:
        print(f"❌ Datubāzes savienojuma kļūda: {e}")
        print("\n🔧 Iespējamie risinājumi:")
        print("1. Pārbaudīt vai PostgreSQL darbojas: net start postgresql-x64-14")
        print("2. Pārbaudīt datubāzes esamību: psql -U postgres -l")
        print("3. Palaist setup: .\\setup_postgres.ps1")
        return False

def test_tables():
    """Testē tabulu izveidi"""
    print("\n🔍 Testējam tabulu izveidi...")
    
    try:
        # Izveidot tabulas
        create_tables()
        print("✅ Tabulas izveidotas veiksmīgi!")
        
        # Testēt tabulu esamību
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result.fetchall()]
            expected_tables = ['suppliers', 'invoices', 'products', 'error_corrections']
            
            print(f"📊 Atrasts tabulas: {tables}")
            
            for table in expected_tables:
                if table in tables:
                    print(f"✅ Tabula '{table}' eksistē")
                else:
                    print(f"❌ Tabula '{table}' nav atrasta")
                    
        return True
        
    except Exception as e:
        print(f"❌ Tabulu izveides kļūda: {e}")
        return False

def test_data_operations():
    """Testē pamata CRUD operācijas"""
    print("\n🔍 Testējam datu operācijas...")
    
    try:
        db = SessionLocal()
        
        # Testēt INSERT
        test_supplier = Supplier(
            name="TEST SUPPLIER",
            name_variations='["TEST SUPPLIER", "Test Supplier"]',
            is_verified=True
        )
        
        db.add(test_supplier)
        db.commit()
        print("✅ INSERT operācija veiksmīga")
        
        # Testēt SELECT
        suppliers = db.query(Supplier).all()
        print(f"✅ SELECT operācija veiksmīga, atrasti {len(suppliers)} piegādātāji")
        
        # Testēt UPDATE
        test_supplier.accuracy_rate = 0.95
        db.commit()
        print("✅ UPDATE operācija veiksmīga")
        
        # Testēt DELETE
        db.delete(test_supplier)
        db.commit()
        print("✅ DELETE operācija veiksmīga")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Datu operāciju kļūda: {e}")
        return False

def main():
    """Galvenā testa funkcija"""
    print("🚀 PostgreSQL datubāzes tests sākas...\n")
    
    success = True
    
    # Testēt savienojumu
    if not test_connection():
        success = False
    
    # Testēt tabulas
    if success and not test_tables():
        success = False
    
    # Testēt datu operācijas
    if success and not test_data_operations():
        success = False
    
    print("\n" + "="*50)
    if success:
        print("🎉 Visi testi izpildīti veiksmīgi!")
        print("✅ PostgreSQL datubāze ir gatava lietošanai")
        print("\n🚀 Nākamie soļi:")
        print("1. Palaidīt backend: uvicorn app.main:app --reload")
        print("2. Atvērt API docs: http://localhost:8000/docs")
    else:
        print("❌ Daži testi neizdevās")
        print("🔧 Lūdzu novērsiet kļūdas un palaidiet vēlreiz")
    
    print("="*50)

if __name__ == "__main__":
    main()
