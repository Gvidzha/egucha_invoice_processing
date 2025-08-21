SUPPLIER_PATTERNS = [
    r"(?i)piegādātājs[\s:]*([^\n\r,]+?)(?:\s*Reg|$|\n)",
    r"(?i)preču nosūtītājs[\s:]*([^\n\r,]+?)(?:\s*Reg|$|\n)",
    # ...pievieno vēl variantus...
]

SUPPLIER_NAME = [
    r'Piegādātājs[:\- ]+([A-Za-zĀ-ž0-9\s\.\-]+)',
    r'Preču piegādātājs[:\- ]+([A-Za-zĀ-ž0-9\s\.\-]+)',
    r'Preču/pakalpojumu piegādātājs[:\- ]+([A-Zaž0-9\s\.\-]+)',
    r'Pakalpojumu sniedzējs[:\- ]+([A-Zaž0-9\s\.\-]+)',
    r'Preču nosūtītājs[:\- ]+([A-Zaž0-9\s\.\-]+)',
]

SUPPLIER_VAT_NUMBER = [
    r"(?i)PVN\s*Nr\.?\s*([A-Z]{2}\d{7,12})",
    r"(?i)PVN\s*([A-Z]{2}\d{7,12})",
]

SUPPLIER_REGISTRATION_NUMBER = [
    r"(?i)reģistrācijas numurs\s*([A-Z]{2}\d{7,12})",
    r"(?i)registration\s*number\s*([A-Z]{2}\d{7,12})",
    # ...pievieno vēl variantus...
]
