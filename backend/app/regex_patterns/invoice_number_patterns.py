INVOICE_NUMBER_PATTERNS = [
    r"(?i)pavadz[īi]me\s+nr\.?\s*([A-Z0-9\-\/]+)",
    r"(?i)invoice\s+no\.?\s*[\:\s]*([A-Z0-9\-\/]+)",
    r"(?i)dokuments?\s+nr\.?\s*([A-Z0-9\-\/]+)",
    r"(?i)nr\.?\s*([A-Z0-9]{2,}\/\d{2,4})",  # Format: 0715/25
    r"(?i)pv\s+([A-Z0-9\-\/]+)",
    r"(?i)re[kķ]ins?\s+nr\.?\s*([A-Z0-9\-\/]+)",
    # Lindström specific - RēķinaNr. 71068107
    r"(?i)r[eē][kķ]ina\s*nr\.?\s*([A-Z0-9\-\/]+)",
    # Specifiski patterni no testiem
    r"marts\s+Nr\.\s*([A-Z0-9\/\-]+)",
    r"(\b[A-Z]{2,}\d{7,}\b)",  # VIS2508271 stils
    r"(\b\d{8}\b)",  # 8-digit number like 71068107
]
