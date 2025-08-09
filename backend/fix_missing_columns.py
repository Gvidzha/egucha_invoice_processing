"""
Pievieno trūkstošos laukus Invoice tabulai
"""
from app.database import get_db
from sqlalchemy import text

def add_missing_columns():
    db = next(get_db())
    
    # Trūkstošie lauki ar to tipiem
    missing_columns = [
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS extracted_text TEXT;",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS ocr_confidence DOUBLE PRECISION;",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS ocr_strategy VARCHAR(50);",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS invoice_number VARCHAR(100);",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS vat_amount DOUBLE PRECISION;",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS address TEXT;",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS started_at TIMESTAMP;"
    ]
    
    print("Pievienoju trūkstošos laukus...")
    
    for sql in missing_columns:
        try:
            print(f"Izpildīju: {sql}")
            db.execute(text(sql))
            db.commit()
            print("✓ Veiksmīgi")
        except Exception as e:
            print(f"✗ Kļūda: {e}")
            db.rollback()
    
    print("\nPārbauda rezultātu...")
    
    # Pārbauda rezultātu
    result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'invoices' ORDER BY ordinal_position"))
    columns = [row[0] for row in result]
    
    print("Visi lauki tagad:")
    for col in columns:
        print(f"- {col}")
    
    db.close()

if __name__ == "__main__":
    add_missing_columns()
