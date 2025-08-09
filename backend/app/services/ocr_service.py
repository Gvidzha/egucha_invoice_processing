"""
OCR (Optical Character Recognition) serviss
Modulārs OCR serviss ar strukturētu pieeju
"""

from .ocr import OCRService
from .ocr.tesseract_config import TesseractManager
from .ocr.image_preprocessor import ImagePreprocessor
from .ocr.text_cleaner import TextCleaner
from .ocr.pdf_processor import PDFProcessor

# Eksportē galvenos klases publiskai lietošanai
__all__ = [
    'OCRService',
    'TesseractManager',
    'ImagePreprocessor', 
    'TextCleaner',
    'PDFProcessor'
]

# Backward compatibility - izveidot default instance
default_ocr_service = None

async def get_ocr_service() -> OCRService:
    """
    Atgriež konfigurētu OCR servisa instanci
    
    Returns:
        OCRService: Gatavs OCR serviss
    """
    global default_ocr_service
    
    if default_ocr_service is None:
        default_ocr_service = OCRService()
        await default_ocr_service.initialize()
    
    return default_ocr_service

# Legacy funkcijas backward compatibility
async def extract_text_from_image(image_path: str) -> dict:
    """Legacy funkcija - izmanto jauno OCR servisu"""
    ocr_service = await get_ocr_service()
    return await ocr_service.extract_text_from_image(image_path)

async def extract_text_from_pdf(pdf_path: str) -> dict:
    """Legacy funkcija - izmanto jauno OCR servisu"""
    ocr_service = await get_ocr_service()
    return await ocr_service.extract_text_from_pdf(pdf_path)
