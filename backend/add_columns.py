"""
Manuāli pievieno trūkstošos laukus Invoice tabulai
"""

from app.database import get_db
from sqlalchemy import text

def add_missing_columns():
    db = next(get_db())
    
    # Komandas lai pievienotu trūkstošos laukus
    commands = [
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS processing_status VARCHAR(50) DEFAULT 'pending'",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMP WITHOUT TIME ZONE",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS processing_completed_at TIMESTAMP WITHOUT TIME ZONE", 
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS bank_account VARCHAR(50)",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS reg_number VARCHAR(50)",
    ]
    
    try:
        for command in commands:
            print(f"Izpildām: {command}")
            db.execute(text(command))
        
        db.commit()
        print("✅ Visi lauki veiksmīgi pievienoti!")
        
    except Exception as e:
        print(f"❌ Kļūda: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_missing_columns()
