from typing import Optional, List
import re

def extract_supplier_reg_number(text: str, patterns: List[str]) -> Optional[str]:
    """
    Atrod piegādātāja reģistrācijas numuru no teksta, izmantojot ārējos regex patternus.
    """
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match[1].strip()
    return None