"""
Aplikācijas konfigurācijas iestatījumi
Satur datubāzes savienojumu, OCR iestatījumus un regex patterns
"""

import os
from pathlib import Path
        
        # Specifiskāri patterni ar kontekstu 
        r"(?i)piegādātājs[\s:]*([^\n\r,]+?)(?:\s*Reg|$|\n)",
        r"(?i)supplier[\s:]*([^\n\r,]+?)(?:\s*Reg|$|\n)", 
        r"(?i)SIA\s*([A-ZĀĒĪŌŪšģķļņčžāēīōū\-\s\"]{2,30})(?:\s*Reg|\s*nr|\s*$|\n)",
        r"(?i)SIA\s*\"([^\"]{2,30})\"",
        r"(?i)AS\s*\"([^\"]{2,30})\"",
        r"(?i)AS\s+([A-ZĀĒĪŌŪšģķļņčžāēīōū\-\s]{2,30})(?:\s*Reg|\s*$|\n)",
        r"(?i)Z\/S\s+([A-ZĀĒĪŌŪšģķļņčžāēīōū\-\s]{2,20})(?:\s*Reg|\s*$|\n)",
        # Patterni ar "egadatajs" (no TIM-T rezultāta)
        r"egadatajs[,\s]*SIA\s*([A-ZĀĒĪŌŪšģķļņčžāēīōū\-\s]{2,20})",
        r"([A-ZĀĒĪŌŪšģķļņčžāēīōū\-]{2,15})\s*Reg\.\s*Nr\.\s*\d+",
        # Uzņēmuma kods ar nosaukumu
        r"SIA\s*([A-ZĀĒĪŌŪšģķļņčžāēīōū\-]{2,15})\s*Reg",umus, failu ceļus, utt.
