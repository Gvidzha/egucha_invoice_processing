"""
Pārbauda Invoice tabulas struktūru
"""
from app.database import get_db
from sqlalchemy import text

def check_invoice_table():
    db = next(get_db())
    result = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'invoices' ORDER BY ordinal_position"))
    
    print('Pašreizējie Invoice tabulas lauki:')
    existing_columns = []
    for row in result:
        print(f'- {row[0]}: {row[1]}')
        existing_columns.append(row[0])
    
    # Visi lauki no Invoice modeļa
    needed_fields = [
        'extracted_text',      # Trūkst!
        'ocr_confidence',      # Trūkst!
        'ocr_strategy',        # Trūkst!
        'invoice_number',      # Trūkst!
        'vat_amount',          # Trūkst!
        'address',             # Trūkst!
        'uploaded_at',         # Trūkst!
        'started_at',          # Trūkst!
        'processing_status',
        'error_message', 
        'processing_started_at',
        'processing_completed_at',
        'bank_account',
        'reg_number'
    ]
    
    print('\nJāpievieno lauki:')
    missing_fields = []
    for field in needed_fields:
        if field not in existing_columns:
            missing_fields.append(field)
            print(f'+ {field}')
        else:
            print(f'✓ {field} jau eksistē')
    
    return missing_fields

if __name__ == "__main__":
    missing = check_invoice_table()
    print(f'\nTrūkst {len(missing)} lauki')
