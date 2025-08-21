"""
PDF failu apstrādes modulis OCR vajadzībām
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path
import tempfile
import os

# PDF apstrādes bibliotēkas
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

import cv2
import numpy as np

logger = logging.getLogger(__name__)

class PDFProcessor:
    """PDF failu apstrādes klase OCR vajadzībām"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "pdf_ocr"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Pārbauda pieejamās PDF bibliotēkas
        self.available_methods = self._check_available_methods()
        logger.info(f"Pieejamās PDF apstrādes metodes: {self.available_methods}")
    
    def _check_available_methods(self) -> List[str]:
        """Pārbauda kādas PDF apstrādes metodes ir pieejamas"""
        methods = []
        
        if PYMUPDF_AVAILABLE:
            methods.append("pymupdf")
        
        if PDF2IMAGE_AVAILABLE:
            methods.append("pdf2image")
        
        if not methods:
            logger.warning("Nav instalētas PDF apstrādes bibliotēkas!")
            logger.info("Instalācijas instrukcijas:")
            logger.info("pip install PyMuPDF pdf2image")
            logger.info("Windows: Nepieciešams instalēt poppler-windows")
            logger.info("Linux: sudo apt-get install poppler-utils")
        
        return methods
    
    def convert_pdf_to_images(self, pdf_path: str, dpi: int = 300) -> List[str]:
        """
        Konvertē PDF lapas uz attēliem
        
        Args:
            pdf_path: Ceļš uz PDF failu
            dpi: Izšķirtspēja konversijai
            
        Returns:
            List[str]: Ceļi uz izveidotajiem attēliem
        """
        if not self.available_methods:
            logger.error("Nav pieejamas PDF apstrādes metodes")
            return []
        
        try:
            # Prioritāte: PyMuPDF (ātrāks) > pdf2image
            if "pymupdf" in self.available_methods:
                return self._convert_with_pymupdf(pdf_path, dpi)
            elif "pdf2image" in self.available_methods:
                return self._convert_with_pdf2image(pdf_path, dpi)
            else:
                logger.error("Nav pieejamas PDF konversijas metodes")
                return []
                
        except Exception as e:
            logger.error(f"Kļūda konvertējot PDF {pdf_path}: {e}")
            return []
    
    def _save_pdf_page_as_image(self, page, output_path, mat):
        pix = page.get_pixmap(matrix=mat)
        pix.save(str(output_path))

    def _get_pymupdf_matrix(self, dpi: int) -> "fitz.Matrix":
        zoom = dpi / 72.0
        return fitz.Matrix(zoom, zoom)

    def _convert_with_pymupdf(self, pdf_path: str, dpi: int = 300) -> List[str]:
        """Konvertē PDF ar PyMuPDF bibliotēku"""
        image_paths = []
        
        try:
            pdf_document = fitz.open(pdf_path)
            pdf_name = Path(pdf_path).stem
            
            mat = self._get_pymupdf_matrix(dpi)

            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                output_path = self.temp_dir / f"{pdf_name}_page_{page_num + 1:03d}.png"
                self._save_pdf_page_as_image(page, output_path, mat)
                image_paths.append(str(output_path))
                
                logger.debug(f"Konvertēta lapa {page_num + 1}/{pdf_document.page_count}")
            
            pdf_document.close()
            logger.info(f"PDF konvertēts: {len(image_paths)} lapas")
            
        except Exception as e:
            logger.error(f"PyMuPDF konversijas kļūda: {e}")
        
        return image_paths
    
    def _convert_with_pdf2image(self, pdf_path: str, dpi: int = 300) -> List[str]:
        """Konvertē PDF ar pdf2image bibliotēku"""
        image_paths = []
        
        try:
            # Konvertē PDF uz PIL Image objektiem
            images = convert_from_path(pdf_path, dpi=dpi)
            pdf_name = Path(pdf_path).stem
            
            for i, image in enumerate(images):
                output_path = self.temp_dir / f"{pdf_name}_page_{i + 1:03d}.png"
                image.save(str(output_path), 'PNG')
                image_paths.append(str(output_path))
                
                logger.debug(f"Konvertēta lapa {i + 1}/{len(images)}")
            
            logger.info(f"PDF konvertēts: {len(image_paths)} lapas")
            
        except Exception as e:
            logger.error(f"pdf2image konversijas kļūda: {e}")
        
        return image_paths
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, any]:
        """
        Ekstraktē tekstu no PDF faila (mēģina vispirms direct text extraction)
        
        Args:
            pdf_path: Ceļš uz PDF failu
            
        Returns:
            Dict: Ekstraktētais teksts
        """
        result = {
            'text': '',
            'pages': [],
            'extraction_method': 'none',
            'needs_ocr': True
        }
        
        try:
            # Mēģina iegūt tekstu tiešā veidā (ja PDF nav skenēts)
            if "pymupdf" in self.available_methods:
                direct_text = self._extract_direct_text_pymupdf(pdf_path)
                if direct_text and len(direct_text.strip()) > 50:  # Ja atrod pietiekami teksta
                    result['text'] = direct_text
                    result['extraction_method'] = 'direct'
                    result['needs_ocr'] = False
                    logger.info("PDF satur tekstu - izmanto direct extraction")
                    return result
            
            # Ja nav teksta vai pārāk maz teksta, vajag OCR
            logger.info("PDF nepieciešams OCR - konvertē uz attēliem")
            result['extraction_method'] = 'ocr_required'
            result['needs_ocr'] = True
            
        except Exception as e:
            logger.error(f"Kļūda analizējot PDF: {e}")
        
        return result
    
    def _extract_direct_text_pymupdf(self, pdf_path: str) -> str:
        """Mēģina iegūt tekstu tiešā veidā no PDF"""
        try:
            pdf_document = fitz.open(pdf_path)
            full_text = ""
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                page_text = page.get_text()
                full_text += page_text + "\n"
            
            pdf_document.close()
            return full_text.strip()
            
        except Exception as e:
            logger.error(f"Direct text extraction kļūda: {e}")
            return ""
    
    def process_pdf_for_ocr(self, pdf_path: str, max_pages: Optional[int] = None) -> Dict[str, any]:
        """
        Sagatavo PDF failu OCR apstrādei
        
        Args:
            pdf_path: Ceļš uz PDF failu
            max_pages: Maksimālais lapu skaits (None = visas lapas)
            
        Returns:
            Dict: Informācija par PDF un konvertētajiem attēliem
        """
        result = {
            'pdf_path': pdf_path,
            'total_pages': 0,
            'processed_pages': 0,
            'image_paths': [],
            'text_content': '',
            'method_used': 'none',
            'success': False
        }
        
        try:
            # Vispirms mēģina direct text extraction
            text_result = self.extract_text_from_pdf(pdf_path)
            result['text_content'] = text_result['text']
            result['method_used'] = text_result['extraction_method']
            
            if not text_result['needs_ocr']:
                result['success'] = True
                return result
            
            # Ja vajag OCR, konvertē uz attēliem
            image_paths = self.convert_pdf_to_images(pdf_path)
            
            if max_pages:
                image_paths = image_paths[:max_pages]
            
            result['image_paths'] = image_paths
            result['total_pages'] = len(image_paths)
            result['processed_pages'] = len(image_paths)
            result['success'] = len(image_paths) > 0
            
            logger.info(f"PDF sagatavots OCR: {len(image_paths)} lapas")
            
        except Exception as e:
            logger.error(f"Kļūda sagatavojot PDF OCR: {e}")
            result['error'] = str(e)
        
        return result
    
    def optimize_pdf_images(self, image_paths: List[str]) -> List[str]:
        """
        Optimizē PDF attēlus OCR kvalitātei
        
        Args:
            image_paths: Attēlu ceļi
            
        Returns:
            List[str]: Optimizēto attēlu ceļi
        """
        optimized_paths = []
        
        for image_path in image_paths:
            try:
                # Ielādē attēlu
                image = cv2.imread(image_path)
                if image is None:
                    logger.warning(f"Nevarēja ielādēt attēlu: {image_path}")
                    continue
                
                # PDF specifiskas optimizācijas
                optimized = self._optimize_pdf_image(image)
                
                # Saglabā optimizēto versiju
                base_name = Path(image_path).stem
                optimized_path = self.temp_dir / f"{base_name}_optimized.png"
                cv2.imwrite(str(optimized_path), optimized)
                optimized_paths.append(str(optimized_path))
                
            except Exception as e:
                logger.error(f"Kļūda optimizējot attēlu {image_path}: {e}")
                # Ja optimizācija neizdevās, izmanto oriģinālo
                optimized_paths.append(image_path)
        
        return optimized_paths
    
    def _optimize_pdf_image(self, image: np.ndarray) -> np.ndarray:
        """PDF attēla optimizācija OCR vajadzībām"""
        
        # 1. Konvertē uz pelēktoņu
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 2. Uzlabo kontrastu (PDF bieži ir vājš kontrasts)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # 3. Samazina PDF specifisko troksni
        denoised = cv2.medianBlur(enhanced, 3)
        
        # 4. Adaptīvā binarizācija
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # 5. Morfoloģiskā tīrīšana
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
        
        return cleaned
    
    def cleanup_temp_files(self, keep_recent: int = 5):
        """
        Iztīra temporary PDF attēlus
        
        Args:
            keep_recent: Cik jaunākos failus paturēt
        """
        try:
            temp_files = list(self.temp_dir.glob("*.png"))
            if len(temp_files) > keep_recent:
                # Sorte pēc modificēšanas datuma
                temp_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # Dzēš vecākos failus
                for file_path in temp_files[keep_recent:]:
                    file_path.unlink()
                logger.info(f"Iztīrīti {len(temp_files) - keep_recent} PDF temporary faili")
        except Exception as e:
            logger.warning(f"Nevarēja iztīrīt PDF temporary failus: {e}")
    
    def get_pdf_info(self, pdf_path: str) -> Dict[str, any]:
        """
        Iegūst PDF faila informāciju
        
        Args:
            pdf_path: Ceļš uz PDF failu
            
        Returns:
            Dict: PDF informācija
        """
        info = {
            'path': pdf_path,
            'exists': False,
            'pages': 0,
            'has_text': False,
            'file_size': 0,
            'title': '',
            'author': '',
            'creator': ''
        }
        
        try:
            pdf_path_obj = Path(pdf_path)
            info['exists'] = pdf_path_obj.exists()
            
            if info['exists']:
                info['file_size'] = pdf_path_obj.stat().st_size
                
                if "pymupdf" in self.available_methods:
                    pdf_doc = fitz.open(pdf_path)
                    info['pages'] = pdf_doc.page_count
                    
                    # Mēģina iegūt metadatus
                    metadata = pdf_doc.metadata
                    info['title'] = metadata.get('title', '')
                    info['author'] = metadata.get('author', '')
                    info['creator'] = metadata.get('creator', '')
                    
                    # Pārbauda vai ir teksts
                    if pdf_doc.page_count > 0:
                        first_page_text = pdf_doc[0].get_text()
                        info['has_text'] = len(first_page_text.strip()) > 10
                    
                    pdf_doc.close()
                    
        except Exception as e:
            logger.error(f"Kļūda iegūstot PDF info: {e}")
            info['error'] = str(e)
        
        return info
    
    def get_installation_instructions(self) -> Dict[str, str]:
        """Atgriež PDF bibliotēku instalācijas instrukcijas"""
        return {
            "PyMuPDF": "pip install PyMuPDF",
            "pdf2image": "pip install pdf2image",
            "Windows_poppler": "Lejupielādēt no: https://github.com/oschwartz10612/poppler-windows/releases/",
            "Ubuntu_poppler": "sudo apt-get install poppler-utils",
            "CentOS_poppler": "sudo yum install poppler-utils",
            "macOS_poppler": "brew install poppler"
        }
