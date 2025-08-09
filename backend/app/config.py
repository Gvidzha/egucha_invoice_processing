"""
Aplikācijas konfigurācijas iestatījumi
Satur datubāzes savienojumu, OCR iestatījumus un regex patterns
"""

import os
from pathlib import Path
from app.env_loader import load_env_file, get_env

# Ielādēt .env failu
load_env_file()

# Projekta saknes direktorija
BASE_DIR = Path(__file__).parent.parent.parent

# Datubāzes iestatījumi
DATABASE_URL = get_env("DATABASE_URL", "postgresql://postgres:password@localhost:5432/invoice_db")

# Uploads direktorija
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Failu ierobežojumi
MAX_FILE_SIZE = int(get_env("MAX_FILE_SIZE", "10485760"))  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".bmp"}  # Atļautie failu paplašinājumi

# OCR iestatījumi
TESSERACT_CMD = get_env("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSERACT_CONFIG = {
    "lang": "lav+eng+deu",  # Latviešu, angļu, vācu valodas
    "config": "--oem 3 --psm 6",  # OCR Engine Mode un Page Segmentation Mode
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

# Datu ekstraktēšanas iestatījumi
CONFIDENCE_THRESHOLD = 0.5  # Minimālais confidence score

# Mašīnmācīšanās iestatījumi
LEARNING_ENABLED = True  # Vai ieslēgt mašīnmācīšanos
LEARNING_CONFIG = {
    "min_examples": 5,  # Minimālais piemēru skaits pattern ģenerēšanai
    "confidence_boost": 0.1,  # Uzticamības palielināšana mācīšanās rezultātā
    "max_patterns_per_field": 20,  # Maksimālais pattern skaits katram laukam
    "pattern_expiry_days": 30,  # Pattern derīgums dienās
    "auto_cleanup": True,  # Automātiska vecu pattern dzēšana
}

# NER un AI ekstraktēšanas iestatījumi
NER_CONFIG = {
    "enabled": True,
    "model_path": "./models/ner",
    "learning_data_path": "./data/learning",
    "confidence_threshold": 0.7,
    "max_learning_examples": 1000,
    "pattern_cache_size": 500,
    "auto_save_interval": 10,  # Saglabā katrus 10 piemērus
    "fallback_to_regex": True,  # Ja NER neizdodas, izmanto regex
    "enable_continuous_learning": True
}

# Hibridās ekstraktēšanas iestatījumi
HYBRID_EXTRACTION = {
    "use_ner": True,
    "combine_confidence": True,
    "ner_weight": 0.6,  # NER rezultātu svars kombinācijā
    "regex_weight": 0.4,  # Regex rezultātu svars kombinācijā
    "min_agreement_threshold": 0.8  # Minimālā saskaņa starp metodēm
}

# PDF apstrādes iestatījumi
PDF_CONFIG = {
    "max_pages": int(get_env("PDF_MAX_PAGES", "10")),  # Maksimālais lapu skaits
    "conversion_dpi": 300,
    "direct_text_threshold": 50,  # Minimālais teksta garums direct extraction
    "ocr_fallback": True
}

# Regex patterni datu ekstraktēšanai
REGEX_PATTERNS = {
    # Pavadzīmes numurs - uzlaboti patterni
    "invoice_number": [
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
    ],
    
    # Uzņēmuma nosaukums - uzlaboti patterni
    "supplier": [
        # Lindström specific patterns
        r"(?i)lindstr[oō]m\s*SIA",
        r"(?i)SIA\s*lindstr[oō]m",
        r"(?i)lindstr[oō]m",
        
        # Specifiskie uzņēmumi (Liepājas Pētertirgus)
        r"(?i)(?:Liep[aā]j[aā]s?\s*)?(?:P[eē]ter[ti]|peter[ti]|pēter[ti])[^\n\r]*?(?:tirgus?|TIRGUS?|ertirg)",
        r"peterstirgus\.lv",  # Email domain atpazīšana
        r"(?i)ertirg\s*uss?\s*SIA",  # Fragmentēts "TIRGUS SIA"
        r"(?i)(?:3\s*ļ\.\s*)?Liep[aā]\s*[^\n\r]*?P[eē]ter",  # "3 ļ. Liepā... Pēter"
        
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
        r"SIA\s*([A-ZĀĒĪŌŪšģķļņčžāēīōū\-]{2,15})\s*Reg",
    ],
    
    # Datums - dažādi formāti
    "date": [
        r"(\d{4})[\.\/\-](\d{1,2})[\.\/\-](\d{1,2})",  # YYYY-MM-DD
        r"(\d{1,2})[\.\/\-](\d{1,2})[\.\/\-](\d{4})",  # DD-MM-YYYY
        r"(\d{4})\.\s*gada\s*(\d{1,2})\.\s*(janvāris|februāris|marts|aprīlis|maijs|jūnijs|jūlijs|augusts|septembris|oktobris|novembris|decembris)",
        r"(?i)datums?[\s:]*(\d{1,2}[\./\-]\d{1,2}[\./\-]\d{2,4})",
        # Lindström specific - 31. 05. 2025
        r"(?i)izrakstibanasdat\.?\s*(\d{1,2})\.?\s*(\d{1,2})\.?\s*(\d{4})",
        # Specifiski patterni
        r"gada(\d{1,2}),?\s*(maijs|maljs)",  # "gada7, maijs"
    ],
    
    # Kopējā summa - uzlaboti patterni
    "total": [
        r"(?i)kop[aā]\s*[:\-]?\s*([0-9\s,\.]+)\s*EUR",
        r"(?i)total\s*[:\-]?\s*([0-9\s,\.]+)",  # Total: 150,75
        r"(?i)summa\s*kop[aā]\s*([0-9\s,\.]+)",
        r"(?i)summakopa\s*\(EUR\)\s*([0-9\s,\.]+)",  # No TIM-T
        r"(?i)kopaapmaksai\s*EUR\s*([0-9\s,\.]+)",  # No Liepājas
        r"(?i)KOPĀ\s*([0-9\s,\.]+)",
        r"(?i)summa\s*bez\s*atlaides\s*([0-9\s,\.]+)",
        # Lindström specific - Apmaksai(EUR). 31,46
        r"(?i)apmaksai\s*\(EUR\)\.?\s*([0-9\s,\.]+)",
        r"([0-9,\.]+)\s*€",
    ],
    
    # PVN summa
    "vat": [
        r"(?i)PVN\s*21%\s*[:\(]?\s*([0-9\s,\.]+)",
        r"(?i)VAT\s*21%\s*[:\(]?\s*([0-9\s,\.]+)",
        r"(?i)nodoklis\s*([0-9\s,\.]+)",
        r"(?i)PVN\s*([0-9\s,\.]+)",
    ],
    
    # Reģistrācijas numurs
    "reg_number": [
        r"(?i)Reg\.?\s*[Nn]r\.?\s*([0-9]{8,12})",
        r"(?i)reģ\.?\s*[Nn]r\.?\s*([0-9]{8,12})",
        r"(?i)registration\s*no\.?\s*([0-9]{8,12})",
        # Lindström specific - Reg. Nr. 40003237187
        r"(?i)reg\.?\s*nr\.?\s*([0-9]{8,12})",
        r"(?i)PVNNr\.?\s*LV([0-9]{8,12})",  # PVNNr. LV40003237187
        r"([0-9]{11})",  # 11 ciparu numurs
    ],
    
    # Juridiskā adrese - uzlaboti patterni  
    "address": [
        r"(?i)juridisk[aā]\s*adrese[:\s]*([^,\n\r]+(?:,[^,\n\r]+)*?)(?:\s*PVN|$|\n)",
        r"(?i)adrese[:\s]*([^,\n\r]+(?:,[^,\n\r]+)*?)(?:\s*konts|$|\n)",
        r"(?i)juridisk[aā]\s*adrese\/dekl[^:]*[:\s]*([^\n\r]+?)(?:\s*PVN|$|\n)",
        r"([A-ZĀĒĪŌŪa-zāēīōūģķļņčšž]+iela\s*\d+[^,\n\r]*,\s*[A-ZĀĒĪŌŪa-zāēīōūģķļņčšž]+,\s*LV-\d{4})",
    ],
    
    # Produkti - tabulas formāts
    "products": [
        # Vienkāršs produkta pattern ar nosaukumu, daudzumu, cenu
        r"([A-ZĀĒĪŌŪa-zāēīōūģķļņčšž\s\(\)]{5,50})\s+(?:kg|gab|l|m)\s*(\d+[,\.]\d+)\s*[0-9,\.]+\s*([0-9,\.]+)",
        # Pattern ar produkta kodu
        r"([0-9]{10,15})\s+([A-ZĀĒĪŌŪa-zāēīōūģķļņčšž\s\(\)]{5,50})\s+kg\s*(\d+[,\.]\d+)\s*([0-9,\.]+)",
    ],
    
    # Bankas konts - IBAN formāts
    "bank_account": [
        r"(LV\d{2}[A-Z]{4}\d{13})",  # Latvijas IBAN
        r"(?i)konts[:\s]*(LV\d{2}[A-Z]{4}\d{13})",
    ]
}

# API iestatījumi
API_CONFIG = {
    "host": get_env("API_HOST", "localhost"),
    "port": int(get_env("API_PORT", "8000")),
    "debug": get_env("DEBUG", "True").lower() == "true",
    "workers": int(get_env("WORKERS", "1"))
}

# Logging iestatījumi
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "simple": {
            "format": "%(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "app.log",
            "mode": "a"
        }
    },
    "loggers": {
        "": {
            "level": "INFO",
            "handlers": ["console", "file"]
        }
    }
}

class Settings:
    """Konfigurācijas iestatījumu klase"""
    def __init__(self):
        self.database_url = DATABASE_URL
        self.upload_dir = UPLOAD_DIR
        self.max_file_size = MAX_FILE_SIZE
        self.allowed_extensions = ALLOWED_EXTENSIONS
        self.tesseract_cmd = TESSERACT_CMD
        self.tesseract_config = TESSERACT_CONFIG
        self.image_preprocessing = IMAGE_PREPROCESSING
        self.pdf_config = PDF_CONFIG
        self.regex_patterns = REGEX_PATTERNS
        self.confidence_threshold = CONFIDENCE_THRESHOLD
        self.api_config = API_CONFIG
        self.logging_config = LOGGING_CONFIG

def get_settings():
    """Atgriež aplikācijas iestatījumus"""
    return Settings()