"""

import os
from pathlib import Path
from app.env_loader import load_env_file, get_env

# Ielādēt .env failu
load_env_file()

# Projekta saknes direktorija
BASE_DIR = Path(__file__).parent.parent.parent

# PostgreSQL datubāzes iestatījumi
DATABASE_URL = get_env(
    "DATABASE_URL", 
    "postgresql://invoice_user:invoice_password@localhost:5432/invoice_processing_db"
)

# Failu glabāšanas iestatījumi
UPLOAD_DIR = Path(get_env("UPLOAD_DIR", str(BASE_DIR / "uploads")))
MAX_FILE_SIZE = int(get_env("MAX_FILE_SIZE", "10485760"))  # 10MB default
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}

# OCR iestatījumi
TESSERACT_PATH = get_env("TESSERACT_PATH", "tesseract")  # Default: use PATH
TESSERACT_CONFIG = {
    "lang": "lav+eng",  # Latviešu + angļu valoda
    "config": "--oem 3 --psm 6 --dpi 300",  # OCR Engine Mode 3, Page Segmentation Mode 6, DPI 300
    "timeout": 30,  # Timeout seconds
    "char_whitelist": "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzĀĒĪŌŪāēīōūčĢģĶķĻļŅņŠšŽž.,€$%-()/"
}

# OCR priekšapstrādes iestatījumi
IMAGE_PREPROCESSING = {
    "enable": True,
    "invoice_mode": True,
    "target_dpi": 300,
    "enhancement_level": "medium",  # low, medium, high
    "denoise": True,
    "auto_rotate": True,
    "binarize": True
}

# PDF apstrādes iestatījumi
PDF_CONFIG = {
    "max_pages": int(get_env("PDF_MAX_PAGES", "10")),  # Maksimālais lapu skaits
    "conversion_dpi": 300,
    "direct_text_threshold": 50,  # Minimālais teksta garums direct extraction
    "ocr_fallback": True
}

# Temp failu iestatījumi
TEMP_DIR = Path(get_env("TEMP_DIR", str(BASE_DIR / "temp")))
TEMP_CLEANUP_HOURS = int(get_env("TEMP_CLEANUP_HOURS", "24"))  # Cik stundās dzēst temp failus

# Regex patterns pavadzīmju apstrādei (balstīti uz reāliem OCR rezultātiem)
REGEX_PATTERNS = {
    # Pavadzīmes numurs - Nr. VIS2508271, Nr. 0715/25, Invoice No: INV-2024-001, PV 456/2024
    "invoice_number": [
        # Specifiskāki patterni ar kontekstu
        r"(?i)(?:pavadzīme|invoice|dokuments)\s*nr\.?\s*([A-Z0-9]{3,}[\/\-]?\d*)",
        r"(?i)(?:pavadzīme|invoice)\s*(?:nr|no|number)\.?[\s:]*([A-Z]{2,}\d+)",
        r"(?i)nr\.?\s*([A-Z]{2,}\d{4,})",  # Nr. VIS2508271
        r"(?i)nr\.?\s*(\d{4}\/\d{2})",     # Nr. 0715/25
        r"(?i)invoice\s*(?:nr|no|number)\.?[\s:]*([A-Z0-9\-]{3,})",
        r"(?i)dokuments\s*nr\.?\s*([A-Z]{2,}[\-\d]+)",
        r"(?i)(?:PV|INV)[\s\-]*(\d{3,}[\-\/]\d+)",
    ],
    
    # Uzņēmuma nosaukums - uzlaboti patterni
    "supplier": [
        # Specifiskāki patterni ar kontekstu 
        r"(?i)piegādātājs[\s:]*([^\n\r,]+?)(?:\s*Reg|$|\n)",
        r"(?i)supplier[\s:]*([^\n\r,]+?)(?:\s*Reg|$|\n)", 
        r"(?i)SIA\s*([A-ZĀĒĪŌŪšģķļņčžāēīōū\-\s\"]{2,30})(?:\s*Reg|\s*nr|\s*$|\n)",
        r"(?i)SIA\s*\"([^\"]{2,30})\"",
        r"(?i)AS\s*\"([^\"]{2,30})\"",
        r"(?i)AS\s+([A-ZĀĒĪŌŪšģķļņčžāēīōū\-\s]{2,30})(?:\s*Reg|\s*$|\n)",
        r"(?i)Z\/S\s+([A-ZĀĒĪŌŪšģķļņčžāēīōū\-\s]{2,20})(?:\s*Reg|\s*$|\n)",
        # Patterni ar "egadatajs" (no TIM-T rezultāta)
        r"egadatajs[,\s]*SIA\s*([A-ZĀĒĪŌŪšģķļņčžāēīōū\-\s]{2,20})",
        r"([A-ZĀĒĪŌŪšģķļņčžāēīōū\-]{2,15})\s*Reg\.\s*Nr\.\s*\d+",
        # Uzņēmuma kods ar nosaukumu
        r"SIA\s*([A-ZĀĒĪŌŪšģķļņčžāēīōū\-]{2,15})\s*Reg",
    ],
    
    # Datumi - uzlaboti patterni
    "date": [
        r"(\d{4})\.?\s*gada?\s*(\d{1,2})\.?\s*(janvāris|februāris|marts|aprīlis|maijs|jūnijs|jūlijs|augusts|septembris|oktobris|novembris|decembris)",
        r"(\d{4})\.\s*gada\s*(\d{1,2})\.\s*(marts|maijs)",  # Specifisks TIM-T formāts
        r"(\d{1,2})\.(\d{1,2})\.(\d{4})",
        r"(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})",
        r"(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})",
        r"datums?\s*(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})",
    ],
    
    # Kopējā summa - uzlaboti patterni
    "total": [
        r"(?i)[Kk]op[aā]\s*(?:apmaks[aā]i?)?\s*[\:\s]*(?:\(EUR\))?\s*([0-9\s,\.]+)\s*EUR?",
        r"(?i)summa\s*k[oō]p[aā]\s*(?:\(EUR\))?\s*([0-9\s,\.]+)",
        r"(?i)total[\:\s]*([0-9\s,\.]+)\s*EUR?",
        r"(?i)kopā\s*ar\s*atlaidi\s*([0-9\s,\.]+)",
        r"(?i)kopā[\:\s]*([0-9\s,\.]+)",
        r"(?i)KOPĀ\s+([0-9,\.]+)",
        r"summa\s*kopā\s*([0-9\s,\.]+)€?",
        # Tim-T formāts: Summakopa(EUR)751,71
        r"(?i)Summakopa\s*\(EUR\)\s*([0-9,\.]+)",
        # Kopaapmaksai formāts
        r"(?i)Kopaapmaksai\s*EUR\s*([0-9\s,\.]+)",
        # Ar Total:
        r"(?i)Total:\s*([0-9,\.]+)",
        # Bez EUR
        r"(?i)Total:\s*([0-9,\.]+)(?!\s*EUR)",
    ],
    
    # PVN - uzlaboti patterni
    "vat": [
        r"(?i)PVN\s*21%\s*(?:\(EUR\))?\s*([0-9\s,\.]+)",
        r"(?i)PVN\s*21%\s*([0-9\s,\.]+)",
        r"(?i)VAT\s*21%\s*([0-9\s,\.]+)",
        r"(?i)nodoklis\s*([0-9\s,\.]+)",
        # Precīzāks pattern Tim-T formātam
        r"PVN21%\s*\(EUR\)\s*([0-9,\.]+)",
    ],
    
    # Produkti/preces - konservatīvāki patterni
    "products": [
        # Tikai precīzi produktu patterni ar kodiem
        r"([0-9]{10,})\s+([A-ZĀĒĪŌŪšģķļņčžāēīōū][^0-9\n]{10,40}?)\s+(\d+[,\.]\d{3})\s*kg\s*(\d+[,\.]\d+)\/21%",
        # Ar produkta kodu un skaidru struktūru
        r"([0-9]{12,})\s+([A-ZĀĒĪŌŪšģķļņčžāēīōū][^0-9\n]{5,40}?)\s+kg\s*(\d+[,\.]\d{3})\s*(\d+[,\.]\d+)",
    ],
    
    # Reģistrācijas numurs - uzlaboti patterni
    "reg_number": [
        r"(?i)Reg\.?\s*Nr\.?\s*([0-9]{11})",  # Precīzs 11 ciparu numurs
        r"(?i)registration\s*(?:number|nr)\.?\s*([0-9]{11})",
        r"nr\.\s*([0-9]{11})",  # Īsāks variants
        # Konteksts ar SIA
        r"SIA\s+[^0-9]*Reg\.\s*nr\.\s*([0-9]{11})",
    ],
    
    # Juridiskā adrese - uzlaboti patterni  
    "address": [
        # Precīzāki patterni ar kontekstu
        r"(?i)Jurid(?:iskā)?\s*adrese[:/]?\s*([^\n\r]+?)(?:\s*PVN|\s*Norekin|\s*$)",
        r"(?i)juridiska\s*adrese[:/]?\s*([^\n\r]+?)(?:\s*konts|\s*$)",
        r"(?i)legal\s*address[:/]?\s*([^\n\r]+?)(?:\s*PVN|\s*$)",
        r"(?i)adrese[:/]?\s*([A-ZĀĒĪŌŪšģķļņčžāēīōū][^\n\r]+?)(?:\s*PVN|\s*konts|\s*$)",
        # Adrese ar pasta indeksu
        r"([A-ZĀĒĪŌŪšģķļņčžāēīōū][^,\n]+,\s*[A-ZĀĒĪŌŪšģķļņčžāēīōū]+,\s*LV-\d{4})",
        # Caunuiela formāts
        r"([A-ZĀĒĪŌŪšģķļņčžāēīōū]iela\s*\d+[^,]*,\s*[A-ZĀĒĪŌŪšģķļņčžāēīōū]+,\s*[^,\n]*LV-\d{4})",
    ],
    
    # Banka un konts - uzlaboti patterni
    "bank_account": [
        r"(?i)konts\s*([A-Z]{2}\d{2}[A-Z0-9]{13,})",  # IBAN formāts
        r"(?i)account[:\s]*([A-Z]{2}\d{2}[A-Z0-9]{13,})",
        r"(?i)IBAN[:\s]*([A-Z]{2}\d{2}[A-Z0-9]{13,})",
        r"konts\s*([A-Z0-9]{15,})",  # Vienkāršāks konts
        # Specifisks LV konts
        r"(LV\d{2}[A-Z]{4}\d{13})",
    ]
}

# Mašīnmācīšanās iestatījumi
CONFIDENCE_THRESHOLD = float(get_env("CONFIDENCE_THRESHOLD", "0.7"))
LEARNING_ENABLED = get_env("LEARNING_ENABLED", "True").lower() == "true"

# Drošības iestatījumi
SECRET_KEY = get_env("SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = get_env("DEBUG", "False").lower() == "true"

# Logging iestatījumi
LOG_LEVEL = get_env("LOG_LEVEL", "INFO")

# Settings klase un funkcija
class Settings:
    """Konfigurācijas iestatījumu klase"""
    def __init__(self):
        self.database_url = DATABASE_URL
        self.upload_dir = UPLOAD_DIR
        self.max_file_size = MAX_FILE_SIZE
        self.allowed_extensions = ALLOWED_EXTENSIONS
        self.tesseract_path = TESSERACT_PATH
        self.tesseract_config = TESSERACT_CONFIG
        self.image_preprocessing = IMAGE_PREPROCESSING
        self.pdf_config = PDF_CONFIG
        self.temp_dir = TEMP_DIR
        self.temp_cleanup_hours = TEMP_CLEANUP_HOURS
        self.regex_patterns = REGEX_PATTERNS
        self.confidence_threshold = CONFIDENCE_THRESHOLD
        self.learning_enabled = LEARNING_ENABLED
        self.secret_key = SECRET_KEY
        self.debug = DEBUG
        self.log_level = LOG_LEVEL

def get_settings() -> Settings:
    """Atgriež aplikācijas iestatījumus"""
    return Settings()