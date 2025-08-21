import re
from datetime import date
from typing import Optional, List
from app.regex_patterns.latvian_months import LATVIAN_MONTHS

def extract_invoice_date(text: str, patterns: List[str]) -> Optional[date]:
    """
    Ekstraktē pavadzīmes datumu no teksta, izmantojot regex patternus.
    """
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            try:
                if len(groups) == 3:
                    # Ja trešais grupas elements ir mēneša vārds
                    if groups[2].lower() in LATVIAN_MONTHS:
                        year, day, month_name = groups
                        month = LATVIAN_MONTHS[month_name.lower()]
                        return date(int(year), month, int(day))
                    else:
                        if len(groups[0]) == 4:  # YYYY-MM-DD formāts
                            year, month, day = groups
                        else:  # DD-MM-YYYY formāts
                            day, month, year = groups
                        return date(int(year), int(month), int(day))
            except (ValueError, IndexError):
                continue
    return None