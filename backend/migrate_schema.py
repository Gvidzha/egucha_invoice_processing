#!/usr/bin/env python3
"""
Migrācijas skripts lai atjaunotu datubāzes shēmu
Dzēš vecās tabulas un izveido jaunās ar complete_models
"""

import sys
import os
from pathlib import Path

# Pievienot app ceļu
sys.path.append(str(Path(__file__).parent / "app"))

from app.database import engine, drop_tables, create_tables
from app.models import Base, Invoice, Product, Supplier, ErrorCorrection
from sqlalchemy import inspect

def main():
    print("🔄 DATUBĀZES SHĒMAS MIGRĀCIJA")
    print("=" * 50)
    
    # Pārbaudam pašreizējo shēmu
    print("1️⃣ Pārbaudam pašreizējo datubāzes stāvokli...")
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"   Esošās tabulas: {existing_tables}")
    
    if 'invoices' in existing_tables:
        columns = inspector.get_columns('invoices')
        column_names = [col['name'] for col in columns]
        print(f"   Invoices kolonnas ({len(column_names)}): {column_names[:10]}...")
        
        # Pārbaudam vai ir original_filename
        if 'original_filename' not in column_names:
            print("   ❌ Trūkst 'original_filename' kolonnas - nepieciešama migrācija!")
        else:
            print("   ✅ 'original_filename' kolonna eksistē")
    
    # Apstiprināšana
    print("\n2️⃣ Migrācijas process:")
    print("   - Dzēsīs visas esošās tabulas")
    print("   - Izveidosim jaunās tabulas ar pilno shēmu")
    
    response = input("\n❓ Vai turpināt? (y/N): ")
    if response.lower() != 'y':
        print("🚫 Migrācija atcelta")
        return
    
    try:
        # Dzēšam vecās tabulas
        print("\n3️⃣ Dzēšam vecās tabulas...")
        drop_tables()
        print("   ✅ Vecās tabulas dzēstas")
        
        # Izveidojam jaunās tabulas
        print("\n4️⃣ Izveidojam jaunās tabulas...")
        create_tables()
        
        # Verificējam rezultātu
        print("\n5️⃣ Verificējam rezultātu...")
        inspector = inspect(engine)
        new_tables = inspector.get_table_names()
        print(f"   Jaunās tabulas: {new_tables}")
        
        if 'invoices' in new_tables:
            columns = inspector.get_columns('invoices')
            column_names = [col['name'] for col in columns]
            print(f"   Invoices kolonnas ({len(column_names)}): {column_names[:10]}...")
            
            if 'original_filename' in column_names:
                print("   ✅ 'original_filename' kolonna izveidota!")
            else:
                print("   ❌ 'original_filename' kolonna netika izveidota!")
        
        print("\n🎉 MIGRĀCIJA PABEIGTA VEIKSMĪGI!")
        
    except Exception as e:
        print(f"\n❌ MIGRĀCIJAS KĻŪDA: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
