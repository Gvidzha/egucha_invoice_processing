"""
Vienkāršs OCR quick test
Pārbauda vai OCR sistēma darbojas
"""

import asyncio
import sys
from pathlib import Path

# Pieliek backend direktoriju sys.path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.ocr import OCRService

async def quick_ocr_test():
    """Ātrs OCR tests"""
    print("🔧 OCR Quick Test")
    print("================")
    
    try:
        # Inicializējam OCR
        print("1️⃣ Inicializējam OCR servisu...")
        ocr_service = OCRService()
        await ocr_service.initialize()
        print("✅ OCR serviss gatavs!")
        
        # Pārbaudam konfigurāciju
        print("\n2️⃣ Pārbaudam konfigurāciju...")
        
        # Tesseract pārbaude
        tesseract_ok = ocr_service.tesseract_manager.check_installation()
        print(f"   Tesseract: {'✅' if tesseract_ok else '❌'}")
        
        # Latvian support
        latvian_ok = ocr_service.tesseract_manager.check_latvian_support()
        print(f"   Latviešu valoda: {'✅' if latvian_ok else '❌'}")
        
        # Available languages
        languages = ocr_service.tesseract_manager.get_available_languages()
        print(f"   Pieejamās valodas: {', '.join(languages[:5])}...")
        
        # PDF support
        pdf_methods = ocr_service.pdf_processor.available_methods
        print(f"   PDF atbalsts: {', '.join(pdf_methods) if pdf_methods else 'Nav'}")
        
        print("\n🎉 OCR sistēma ir gatava darbam!")
        print("\nNākamais solis:")
        print("   python test_ocr_workflow.py  # Pilnais workflow tests")
        
    except Exception as e:
        print(f"❌ Kļūda: {e}")
        print("\nIeteikums:")
        print("1. Pārbaudiet vai Tesseract ir instalēts")
        print("2. Pārbaudiet vai Python packages ir instalēti")
        print("3. Aktivizējiet virtual environment")

if __name__ == "__main__":
    asyncio.run(quick_ocr_test())
