#!/usr/bin/env python3
"""
Reālu pavadzīmju OCR testēšana
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Pievienojam app moduli
sys.path.insert(0, '.')

from app.services.ocr import OCRService
from app.services.ocr.image_preprocessor import ImagePreprocessor

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealInvoiceOCRTester:
    """Reālu pavadzīmju OCR testētājs"""
    
    def __init__(self):
        self.ocr_service = OCRService()
        self.preprocessor = ImagePreprocessor()
        
        # Reālie pavadzīmju faili
        self.test_files = [
            "C:/Code/regex_invoice_processing/uploads/liepajas_petertirgus.jpg",
            "C:/Code/regex_invoice_processing/uploads/tim_t.jpg", 
            "C:/Code/regex_invoice_processing/uploads/enra.jpg"
        ]
    
    async def initialize(self):
        """Inicializē OCR servisu"""
        logger.info("🔧 Inicializējam OCR servisu...")
        await self.ocr_service.initialize()
        logger.info("✅ OCR serviss gatavs!")
    
    async def test_single_invoice(self, file_path: str, enable_debug: bool = True):
        """
        Testē vienu pavadzīmi ar detalizētu izvadi
        
        Args:
            file_path: Ceļš uz pavadzīmes attēlu
            enable_debug: Vai saglabāt priekšapstrādes soļus
        """
        if not Path(file_path).exists():
            logger.error(f"❌ Fails neeksistē: {file_path}")
            return
        
        invoice_name = Path(file_path).stem
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 TESTĒJAM: {invoice_name}")
        logger.info(f"📁 Fails: {file_path}")
        logger.info(f"{'='*60}")
        
        try:
            # 1. Pārbaudām faila informāciju
            file_size = Path(file_path).stat().st_size / 1024  # KB
            logger.info(f"📊 Faila izmērs: {file_size:.1f} KB")
            
            # 2. Priekšapstrāde ar debug
            if enable_debug:
                logger.info("🖼️ Sākam attēla priekšapstrādi (ar debug)...")
                processed_path = self.preprocessor.preprocess_for_invoice(file_path)
                
                # Pārbaudām debug failus
                debug_dir = Path("temp/preprocessed/debug")
                if debug_dir.exists():
                    debug_files = list(debug_dir.glob(f"{invoice_name}*"))
                    logger.info(f"🔧 Debug faili izveidoti: {len(debug_files)}")
                    for debug_file in sorted(debug_files):
                        logger.info(f"   📄 {debug_file.name}")
            else:
                logger.info("🖼️ Sākam attēla priekšapstrādi...")
                processed_path = self.preprocessor.preprocess_for_invoice(file_path)
            
            logger.info(f"✅ Priekšapstrāde pabeigta: {processed_path}")
            
            # 3. OCR apstrāde
            logger.info("📖 Sākam OCR apstrādi...")
            result = await self.ocr_service.extract_text_from_image(file_path)
            
            if result['success']:
                # OCR atgriež 'raw_text' un 'cleaned_text', nevis 'text'
                raw_text = result.get('raw_text', '')
                cleaned_text = result.get('cleaned_text', '')
                confidence = result.get('confidence_score', 0) * 100  # Pārveidojam uz procentiem
                
                # Izmantojam cleaned_text, ja pieejams, citādi raw_text
                extracted_text = cleaned_text if cleaned_text else raw_text
                
                logger.info(f"✅ OCR VEIKSMĪGS!")
                logger.info(f"📊 Ticamība: {confidence:.1f}%")
                logger.info(f"📏 Teksta garums: {len(extracted_text)} simboli")
                logger.info(f"📄 Teksta garums: {len(extracted_text)} simboli")
                logger.info(f"📝 Teksta līnijas: {len(extracted_text.splitlines())} rindas")
                
                # Rādām pirmo daļu no teksta
                preview_lines = extracted_text.splitlines()[:10]
                logger.info("\n📋 TEKSTA PRIEKŠSKATĪJUMS (pirmas 10 rindas):")
                logger.info("-" * 50)
                for i, line in enumerate(preview_lines, 1):
                    if line.strip():
                        logger.info(f"{i:2d}: {line[:80]}{'...' if len(line) > 80 else ''}")
                
                # Saglabājam pilno tekstu
                output_dir = Path("test_results")
                output_dir.mkdir(exist_ok=True)
                
                text_file = output_dir / f"{invoice_name}_extracted.txt"
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(f"Pavadzīme: {invoice_name}\n")
                    f.write(f"Oriģinālais fails: {file_path}\n")
                    f.write(f"OCR ticamība: {confidence:.1f}%\n")
                    f.write(f"Teksta garums: {len(extracted_text)} simboli\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(extracted_text)
                
                logger.info(f"💾 Teksts saglabāts: {text_file}")
                
            else:
                error = result.get('error', 'Nezināma kļūda')
                logger.error(f"❌ OCR NEIZDEVĀS: {error}")
                
        except Exception as e:
            logger.error(f"❌ Kļūda testējot {invoice_name}: {e}")
    
    async def test_all_invoices(self):
        """Testē visas pavadzīmes"""
        logger.info(f"\n🚀 === SĀKAM REĀLU PAVADZĪMJU TESTĒŠANU ===")
        logger.info(f"📁 Testējam {len(self.test_files)} pavadzīmes:")
        
        for file_path in self.test_files:
            if Path(file_path).exists():
                logger.info(f"   ✅ {Path(file_path).name}")
            else:
                logger.warning(f"   ❌ {Path(file_path).name} - nav atrasts")
        
        # Testējam katru failu
        for i, file_path in enumerate(self.test_files, 1):
            if Path(file_path).exists():
                logger.info(f"\n[{i}/{len(self.test_files)}] Testējam: {Path(file_path).name}")
                await self.test_single_invoice(file_path, enable_debug=(i == 1))  # Debug tikai pirmajai
            else:
                logger.warning(f"\n[{i}/{len(self.test_files)}] Izlaižam: {Path(file_path).name} (nav atrasts)")
        
        logger.info(f"\n🎉 === TESTĒŠANA PABEIGTA ===")
        logger.info(f"📊 Rezultāti saglabāti: test_results/")
        logger.info(f"🔧 Debug attēli: temp/preprocessed/debug/")
    
    async def quick_test(self, file_path: str):
        """Ātra vienas pavadzīmes testēšana"""
        if not Path(file_path).exists():
            logger.error(f"❌ Fails neeksistē: {file_path}")
            return
        
        logger.info(f"⚡ ĀTRĀ TESTĒŠANA: {Path(file_path).name}")
        await self.test_single_invoice(file_path, enable_debug=False)

async def main():
    """Galvenā funkcija"""
    tester = RealInvoiceOCRTester()
    
    try:
        # Inicializējam OCR
        await tester.initialize()
        
        # Izvēlamies test veidu
        if len(sys.argv) > 1:
            # Ātra testēšana ar konkrētu failu
            test_file = sys.argv[1]
            await tester.quick_test(test_file)
        else:
            # Testējam visus failus
            await tester.test_all_invoices()
            
    except KeyboardInterrupt:
        logger.info("❌ Testēšana pārtraukta")
    except Exception as e:
        logger.error(f"❌ Kļūda: {e}")

if __name__ == "__main__":
    print("Reālu Pavadzīmju OCR Testētājs")
    print("=" * 40)
    
    # Palaižam async main
    asyncio.run(main())
