DATE_PATTERNS = [
    r"(\d{4})[\.\/\-](\d{1,2})[\.\/\-](\d{1,2})",  # YYYY-MM-DD
    r"(\d{1,2})[\.\/\-](\d{1,2})[\.\/\-](\d{4})",  # DD-MM-YYYY
    r"(\d{4})\.\s*gada\s*(\d{1,2})\.\s*(janvāris|februāris|marts|aprīlis|maijs|jūnijs|jūlijs|augusts|septembris|oktobris|novembris|decembris)",
    r"(?i)datums?[\s:]*(\d{1,2}[\./\-]\d{1,2}[\./\-]\d{2,4})",
    # Lindström specific - 31. 05. 2025
    r"(?i)izrakstibanasdat\.?\s*(\d{1,2})\.?\s*(\d{1,2})\.?\s*(\d{4})",
    # Specifiski patterni
    r"gada(\d{1,2}),?\s*(maijs|maljs)",  # "gada7, maijs"
]

DELIVERY_DATE_PATTERNS = [
    r"(\d{4}.\sgads\s\d{2}.\s*[a-zāčēģīķļņšūž]+)",
    r"(?i)piegādes\s*datums[:\s]*([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})",
    r"(?i)delivery\s*date[:\s]*([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})",
    r"(?i)datums\s*([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})",
]

SERVICE_DELIVERY_DATE_PATTERNS = [
    r"Pakalpojumu sniegšanas periods:\s*(\d{4}.\sgads\s[a-zāčēģīķļņšūž]+)",
    r"(?i)piegādes\s*datums[:\s]*([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})",
    r"(?i)delivery\s*date[:\s]*([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})",
    r"(?i)datums\s*([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})",
]