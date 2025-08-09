"""
OCR servisa modulis
Sadalīts moduļos strukturētai pieejai
"""

from .ocr_main import OCRService
from .image_preprocessor import ImagePreprocessor
from .text_cleaner import TextCleaner
from .tesseract_config import TesseractManager
from .pdf_processor import PDFProcessor

__all__ = [
    'OCRService',
    'ImagePreprocessor', 
    'TextCleaner',
    'TesseractManager',
    'PDFProcessor'
]
