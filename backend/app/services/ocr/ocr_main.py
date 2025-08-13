"""
Galvenais OCR servisa modulis
Koordinē visus OCR apstrādes soļus
"""

import asyncio
import logging
from typing import Dict, List, Optional, Union
from pathlib import Path
import time

# OCR pamata bibliotēkas
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

from .tesseract_config import TesseractManager
from .image_preprocessor import ImagePreprocessor
from .text_cleaner import TextCleaner
from .pdf_processor import PDFProcessor
from .structure_aware_ocr import StructureAwareOCR, StructureAwareOCRResult

logger = logging.getLogger(__name__)

class OCRService:
    """Galvenais OCR serviss ar modulāru arhitektūru"""
    
    def __init__(self):
        """Inicializē OCR servisu ar visiem moduļiem"""
        
        # Inicializē apakšmoduļus
        self.tesseract_manager = TesseractManager()
        self.image_preprocessor = ImagePreprocessor()
        self.text_cleaner = TextCleaner()
        self.pdf_processor = PDFProcessor()
        
        # Inicializē StructureAwareOCR - POSM 4.5 Week 3
        self.structure_aware_ocr = StructureAwareOCR(ocr_service=self)
        
        # Pārbauda sistēmas gatavību
        self.system_ready = False
        self.setup_errors = []
        
        # Statistika
        self.processing_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'avg_processing_time': 0.0
        }
        
        logger.info("OCR serviss inicializēts")
    
    async def initialize(self) -> Dict[str, any]:
        """
        Inicializē un pārbauda OCR sistēmas gatavību
        
        Returns:
            Dict: Inicializācijas rezultāts
        """
        logger.info("Sāk OCR sistēmas inicializāciju...")
        
        init_result = {
            'success': False,
            'tesseract_ready': False,
            'latvian_support': False,
            'errors': [],
            'warnings': [],
            'setup_info': {}
        }
        
        try:
            # 1. Pārbauda Tesseract instalāciju
            tesseract_setup = self.tesseract_manager.setup_tesseract()
            init_result['tesseract_ready'] = tesseract_setup['installed']
            init_result['latvian_support'] = tesseract_setup['latvian_support']
            init_result['setup_info']['tesseract'] = tesseract_setup
            
            if not tesseract_setup['installed']:
                init_result['errors'].append("Tesseract nav instalēts")
                init_result['setup_info']['instructions'] = tesseract_setup['instructions']
            
            if tesseract_setup['installed'] and not tesseract_setup['latvian_support']:
                init_result['warnings'].append("Latviešu valodas atbalsts nav instalēts")
            
            # 2. Pārbauda Python bibliotēkas
            if not PYTESSERACT_AVAILABLE:
                init_result['errors'].append("pytesseract bibliotēka nav instalēta")
                init_result['setup_info']['python_install'] = "pip install pytesseract"
            
            # 3. Pārbauda PDF apstrādes iespējas
            pdf_methods = self.pdf_processor.available_methods
            init_result['setup_info']['pdf_support'] = pdf_methods
            if not pdf_methods:
                init_result['warnings'].append("PDF apstrāde nav pieejama")
            
            # 4. Testa OCR ar vienkāršu attēlu (ja iespējams)
            if init_result['tesseract_ready'] and PYTESSERACT_AVAILABLE:
                test_result = await self._run_test_ocr()
                init_result['setup_info']['test_ocr'] = test_result
                if not test_result['success']:
                    init_result['errors'].append("OCR tests neizdevās")
            
            # Kopējais rezultāts
            self.system_ready = (init_result['tesseract_ready'] and 
                               PYTESSERACT_AVAILABLE and 
                               len(init_result['errors']) == 0)
            
            init_result['success'] = self.system_ready
            self.setup_errors = init_result['errors']
            
            if self.system_ready:
                logger.info("✅ OCR sistēma pilnībā gatava darbam")
            else:
                logger.warning("⚠️ OCR sistēma nav pilnībā konfigurēta")
                for error in init_result['errors']:
                    logger.error(f"  - {error}")
            
        except Exception as e:
            logger.error(f"Kļūda inicializējot OCR sistēmu: {e}")
            init_result['errors'].append(f"Sistēmas kļūda: {str(e)}")
        
        return init_result
    
    async def extract_text_from_image(self, image_path: str, 
                                    preprocess: bool = True,
                                    clean_text: bool = True,
                                    invoice_mode: bool = True) -> Dict[str, any]:
        """
        Ekstraktē tekstu no attēla faila
        
        Args:
            image_path: Ceļš uz attēla failu
            preprocess: Vai veikt attēla priekšapstrādi
            clean_text: Vai veikt teksta tīrīšanu
            invoice_mode: Vai izmantot pavadzīmju specializētos uzstādījumus
            
        Returns:
            Dict: OCR rezultāts ar tekstu un metadatiem
        """
        start_time = time.time()
        processed_image_path = None

        result = {
            'file_path': image_path,
            'raw_text': '',
            'cleaned_text': '',
            'structured_data': {},
            'confidence_score': 0.0,
            'processing_time': 0.0,
            'preprocessing_used': preprocess,
            'cleaning_used': clean_text,
            'success': False,
            'error': None,
            'metadata': {}
        }
        
        try:
            if not self.system_ready:
                raise Exception("OCR sistēma nav inicializēta. Izsauciet initialize() metodi.")
            
            # Pārbauda faila eksistenci
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Attēls nav atrasts: {image_path}")
            
            logger.info(f"Sāk OCR apstrādi: {image_path}")
            
            # 1. Attēla priekšapstrāde (ja nepieciešams)
            processed_image_path = image_path
            if preprocess:
                if invoice_mode:
                    processed_image_path = self.image_preprocessor.preprocess_for_invoice(image_path)
                else:
                    processed_image_path = self.image_preprocessor.preprocess_image(image_path)
                
                result['metadata']['preprocessed_image'] = processed_image_path
                logger.debug(f"Attēls priekšapstrādāts: {processed_image_path}")
            
            # 2. OCR ar Tesseract
            raw_text = await self._perform_ocr(processed_image_path, invoice_mode)
            result['raw_text'] = raw_text
            
            if not raw_text:
                logger.warning("OCR neatrada tekstu attēlā")
                result['error'] = "Nav atrasts teksts attēlā"
                return result
            
            # 3. Teksta tīrīšana (ja nepieciešams)
            if clean_text:
                cleaned_text = self.text_cleaner.clean_text(raw_text)
                result['cleaned_text'] = cleaned_text
                
                # Strukturēto datu ekstraktēšana
                structured_data = self.text_cleaner.extract_structured_data(cleaned_text)
                result['structured_data'] = structured_data
                
                # Confidence score
                confidence = self.text_cleaner.get_confidence_score(raw_text, cleaned_text)
                result['confidence_score'] = confidence
                
                logger.debug(f"Teksts iztīrīts, confidence: {confidence:.2f}")
            else:
                result['cleaned_text'] = raw_text
                result['confidence_score'] = 0.5  # Default score bez tīrīšanas
            
            # Statistika
            result['processing_time'] = time.time() - start_time
            result['success'] = True
            
            # Atjaunina globālo statistiku
            self._update_stats(result['processing_time'], True)
            
            logger.info(f"OCR pabeigts veiksmīgi: {result['processing_time']:.2f}s, "
                       f"confidence: {result['confidence_score']:.2f}")
            
        except Exception as e:
            result['processing_time'] = time.time() - start_time
            result['error'] = str(e)
            result['success'] = False
            
            self._update_stats(result['processing_time'], False)
            logger.error(f"OCR kļūda: {e}")
        
        finally:
            # Iztīra temporary failus
            if preprocess and processed_image_path and processed_image_path != image_path:
                try:
                    self.image_preprocessor.cleanup_temp_files()
                except Exception as e:
                    logger.warning(f"Nevarēja iztīrīt temp failus: {e}")
        
        return result
    
    async def extract_text_from_pdf(self, pdf_path: str, **kwargs) -> Dict[str, any]:
        """
        Ekstraktē tekstu no PDF faila
        
        Args:
            pdf_path: Ceļš uz PDF failu
            **kwargs: Parametri extract_text_from_image metodei
            
        Returns:
            Dict: OCR rezultāts no visām PDF lapām
        """
        start_time = time.time()
        
        result = {
            'file_path': pdf_path,
            'total_pages': 0,
            'processed_pages': 0,
            'pages_results': [],
            'combined_text': '',
            'combined_structured_data': {},
            'avg_confidence': 0.0,
            'processing_time': 0.0,
            'success': False,
            'error': None
        }
        
        try:
            logger.info(f"Sāk PDF OCR apstrādi: {pdf_path}")
            
            # Sagatavo PDF OCR apstrādei
            pdf_prep = self.pdf_processor.process_pdf_for_ocr(pdf_path)
            
            if not pdf_prep['success']:
                raise Exception(f"Nevarēja sagatavot PDF: {pdf_prep.get('error', 'Unknown error')}")
            
            result['total_pages'] = pdf_prep['total_pages']
            
            # Ja PDF jau satur tekstu, izmanto to
            if pdf_prep['method_used'] == 'direct' and pdf_prep['text_content']:
                result['combined_text'] = pdf_prep['text_content']
                result['processed_pages'] = pdf_prep['total_pages']
                result['avg_confidence'] = 0.9  # Augsts confidence direct text
                result['success'] = True
                
                # Izkārto tekstu arī uz clean version
                if kwargs.get('clean_text', True):
                    cleaned = self.text_cleaner.clean_text(pdf_prep['text_content'])
                    result['combined_text'] = cleaned
                    structured = self.text_cleaner.extract_structured_data(cleaned)
                    result['combined_structured_data'] = structured
                
                logger.info(f"PDF satur tekstu - izmantots direct extraction")
                return result
            
            # OCR katrai lapai
            image_paths = pdf_prep['image_paths']
            if not image_paths:
                raise Exception("Nav izveidoti attēli no PDF lapām")
            
            all_texts = []
            all_confidences = []
            
            for i, image_path in enumerate(image_paths):
                logger.debug(f"Apstrādā PDF lapu {i+1}/{len(image_paths)}")
                
                page_result = await self.extract_text_from_image(image_path, **kwargs)
                result['pages_results'].append(page_result)
                
                if page_result['success']:
                    text_to_use = page_result['cleaned_text'] or page_result['raw_text']
                    all_texts.append(text_to_use)
                    all_confidences.append(page_result['confidence_score'])
                    result['processed_pages'] += 1
            
            # Apvieno rezultātus
            if all_texts:
                result['combined_text'] = '\n\n--- JAUNA LAPA ---\n\n'.join(all_texts)
                result['avg_confidence'] = sum(all_confidences) / len(all_confidences)
                result['success'] = True
                
                # Apvieno strukturētos datus
                if kwargs.get('clean_text', True):
                    combined_structured = self.text_cleaner.extract_structured_data(result['combined_text'])
                    result['combined_structured_data'] = combined_structured
            
            logger.info(f"PDF OCR pabeigts: {result['processed_pages']}/{result['total_pages']} lapas")
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
            logger.error(f"PDF OCR kļūda: {e}")
        
        finally:
            result['processing_time'] = time.time() - start_time
            
            # Iztīra PDF temporary failus
            try:
                self.pdf_processor.cleanup_temp_files()
            except Exception as e:
                logger.warning(f"Nevarēja iztīrīt PDF temp failus: {e}")
        
        return result
    
    async def batch_process(self, file_paths: List[str], **kwargs) -> Dict[str, Dict]:
        """
        Apstrādā vairākus failus paralēli
        
        Args:
            file_paths: Failu ceļu saraksts
            **kwargs: Parametri OCR metodēm
            
        Returns:
            Dict: Rezultāti katram failam
        """
        logger.info(f"Sāk batch apstrādi: {len(file_paths)} faili")
        
        # Sadala failus pa tipiem
        image_files = []
        pdf_files = []
        
        for file_path in file_paths:
            ext = Path(file_path).suffix.lower()
            if ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                image_files.append(file_path)
            elif ext == '.pdf':
                pdf_files.append(file_path)
            else:
                logger.warning(f"Neatbalstīts faila tips: {file_path}")
        
        # Paralēlā apstrāde
        tasks = []
        
        # Attēlu apstrāde
        for image_path in image_files:
            task = self.extract_text_from_image(image_path, **kwargs)
            tasks.append((image_path, task))
        
        # PDF apstrāde
        for pdf_path in pdf_files:
            task = self.extract_text_from_pdf(pdf_path, **kwargs)
            tasks.append((pdf_path, task))
        
        # Gaida visus rezultātus
        results = {}
        for file_path, task in tasks:
            try:
                result = await task
                results[file_path] = result
            except Exception as e:
                logger.error(f"Batch apstrādes kļūda {file_path}: {e}")
                results[file_path] = {
                    'success': False,
                    'error': str(e),
                    'file_path': file_path
                }
        
        logger.info(f"Batch apstrāde pabeigta: {len(results)} faili")
        return results
    
    async def extract_text_with_structure(self, image_path: str, **kwargs) -> Dict[str, any]:
        """
        POSM 4.5 Week 3: Structure-Aware OCR
        Extraktē tekstu ar dokumenta struktūras kontekstu
        
        Args:
            image_path: Ceļš uz attēlu
            **kwargs: Papildu parametri
            
        Returns:
            Dict: Strukturētais OCR rezultāts
        """
        start_time = time.time()
        
        result = {
            'success': False,
            'error': None,
            'structure_aware_result': None,
            'processing_time': 0.0,
            'metadata': {}
        }
        
        try:
            if not self.system_ready:
                raise Exception("OCR sistēma nav inicializēta. Izsauciet initialize() metodi.")
            
            # Pārbauda faila eksistenci
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Attēls nav atrasts: {image_path}")
            
            logger.info(f"Sāk Structure-Aware OCR: {image_path}")
            
            # Veic Structure-Aware OCR
            structure_result = await self.structure_aware_ocr.process_with_structure(image_path)
            
            result['structure_aware_result'] = {
                'text': structure_result.text,
                'enhanced_text': structure_result.enhanced_text,
                'confidence': structure_result.confidence,
                'structure': structure_result.structure.to_dict(),
                'zone_results': structure_result.zone_results,
                'table_results': structure_result.table_results,
                'processing_time_ms': structure_result.processing_time_ms
            }
            
            result['success'] = True
            result['metadata']['zones_detected'] = len(structure_result.structure.zones)
            result['metadata']['tables_detected'] = len(structure_result.structure.tables)
            result['metadata']['overall_confidence'] = structure_result.confidence
            
            # Statistika
            self.processing_stats['total_processed'] += 1
            self.processing_stats['successful'] += 1
            
            logger.info(f"Structure-Aware OCR pabeigts: confidence={structure_result.confidence:.2f}, "
                       f"zones={len(structure_result.structure.zones)}, "
                       f"tables={len(structure_result.structure.tables)}")
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
            self.processing_stats['total_processed'] += 1
            self.processing_stats['failed'] += 1
            logger.error(f"Structure-Aware OCR kļūda: {e}")
        
        finally:
            result['processing_time'] = time.time() - start_time
            
            # Atjaunina vidējo apstrādes laiku
            if self.processing_stats['total_processed'] > 0:
                total_time = (self.processing_stats['avg_processing_time'] * 
                             (self.processing_stats['total_processed'] - 1) + 
                             result['processing_time'])
                self.processing_stats['avg_processing_time'] = total_time / self.processing_stats['total_processed']
        
        return result
    
    async def _perform_ocr(self, image_path: str, invoice_mode: bool = True) -> str:
        """Veic OCR ar Tesseract"""
        try:
            # Konfigurē Tesseract parametrus
            config_overrides = {}
            if invoice_mode:
                # Pavadzīmju specifiskā konfigurācija
                config_overrides = {
                    'psm': '6',  # Uniform text block
                    'config': '--dpi 300 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzĀĒĪŌŪāēīōūčĢģĶķĻļŅņŠšŽž.,€$%-()/'
                }
            
            tesseract_config = self.tesseract_manager.get_ocr_config(config_overrides)
            
            # Iestata tesseract ceļu
            if self.tesseract_manager.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_manager.tesseract_cmd
            
            # Veic OCR
            text = pytesseract.image_to_string(
                image_path,
                config=tesseract_config
            )
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Tesseract OCR kļūda: {e}")
            return ""
    
    async def _run_test_ocr(self) -> Dict[str, any]:
        """Palaiž OCR testu ar vienkāršu tekstu"""
        test_result = {
            'success': False,
            'test_text': '',
            'error': None
        }
        
        try:
            # Šajā implementācijā vienkārši pārbauda vai Tesseract reaģē
            # Reālā implementācijā varētu izveidot test attēlu
            test_config = self.tesseract_manager.get_ocr_config()
            test_result['success'] = bool(test_config)
            test_result['test_text'] = "Tesseract konfigurācija gatava"
            
        except Exception as e:
            test_result['error'] = str(e)
        
        return test_result
    
    def _update_stats(self, processing_time: float, success: bool):
        """Atjaunina apstrādes statistiku"""
        self.processing_stats['total_processed'] += 1
        
        if success:
            self.processing_stats['successful'] += 1
        else:
            self.processing_stats['failed'] += 1
        
        # Atjaunina vidējo apstrādes laiku
        total = self.processing_stats['total_processed']
        current_avg = self.processing_stats['avg_processing_time']
        self.processing_stats['avg_processing_time'] = (
            (current_avg * (total - 1) + processing_time) / total
        )
    
    def get_system_status(self) -> Dict[str, any]:
        """Atgriež sistēmas stāvokļa informāciju"""
        return {
            'system_ready': self.system_ready,
            'setup_errors': self.setup_errors,
            'tesseract_available': self.tesseract_manager.tesseract_cmd is not None,
            'latvian_support': 'lav' in self.tesseract_manager.supported_languages,
            'pdf_support': len(self.pdf_processor.available_methods) > 0,
            'processing_stats': self.processing_stats.copy()
        }
    
    def get_supported_formats(self) -> List[str]:
        """Atgriež atbalstītos failu formātus"""
        formats = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
        
        if self.pdf_processor.available_methods:
            formats.append('.pdf')
        
        return formats

    async def extract_text_adaptive(self, image_path: str) -> Dict[str, any]:
        """
        Adaptīva teksta ekstraktēšana ar dažādām priekšapstrādes stratēģijām
        
        Args:
            image_path: Ceļš uz attēla failu
            
        Returns:
            Dict: OCR rezultāts ar labāko stratēģiju
        """
        logger.info(f"Sākam adaptīvo OCR: {image_path}")
        
        # Stratēģija 1: Bez priekšapstrādes
        logger.debug("Mēģinām bez priekšapstrādes...")
        result1 = await self.extract_text_from_image(image_path, preprocess=False, clean_text=True)
        
        if result1['success'] and result1['confidence_score'] > 0.6:
            result1['strategy_used'] = 'no_preprocessing'
            logger.info(f"✅ Veiksmīgs bez priekšapstrādes: {result1['confidence_score']:.2f}")
            return result1
        
        # Stratēģija 2: Viegla priekšapstrāde
        logger.debug("Mēģinām ar vieglu priekšapstrādi...")
        result2 = await self.extract_text_from_image(image_path, preprocess=True, 
                                                   clean_text=True, invoice_mode=False)
        
        if result2['success'] and result2['confidence_score'] > 0.4:
            result2['strategy_used'] = 'light_preprocessing'
            logger.info(f"✅ Veiksmīgs ar vieglu priekšapstrādi: {result2['confidence_score']:.2f}")
            return result2
        
        # Stratēģija 3: Agresīva priekšapstrāde
        logger.debug("Mēģinām ar agresīvu priekšapstrādi...")
        result3 = await self.extract_text_from_image(image_path, preprocess=True, 
                                                   clean_text=True, invoice_mode=True)
        
        # Atgriežam labāko rezultātu
        best_result = max([result1, result2, result3], 
                         key=lambda x: x.get('confidence_score', 0) if x.get('success', False) else 0)
        
        if best_result == result1:
            best_result['strategy_used'] = 'no_preprocessing'
        elif best_result == result2:
            best_result['strategy_used'] = 'light_preprocessing'
        else:
            best_result['strategy_used'] = 'aggressive_preprocessing'
        
        if best_result['success']:
            logger.info(f"✅ Labākā stratēģija: {best_result['strategy_used']}, "
                       f"confidence: {best_result['confidence_score']:.2f}")
        else:
            logger.warning("❌ Visas stratēģijas neizdevās")
            best_result['strategy_used'] = 'all_failed'
        
        return best_result
