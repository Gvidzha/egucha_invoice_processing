"""
OCR sistēmas setup un testa skripts
Pārbauda un konfigurē OCR komponentes
"""

import asyncio
import logging
import sys
from pathlib import Path

# Pievieno projekta ceļu
sys.path.append(str(Path(__file__).parent.parent))

from app.services.ocr import OCRService, TesseractManager

# Konfigurē logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def setup_ocr_system():
    """Galvenā setup funkcija"""
    
    print("=" * 60)
    print("OCR SISTĒMAS SETUP UN TESTS")
    print("=" * 60)
    
    # 1. Pārbauda Tesseract instalāciju
    print("\n1. TESSERACT PĀRBAUDE")
    print("-" * 30)
    
    tesseract_manager = TesseractManager()
    setup_result = tesseract_manager.setup_tesseract()
    
    print(f"Instalēts: {'✅' if setup_result['installed'] else '❌'}")
    print(f"Latviešu atbalsts: {'✅' if setup_result['latvian_support'] else '❌'}")
    
    if setup_result['installed']:
        print(f"Tesseract ceļš: {setup_result['tesseract_path']}")
        print(f"Pieejamās valodas: {', '.join(setup_result['available_languages'])}")
    else:
        print("\n📋 INSTALĀCIJAS INSTRUKCIJAS:")
        instructions = setup_result['instructions']
        for method, command in instructions.items():
            print(f"  {method}: {command}")
        return False
    
    # 2. OCR servisa inicializācija
    print("\n2. OCR SERVISA INICIALIZĀCIJA")
    print("-" * 30)
    
    ocr_service = OCRService()
    init_result = await ocr_service.initialize()
    
    print(f"Sistēma gatava: {'✅' if init_result['success'] else '❌'}")
    
    if init_result['errors']:
        print("❌ Kļūdas:")
        for error in init_result['errors']:
            print(f"  - {error}")
    
    if init_result['warnings']:
        print("⚠️ Brīdinājumi:")
        for warning in init_result['warnings']:
            print(f"  - {warning}")
    
    # 3. Sistēmas statuss
    print("\n3. SISTĒMAS STATUSS")
    print("-" * 30)
    
    status = ocr_service.get_system_status()
    print(f"OCR gatavs: {'✅' if status['system_ready'] else '❌'}")
    print(f"PDF atbalsts: {'✅' if status['pdf_support'] else '❌'}")
    print(f"Atbalstītie formāti: {', '.join(ocr_service.get_supported_formats())}")
    
    # 4. Testa OCR (ja ir test attēls)
    print("\n4. OCR TESTS")
    print("-" * 30)
    
    test_image_path = Path(__file__).parent / "test_images" / "test_invoice.jpg"
    
    if test_image_path.exists():
        print(f"Testē ar: {test_image_path}")
        
        try:
            result = await ocr_service.extract_text_from_image(str(test_image_path))
            
            if result['success']:
                print("✅ OCR tests veiksmīgs!")
                print(f"Confidence: {result['confidence_score']:.2f}")
                print(f"Apstrādes laiks: {result['processing_time']:.2f}s")
                
                if result['cleaned_text']:
                    preview = result['cleaned_text'][:200]
                    print(f"Teksta priekšskatījums: {preview}...")
                
                if result['structured_data']:
                    structured = result['structured_data']
                    print(f"Atrasti datumi: {len(structured.get('dates', []))}")
                    print(f"Atrastas summas: {len(structured.get('amounts', []))}")
            else:
                print(f"❌ OCR tests neizdevās: {result['error']}")
                
        except Exception as e:
            print(f"❌ Testa kļūda: {e}")
    else:
        print("⚠️ Nav atrasts test attēls")
        print(f"Izveidojiet: {test_image_path}")
    
    # 5. Nākamie soļi
    print("\n5. NĀKAMIE SOĻI")
    print("-" * 30)
    
    if init_result['success']:
        print("✅ OCR sistēma ir gatava!")
        print("📝 Nākamais:")
        print("  1. Testējiet ar īstām pavadzīmēm")
        print("  2. Konfigurējiet API endpoints")
        print("  3. Integrējiet ar frontend")
    else:
        print("⚠️ Sistēma nav pilnībā gatava")
        print("🔧 Nepieciešams:")
        for error in init_result['errors']:
            print(f"  - {error}")
    
    print("\n" + "=" * 60)
    
    return init_result['success']

def create_test_structure():
    """Izveido test direktoriju struktūru"""
    test_dir = Path(__file__).parent / "test_images"
    test_dir.mkdir(exist_ok=True)
    
    readme_content = """# OCR Test attēli

Ievietojiet šeit pavadzīmju attēlus testēšanai:

- test_invoice.jpg - Pamata tests
- sample_pavadzime.png - Pavadzīmes paraugs
- complex_invoice.pdf - PDF tests

Atbalstītie formāti: JPG, PNG, TIFF, BMP, PDF
"""
    
    readme_path = test_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text(readme_content, encoding='utf-8')
        print(f"Izveidots test direktorijs: {test_dir}")

if __name__ == "__main__":
    try:
        create_test_structure()
        success = asyncio.run(setup_ocr_system())
        
        if success:
            print("\n🎉 Setup pabeigts veiksmīgi!")
            sys.exit(0)
        else:
            print("\n💥 Setup nav pabeigts - nepieciešama konfigurācija")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Setup pārtraukts")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Setup kļūda: {e}")
        sys.exit(1)
