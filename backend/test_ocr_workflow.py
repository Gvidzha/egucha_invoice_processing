"""
OCR sistēmas pilnā workflow testēšana
Testē: failu ielādi, OCR apstrādi, rezultātu saglabāšanu
"""

import asyncio
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Pieliek backend direktoriju sys.path, lai varētu importēt
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.ocr import OCRService
from app.services.file_service import FileService
from app.config import get_settings
import logging

# Logging konfigurācija
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OCRWorkflowTester:
    """OCR workflow testēšanas klase"""
    
    def __init__(self):
        self.settings = get_settings()
        self.ocr_service = None
        self.file_service = FileService()
        self.test_files_dir = Path("test_images")
        self.temp_test_files = []
    
    async def initialize(self):
        """Inicializē OCR servisu"""
        try:
            logger.info("🔧 Inicializējam OCR servisu...")
            self.ocr_service = OCRService()
            await self.ocr_service.initialize()
            logger.info("✅ OCR serviss inicializēts")
            return True
        except Exception as e:
            logger.error(f"❌ OCR inicializācijas kļūda: {e}")
            return False
    
    def create_test_directory(self):
        """Izveido test direktoriju"""
        self.test_files_dir.mkdir(exist_ok=True)
        logger.info(f"📁 Test direktorija: {self.test_files_dir.absolute()}")
    
    def create_sample_test_image(self) -> str:
        """Izveido parauga test attēlu ar tekstu"""
        try:
            import cv2
            import numpy as np
            
            # Izveido baltu attēlu
            img = np.ones((800, 600, 3), dtype=np.uint8) * 255
            
            # Pievieno tekstu (simulē rēķinu)
            font = cv2.FONT_HERSHEY_SIMPLEX
            
            # Virsraksts
            cv2.putText(img, 'PAVADZIME / INVOICE', (50, 80), font, 1.2, (0, 0, 0), 2)
            cv2.putText(img, 'SIA "TestCompany"', (50, 130), font, 0.8, (0, 0, 0), 2)
            
            # Datums
            cv2.putText(img, 'Datums: 2024-01-15', (50, 180), font, 0.7, (0, 0, 0), 2)
            cv2.putText(img, 'Nr: INV-2024-001', (300, 180), font, 0.7, (0, 0, 0), 2)
            
            # Piegādātājs
            cv2.putText(img, 'PIEGADATAJS:', (50, 230), font, 0.6, (0, 0, 0), 2)
            cv2.putText(img, 'SIA "Suppliers Ltd"', (50, 260), font, 0.6, (0, 0, 0), 1)
            cv2.putText(img, 'Reg.Nr: 40003123456', (50, 285), font, 0.6, (0, 0, 0), 1)
            
            # Produkti
            cv2.putText(img, 'PRODUKTI:', (50, 335), font, 0.6, (0, 0, 0), 2)
            cv2.putText(img, '1. Dators HP Laptop   Skaits: 2   Cena: 500.00 EUR', (50, 365), font, 0.5, (0, 0, 0), 1)
            cv2.putText(img, '2. Pele Logitech      Skaits: 3   Cena: 25.00 EUR', (50, 390), font, 0.5, (0, 0, 0), 1)
            
            # Kopsumma
            cv2.putText(img, 'KOPSUMMA: 1075.00 EUR', (50, 450), font, 0.8, (0, 0, 0), 2)
            cv2.putText(img, 'PVN (21%): 225.75 EUR', (50, 480), font, 0.6, (0, 0, 0), 1)
            cv2.putText(img, 'MAKSĀT: 1300.75 EUR', (50, 520), font, 0.8, (0, 0, 0), 2)
            
            # Saglabā
            test_image_path = self.test_files_dir / "test_invoice.png"
            cv2.imwrite(str(test_image_path), img)
            self.temp_test_files.append(test_image_path)
            
            logger.info(f"✅ Izveidots test attēls: {test_image_path}")
            return str(test_image_path)
            
        except ImportError:
            logger.warning("⚠️ OpenCV nav pieejams - nevarēja izveidot test attēlu")
            return None
        except Exception as e:
            logger.error(f"❌ Kļūda veidojot test attēlu: {e}")
            return None
    
    def create_sample_pdf(self) -> str:
        """Izveido parauga PDF failu"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            
            pdf_path = self.test_files_dir / "test_invoice.pdf"
            c = canvas.Canvas(str(pdf_path), pagesize=A4)
            
            # Pievieno tekstu PDF
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, 750, "PAVADZĪME / INVOICE")
            
            c.setFont("Helvetica", 12)
            c.drawString(50, 720, 'SIA "TestCompany"')
            c.drawString(50, 700, "Datums: 2024-01-15")
            c.drawString(300, 700, "Nr: INV-2024-001")
            
            c.drawString(50, 660, "PIEGĀDĀTĀJS:")
            c.setFont("Helvetica", 10)
            c.drawString(50, 640, 'SIA "Suppliers Ltd"')
            c.drawString(50, 625, "Reg.Nr: 40003123456")
            
            c.setFont("Helvetica", 12)
            c.drawString(50, 580, "PRODUKTI:")
            c.setFont("Helvetica", 10)
            c.drawString(50, 560, "1. Dators HP Laptop   Skaits: 2   Cena: 500.00 EUR")
            c.drawString(50, 545, "2. Pele Logitech      Skaits: 3   Cena: 25.00 EUR")
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, 500, "KOPSUMMA: 1075.00 EUR")
            c.setFont("Helvetica", 10)
            c.drawString(50, 480, "PVN (21%): 225.75 EUR")
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, 460, "MAKSĀT: 1300.75 EUR")
            
            c.save()
            self.temp_test_files.append(pdf_path)
            
            logger.info(f"✅ Izveidots test PDF: {pdf_path}")
            return str(pdf_path)
            
        except ImportError:
            logger.warning("⚠️ reportlab nav pieejams - nevarēja izveidot test PDF")
            return None
        except Exception as e:
            logger.error(f"❌ Kļūda veidojot test PDF: {e}")
            return None
    
    async def test_file_upload_simulation(self, file_path: str) -> dict:
        """Simulē failu upload procesu"""
        try:
            logger.info(f"📤 Testējam failu upload: {Path(file_path).name}")
            
            # Ielādējam faila saturu (kā tas notiktu reālā upload)
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            filename = Path(file_path).name
            
            # Simulē file upload validation ar pareiziem parametriem
            file_info = await self.file_service.validate_file(file_content, filename)
            if not file_info['valid']:
                logger.error(f"❌ Faila validācija neizdevās: {file_info['error']}")
                return {'success': False, 'error': file_info['error']}
            
            # Simulē faila saglabāšanu uploads direktorijā
            uploads_dir = Path("uploads")
            uploads_dir.mkdir(exist_ok=True)
            
            destination = uploads_dir / Path(file_path).name
            shutil.copy2(file_path, destination)
            
            logger.info(f"✅ Fails saglabāts: {destination}")
            
            return {
                'success': True,
                'upload_path': str(destination),
                'file_info': file_info
            }
            
        except Exception as e:
            logger.error(f"❌ Upload simulācijas kļūda: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_ocr_processing(self, file_path: str) -> dict:
        """Testē OCR apstrādi"""
        try:
            logger.info(f"🔍 Sākam OCR apstrādi: {Path(file_path).name}")
            
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.pdf':
                logger.info("📄 Apstrādājam PDF failu...")
                result = await self.ocr_service.extract_text_from_pdf(file_path)
            else:
                logger.info("🖼️ Apstrādājam attēla failu...")
                result = await self.ocr_service.extract_text_from_image(file_path)
            
            if result['success']:
                logger.info("✅ OCR apstrāde veiksmīga!")
                logger.info(f"📝 Atrastas {len(result['text'])} rakstzīmes")
                
                # Parāda teksta fragmentu
                text_preview = result['text'][:200] + "..." if len(result['text']) > 200 else result['text']
                logger.info(f"📖 Teksta priekšskatījums:\n{text_preview}")
                
            else:
                logger.error(f"❌ OCR apstrāde neizdevās: {result.get('error', 'Nezināma kļūda')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ OCR testēšanas kļūda: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_batch_processing(self, file_paths: list) -> dict:
        """Testē batch OCR apstrādi"""
        try:
            logger.info(f"📦 Testējam batch apstrādi: {len(file_paths)} faili")
            
            results = await self.ocr_service.batch_process(file_paths)
            
            successful = sum(1 for r in results if r['success'])
            logger.info(f"✅ Batch rezultāts: {successful}/{len(results)} veiksmīgi")
            
            return {
                'success': True,
                'total_files': len(file_paths),
                'successful': successful,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Batch testēšanas kļūda: {e}")
            return {'success': False, 'error': str(e)}
    
    def analyze_results(self, ocr_result: dict):
        """Analizē OCR rezultātus"""
        if not ocr_result['success']:
            return
        
        text = ocr_result['text']
        logger.info("\n📊 === OCR REZULTĀTU ANALĪZE ===")
        
        # Pamata statistika
        logger.info(f"📏 Teksta garums: {len(text)} rakstzīmes")
        logger.info(f"📄 Rindu skaits: {text.count(chr(10)) + 1}")
        logger.info(f"🔤 Vārdu skaits: {len(text.split())}")
        
        # Meklē atslēgvārdus
        keywords = [
            'pavadzīme', 'invoice', 'rēķins',
            'datums', 'date', 'nr',
            'piegādātājs', 'supplier',
            'kopsumma', 'summa', 'total',
            'pvn', 'vat', 'eur'
        ]
        
        found_keywords = []
        for keyword in keywords:
            if keyword.lower() in text.lower():
                found_keywords.append(keyword)
        
        logger.info(f"🔍 Atrasti atslēgvārdi: {', '.join(found_keywords)}")
        
        # Meklē skaitļus (iespējamās cenas)
        import re
        numbers = re.findall(r'\d+[.,]\d+', text)
        if numbers:
            logger.info(f"💰 Atrasti skaitļi: {', '.join(numbers[:5])}")
        
        # Meklē datumus
        dates = re.findall(r'\d{4}[-./]\d{1,2}[-./]\d{1,2}', text)
        if dates:
            logger.info(f"📅 Atrasti datumi: {', '.join(dates)}")
    
    def cleanup(self):
        """Iztīra test failus"""
        try:
            for file_path in self.temp_test_files:
                if file_path.exists():
                    file_path.unlink()
            
            # Iztīra test direktoriju, ja tukša
            if self.test_files_dir.exists() and not any(self.test_files_dir.iterdir()):
                self.test_files_dir.rmdir()
            
            logger.info("🧹 Test faili iztīrīti")
        except Exception as e:
            logger.warning(f"⚠️ Nevarēja iztīrīt test failus: {e}")
    
    async def run_full_workflow_test(self):
        """Palaiž pilno workflow testu"""
        logger.info("\n🚀 === SĀKAM OCR WORKFLOW TESTĒŠANU ===\n")
        
        try:
            # 1. Inicializācija
            success = await self.initialize()
            if not success:
                logger.error("❌ Nevarēja inicializēt OCR servisu")
                return
            
            # 2. Izveido test direktoriju
            self.create_test_directory()
            
            # 3. Izveido test failus
            test_files = []
            
            image_path = self.create_sample_test_image()
            if image_path:
                test_files.append(image_path)
            
            pdf_path = self.create_sample_pdf()
            if pdf_path:
                test_files.append(pdf_path)
            
            if not test_files:
                logger.error("❌ Nevarēja izveidot test failus")
                return
            
            # 4. Testē katru failu atsevišķi
            for test_file in test_files:
                logger.info(f"\n--- Testējam failu: {Path(test_file).name} ---")
                
                # Upload simulācija
                upload_result = await self.test_file_upload_simulation(test_file)
                if not upload_result['success']:
                    continue
                
                # OCR apstrāde
                ocr_result = await self.test_ocr_processing(upload_result['upload_path'])
                
                # Rezultātu analīze
                self.analyze_results(ocr_result)
            
            # 5. Batch processing tests
            if len(test_files) > 1:
                logger.info("\n--- Testējam Batch Processing ---")
                uploaded_files = []
                for test_file in test_files:
                    upload_result = await self.test_file_upload_simulation(test_file)
                    if upload_result['success']:
                        uploaded_files.append(upload_result['upload_path'])
                
                if uploaded_files:
                    batch_result = await self.test_batch_processing(uploaded_files)
            
            logger.info("\n🎉 === OCR WORKFLOW TESTĒŠANA PABEIGTA ===")
            
        except Exception as e:
            logger.error(f"❌ Workflow tests kļūda: {e}")
        
        finally:
            # Cleanup
            self.cleanup()

async def main():
    """Galvenā funkcija"""
    tester = OCRWorkflowTester()
    await tester.run_full_workflow_test()

if __name__ == "__main__":
    print("OCR Workflow Tester")
    print("==================")
    asyncio.run(main())
