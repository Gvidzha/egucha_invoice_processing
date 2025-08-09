#!/usr/bin/env python3
"""
Manuāla tabulu izveide - debug script
"""

import sys
from pathlib import Path

# Pievienot app ceļu
sys.path.append(str(Path(__file__).parent))

from app.database import engine, Base
from app.config import DATABASE_URL

# Explicit imports lai nodrošinātu, ka visi modeļi ir ielādēti
from app.models import Invoice, Supplier, Product, ErrorCorrection

def main():
    print("🔧 Manual table creation script")
    print(f"📍 Database URL: {DATABASE_URL}")
    print(f"🏗️ Registered tables in metadata: {list(Base.metadata.tables.keys())}")
    
    try:
        # Drop visas tabulas (ja pastāv)
        print("🗑️ Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
        
        # Izveidot visas tabulas
        print("🏗️ Creating all tables...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Tables created successfully!")
        
        # Pārbaudīt rezultātu
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Created tables: {tables}")
            
            # Pārbaudīt invoices tabulas kolonnas
            if 'invoices' in tables:
                result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'invoices' ORDER BY ordinal_position"))
                columns = [row[0] for row in result.fetchall()]
                print(f"📄 Invoices columns: {columns}")
                
                if 'product_summary' in columns:
                    print("✅ product_summary column exists!")
                else:
                    print("❌ product_summary column MISSING!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
