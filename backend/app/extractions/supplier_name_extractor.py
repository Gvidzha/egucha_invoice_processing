import re
from typing import Optional, Tuple, List

def _calculate_supplier_confidence(supplier_clean: str) -> float:
    confidence = 0.7
    if any(word in supplier_clean.upper() for word in ['SIA', 'AS', 'Z/S']):
        confidence += 0.1
    if 3 < len(supplier_clean) < 50:
        confidence += 0.1
    return min(confidence, 1.0)

def extract_supplier_name(text: str, patterns: List[str]) -> Tuple[Optional[str], float]:
    """
    Atrod piegādātāja nosaukumu tekstā, izmantojot regex patternus.
    """
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            supplier = (match[1] if match.groups() else match[0]).strip().strip('"\'.,;')
            confidence = _calculate_supplier_confidence(supplier)
            return supplier, confidence
    return None, 0.0
