#!/usr/bin/env python3
"""
Pievieno jaunos piegādātāja bankas laukus datubāzē
"""

import sys
import os

# Pievienot backend ceļu
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.database import engine
from sqlalchemy import text

def add_supplier_bank_fields():
    """Pievieno jaunos piegādātāja bankas laukus"""
    
    try:
        with engine.connect() as conn:
            # Pārbaudam vai lauki jau eksistē
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'invoices' 
                AND column_name IN ('supplier_bank_name', 'supplier_swift_code')
            """))
            
            existing_columns = [row[0] for row in result]
            
            # Pievienojam supplier_bank_name ja neeksistē
            if 'supplier_bank_name' not in existing_columns:
                conn.execute(text("ALTER TABLE invoices ADD COLUMN supplier_bank_name VARCHAR(255);"))
                print("✅ Pievienots lauks: supplier_bank_name")
            else:
                print("ℹ️  Lauks supplier_bank_name jau eksistē")
            
            # Pievienojam supplier_swift_code ja neeksistē
            if 'supplier_swift_code' not in existing_columns:
                conn.execute(text("ALTER TABLE invoices ADD COLUMN supplier_swift_code VARCHAR(20);"))
                print("✅ Pievienots lauks: supplier_swift_code")
            else:
                print("ℹ️  Lauks supplier_swift_code jau eksistē")
            
            # Commit izmaiņas
            conn.commit()
            print("🎉 Datubāzes migrācija pabeigta!")
            
    except Exception as e:
        print(f"❌ Kļūda pievienojot laukus: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 Pievienojam jaunos piegādātāja bankas laukus...")
    success = add_supplier_bank_fields()
    
    if success:
        print("\n✅ Viss kārtībā! Tagad varat restartēt backend serveri.")
    else:
        print("\n❌ Migrācija neizdevās. Pārbaudiet kļūdu ziņojumus.")
