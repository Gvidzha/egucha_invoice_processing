"""
OCR tests ar reālu failu
Ļauj testēt OCR ar jūsu izvēlētu failu
"""

import asyncio
import sys
from pathlib import Path

# Pieliek backend direktoriju sys.path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.ocr import OCRService

async def test_with_real_file():
    """Testē OCR ar reālu failu"""
    print("📁 OCR Real File Test")
    print("====================")
    
    # Meklē testēšanai piemērotus failus
    potential_files = []
    
    # Meklē uploads direktorijā
    uploads_dir = Path("uploads")
    if uploads_dir.exists():
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.pdf']:
            potential_files.extend(uploads_dir.glob(ext))
    
    # Meklē data direktorijā
    data_dir = Path("../data")
    if data_dir.exists():
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.pdf']:
            potential_files.extend(data_dir.glob(ext))
    
    # Meklē pašreizējā direktorijā
    current_dir = Path(".")
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.pdf']:
        potential_files.extend(current_dir.glob(ext))
    
    print(f"🔍 Atrasti {len(potential_files)} faili testēšanai:")
    for i, file_path in enumerate(potential_files[:10], 1):
        print(f"   {i}. {file_path}")
    
    if not potential_files:
        print("❌ Nav atrasti faili testēšanai!")
        print("\nIeteikums:")
        print("1. Ievietojiet test attēlu vai PDF uploads/ direktorijā")
        print("2. Vai norādiet faila ceļu manuāli:")
        
        manual_path = input("\nIevadiet faila ceļu (vai Enter, lai iziet): ").strip()
        if manual_path and Path(manual_path).exists():
            potential_files = [Path(manual_path)]
        else:
            return
    
    # Izvēlas failu
    if len(potential_files) == 1:
        selected_file = potential_files[0]
        print(f"\n📋 Izmantojam: {selected_file}")
    else:
        try:
            choice = input(f"\nIzvēlieties failu (1-{min(len(potential_files), 10)}) vai Enter priekš 1: ").strip()
            index = int(choice) - 1 if choice else 0
            selected_file = potential_files[index]
        except (ValueError, IndexError):
            selected_file = potential_files[0]
            print(f"📋 Izmantojam pirmo: {selected_file}")
    
    try:
        # Inicializējam OCR
        print("\n🔧 Inicializējam OCR...")
        ocr_service = OCRService()
        await ocr_service.initialize()
        
        # Apstrādājam failu
        print(f"🔍 Apstrādājam: {selected_file.name}")
        
        if selected_file.suffix.lower() == '.pdf':
            result = await ocr_service.extract_text_from_pdf(str(selected_file))
        else:
            result = await ocr_service.extract_text_from_image(str(selected_file))
        
        # Rezultāti
        if result['success']:
            print("✅ OCR apstrāde veiksmīga!")
            
            text = result['text']
            print(f"\n📊 Statistika:")
            print(f"   📏 Teksta garums: {len(text)} rakstzīmes")
            print(f"   📄 Rindu skaits: {text.count(chr(10)) + 1}")
            print(f"   🔤 Vārdu skaits: {len(text.split())}")
            
            # Parāda tekstu
            print(f"\n📖 Ekstraktētais teksts:")
            print("=" * 50)
            print(text)
            print("=" * 50)
            
            # Analizē saturu
            print(f"\n🔍 Satura analīze:")
            keywords = ['pavadzīme', 'invoice', 'rēķins', 'datums', 'summa', 'pvn', 'eur']
            found = [kw for kw in keywords if kw.lower() in text.lower()]
            if found:
                print(f"   📝 Atrasti atslēgvārdi: {', '.join(found)}")
            
            # Meklē skaitļus
            import re
            numbers = re.findall(r'\d+[.,]\d+', text)
            if numbers:
                print(f"   💰 Atrasti skaitļi: {', '.join(numbers[:5])}")
            
            # Meklē datumus
            dates = re.findall(r'\d{4}[-./]\d{1,2}[-./]\d{1,2}', text)
            if dates:
                print(f"   📅 Atrasti datumi: {', '.join(dates)}")
        
        else:
            print(f"❌ OCR kļūda: {result.get('error', 'Nezināma kļūda')}")
    
    except Exception as e:
        print(f"❌ Testēšanas kļūda: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_with_real_file())
