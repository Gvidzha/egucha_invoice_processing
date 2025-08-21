"""
Testē regex patternu ekstraktēšanu ar īstiem OCR rezultātiem
"""

import asyncio
import logging
from app.services.extraction_service import ExtractionService
from app.services.ocr.ocr_main import OCRService

# Konfigurē logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_extraction_with_real_images():
    """Testē ekstraktēšanu ar īstiem attēliem"""
    
    # Initiālize services
    ocr_service = OCRService()
    await ocr_service.initialize()  # Svarīgi inicializēt OCR!
    extraction_service = ExtractionService()
    
    # Test attēli
    test_images = [
        "c:\\Code\\regex_invoice_processing\\uploads\\liepajas_petertirgus.jpg",
        "c:\\Code\\regex_invoice_processing\\uploads\\tim_t.jpg", 
        "c:\\Code\\regex_invoice_processing\\uploads\\enra.jpg"
    ]
    
    for image_path in test_images:
        try:
            print(f"\n{'='*60}")
            print(f"Testējam: {image_path.split('\\\\')[-1]}")
            print('='*60)
            
            # Iegūstam OCR tekstu
            ocr_result = await ocr_service.extract_text_adaptive(image_path)
            
            if not ocr_result or not ocr_result.get('success') or not ocr_result.get('cleaned_text'):
                print("❌ Nevarēja iegūt OCR tekstu")
                continue
                
            text = ocr_result['cleaned_text']
            confidence = ocr_result.get('confidence_score', 0.0)
            strategy = ocr_result.get('strategy_used', 'unknown')
            
            print(f"📝 OCR Confidence: {confidence:.1f}%")
            print(f"📝 OCR Stratēģija: {strategy}")
            print(f"📝 OCR Teksta garums: {len(text)} simboli")
            
            # Testē regex ekstraktēšanu
            extracted_data = await extraction_service.extract_invoice_data(text)
            
            # Parādām rezultātus
            print(f"\n🔍 EKSTRAKTĒTIE DATI:")
            print(f"📄 Pavadzīmes Nr: {extracted_data.document_number}")
            print(f"🏢 Piegādātājs: {extracted_data.supplier_name}")
            print(f"📅 Pavadzīmes datums: {extracted_data.invoice_date}")
            print(f"📅 Piegādes datums: {extracted_data.delivery_date}")
            print(f"💰 Kopējā summa: {extracted_data.total_amount} {extracted_data.currency}")
            print(f"💰 PVN summa: {extracted_data.vat_amount} {extracted_data.currency}")
            print(f"🔢 Reģ. numurs: {extracted_data.reg_number}")
            print(f"📍 Adrese: {extracted_data.address}")
            print(f"🏦 Bankas konts: {getattr(extracted_data, 'bank_account', 'Nav')}")
            print(f"📦 Produktu skaits: {len(extracted_data.products)}")
            
            if extracted_data.products:
                print(f"\n📦 PRODUKTI:")
                for i, product in enumerate(extracted_data.products[:3], 1):  # Tikai pirmie 3
                    print(f"  {i}. {product['name'][:40]}{'...' if len(product['name']) > 40 else ''}")
                    print(f"     Daudzums: {product['quantity']}, Cena: {product['unit_price']}")
                
            print(f"\n📊 Confidence Score: {extracted_data.supplier_confidence:.1f}")
            
            # Parādām raw OCR tekstu analīzei
            print(f"\n📄 OCR TEKSTS (pirmie 500 simboli):")
            print("-" * 50)
            print(text[:500])
            if len(text) > 500:
                print("... (saīsināts)")
                
        except Exception as e:
            logger.error(f"Kļūda testējot {image_path}: {e}")
            print(f"❌ Kļūda: {e}")

async def test_specific_patterns():
    """Testē specifiskus regex patternus"""
    
    extraction_service = ExtractionService()
    
    # Test teksti
    test_texts = {
        "document_number": [
            "Pavadzīme Nr. 12345",
            "Invoice No: INV-2024-001", 
            "Dokuments Nr.PV-789",
            "PV 456/2024"
        ],
        "supplier": [
            "SIA \"PETERS TIRGUS\"",
            "SIA PRODUKTI PLUS",
            "AS \"Latvijas Gāze\"",
            "Z/S ENRA"
        ],
        "total": [
            "Kopā: 25.50 EUR",
            "Total: 150,75",
            "Summa kopā 89.99€",
            "KOPĀ 45,30"
        ]
    }
    
    print(f"\n{'='*50}")
    print("REGEX PATTERN TESTĒŠANA")
    print('='*50)
    
    for category, texts in test_texts.items():
        print(f"\n🔍 Testējam: {category.upper()}")
        print("-" * 30)
        
        for text in texts:
            print(f"📄 Teksts: '{text}'")
            
            if category == "document_number":
                result = await extraction_service._extract_document_number(text)
                print(f"✅ Rezultāts: {result}")
            elif category == "supplier":
                result = await extraction_service._extract_supplier(text)
                print(f"✅ Rezultāts: {result}")
            elif category == "total":
                result = await extraction_service._extract_total_amount(text)
                print(f"✅ Rezultāts: {result}")
            
            print()

if __name__ == "__main__":
    asyncio.run(test_extraction_with_real_images())
    asyncio.run(test_specific_patterns())
