#!/usr/bin/env python3
"""
Adaptīvās OCR stratēģijas tests
"""

import sys
import asyncio
import logging
from pathlib import Path

# Pievienojam app moduli path
sys.path.insert(0, '.')

from app.services.ocr.ocr_main import OCRService

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_adaptive_ocr():
    """Testē adaptīvo OCR ar reālām pavadzīmēm"""
    
    print("🚀 === ADAPTĪVĀS OCR TESTĒŠANA ===")
    
    # Inicializējam OCR servisu
    ocr = OCRService()
    await ocr.initialize()
    
    # Test faili (absolūtie ceļi)
    test_files = [
        "C:/Code/regex_invoice_processing/uploads/liepajas_petertirgus.jpg",
        "C:/Code/regex_invoice_processing/uploads/tim_t.jpg", 
        "C:/Code/regex_invoice_processing/uploads/enra.jpg"
    ]
    
    # Pārbaudām kuri faili eksistē
    existing_files = []
    for file_path in test_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
            logger.info(f"✅ {Path(file_path).name}")
        else:
            logger.warning(f"❌ Nav atrasts: {file_path}")
    
    if not existing_files:
        logger.error("Nav atrasts neviens test fails!")
        return
    
    print(f"\n📁 Testējam {len(existing_files)} failus ar adaptīvo OCR:\n")
    
    # Testējam katru failu
    for i, file_path in enumerate(existing_files, 1):
        print(f"[{i}/{len(existing_files)}] {Path(file_path).name}")
        print("=" * 60)
        
        try:
            # Adaptīvs OCR
            result = await ocr.extract_text_adaptive(file_path)
            
            print(f"📊 Stratēģija: {result.get('strategy_used', 'unknown')}")
            print(f"✅ Veiksmīgs: {result['success']}")
            
            if result['success']:
                print(f"📈 Confidence: {result['confidence_score']:.1%}")
                print(f"⏱️ Laiks: {result['processing_time']:.2f}s")
                print(f"📏 Teksta garums: {len(result['cleaned_text'])} simboli")
                
                # Parādām pirmo līniju
                lines = result['cleaned_text'].strip().split('\n')
                if lines and lines[0].strip():
                    print(f"📝 Pirmā līnija: '{lines[0][:50]}{'...' if len(lines[0]) > 50 else ''}'")
                
                # Saglabājam rezultātu
                output_file = f"test_results/adaptive_{Path(file_path).stem}.txt"
                Path("test_results").mkdir(exist_ok=True)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"Fails: {file_path}\n")
                    f.write(f"Stratēģija: {result['strategy_used']}\n")
                    f.write(f"Confidence: {result['confidence_score']:.2%}\n")
                    f.write(f"Laiks: {result['processing_time']:.2f}s\n")
                    f.write("-" * 50 + "\n")
                    f.write(result['cleaned_text'])
                
                print(f"💾 Saglabāts: {output_file}")
            else:
                print(f"❌ Kļūda: {result.get('error', 'Nav zināma')}")
                
        except Exception as e:
            logger.error(f"Kļūda testējot {file_path}: {e}")
        
        print()
    
    print("🎉 === ADAPTĪVĀ TESTĒŠANA PABEIGTA ===")

if __name__ == "__main__":
    asyncio.run(test_adaptive_ocr())
