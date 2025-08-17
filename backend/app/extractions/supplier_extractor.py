import re
from typing import Optional

def extract_supplier_name(text: str) -> Optional[str]:
    """
    Atrod piegādātāja nosaukumu no teksta.
    Aptver dažādus iespējamos apzīmējumus.
    """
    patterns = [
        r'Piegādātājs[:\- ]+([A-Za-zĀ-ž0-9\s\.\-]+)',
        r'Preču piegādātājs[:\- ]+([A-Za-zĀ-ž0-9\s\.\-]+)',
        r'Preču/pakalpojumu piegādātājs[:\- ]+([A-Za-zĀ-ž0-9\s\.\-]+)',
        r'Pakalpojumu sniedzējs[:\- ]+([A-Za-zĀ-ž0-9\s\.\-]+)',
        r'Preču nosūtītājs[:\- ]+([A-Za-zĀ-ž0-9\s\.\-]+)',
        # ...pievieno vēl pēc vajadzības...
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def extract_supplier_reg_number(text: str) -> Optional[str]:
    """
    Atrod piegādātāja reģistrācijas numuru no teksta.
    Piemērs: "Reģ. nr. 40003012345"
    """
    match = re.search(r'Reģ\.?\s*nr\.?\s*([0-9]{6,12})', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None