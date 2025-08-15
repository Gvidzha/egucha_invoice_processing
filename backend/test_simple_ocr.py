#!/usr/bin/env python3
"""
Vienkāršs OCR tests ar reālu tekstu
"""
import sys
import os
sys.path.insert(0, '.')

import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pytesseract
from app.services.ocr.ocr_main import OCRService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_simple_test_image():
    """Izveido vienkāršu test attēlu ar skaidru tekstu"""
    # Izveido baltu fonu ar melnu tekstu
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Mēģinām atrast fontu, ja nav, izmantojam default
    try:
        # Windows default font
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
        except:
            font = ImageFont.load_default()
    
    # Vienkāršs teksts
    text_lines = [
        "PAVADZĪME Nr. 123456",
        "",
        "Datums: 2025-01-31",
        "Piegādātājs: SIA Test",
        "",
        "Produkti:",
        "1. Produkts A - 10.50 EUR",
        "2. Produkts B - 25.30 EUR", 
        "",
        "KOPĀ: 35.80 EUR"
    ]
    
    y_position = 50
    for line in text_lines:
        if line.strip():  # Ja nav tukša līnija
            draw.text((50, y_position), line, fill='black', font=font)
        y_position += 40
    
    # Saglabāt attēlu
    test_path = Path("test_simple.png")
    img.save(test_path)
    return str(test_path)

async def test_direct_tesseract(image_path: str):
    """Tests Tesseract directly"""
    logger.info("🔍 Testējam Tesseract tieši...")
    
    try:
        # Direct Tesseract bez preprocessing
        text = pytesseract.image_to_string(
            Image.open(image_path), 
            lang='eng+lav',
            config='--psm 6'
        )
        
        logger.info(f"📝 Tesseract rezultāts (bez preprocessing):")
        logger.info(f"'{text.strip()}'")
        
        if text.strip():
            logger.info("✅ Tesseract tieši strādā!")
            return True
        else:
            logger.warning("⚠️ Tesseract neatrada tekstu")
            return False
            
    except Exception as e:
        logger.error(f"❌ Tesseract kļūda: {e}")
        return False

async def test_ocr_service(image_path: str):
    """Tests our OCR service"""
    logger.info("🔍 Testējam mūsu OCR servisu...")
    
    try:
        ocr_service = OCRService()
        await ocr_service.initialize()
        
        result = await ocr_service.extract_text_from_image(image_path)
        
        logger.info(f"📝 OCR Service rezultāts:")
        logger.info(f"Success: {result.get('success', False)}")
        logger.info(f"Text: '{result.get('text', '').strip()}'")
        logger.info(f"Confidence: {result.get('confidence', 0)}")
        
        if result.get('success') and result.get('text', '').strip():
            logger.info("✅ OCR Service strādā!")
            return True
        else:
            logger.warning("⚠️ OCR Service neatrada tekstu")
            return False
            
    except Exception as e:
        logger.error(f"❌ OCR Service kļūda: {e}")
        return False

async def main():
    """Galvenā testa funkcija"""
    logger.info("=== VIENKĀRŠS OCR TESTS ===")
    
    # 1. Izveido test attēlu
    logger.info("🎨 Veidojam test attēlu...")
    test_image = create_simple_test_image()
    logger.info(f"✅ Test attēls izveidots: {test_image}")
    
    # 2. Testē Tesseract tieši
    await test_direct_tesseract(test_image)
    
    print()  # Atstarpe
    
    # 3. Testē mūsu OCR servisu
    await test_ocr_service(test_image)
    
    # 4. Iztīrīšana
    try:
        Path(test_image).unlink()
        logger.info("🧹 Test attēls iztīrīts")
    except:
        pass
    
    logger.info("=== TESTS PABEIGTS ===")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
