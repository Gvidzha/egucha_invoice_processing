"""
Attēlu priekšapstrādes modulis
Uzlabo attēlu kvalitāti OCR procesam
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import logging
from typing import Tuple, Optional, Union
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """Attēlu priekšapstrādes klase OCR kvalitātes uzlabošanai"""
    
    def __init__(self):
        self.temp_dir = Path("temp/preprocessed")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    def preprocess_image(self, image_path: str, save_steps: bool = False) -> str:
        """
        Galvenā priekšapstrādes funkcija
        
        Args:
            image_path: Ceļš uz oriģinālo attēlu
            save_steps: Vai saglabāt katru apstrādes soli (debug)
            
        Returns:
            str: Ceļš uz priekšapstrādāto attēlu
        """
        try:
            # Ielādēt attēlu
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Nevarēja ielādēt attēlu: {image_path}")
            
            original_name = Path(image_path).stem
            step_counter = 0
            
            if save_steps:
                self._save_step(image, original_name, step_counter, "original")
                step_counter += 1
            
            # 1. Izmēra normalizācija (ja pārāk mazs vai liels)
            image = self._normalize_size(image)
            if save_steps:
                self._save_step(image, original_name, step_counter, "resized")
                step_counter += 1
            
            # 2. Rotācijas korekcija
            image = self._correct_rotation(image)
            if save_steps:
                self._save_step(image, original_name, step_counter, "rotated")
                step_counter += 1
            
            # 3. Trokšņa samazināšana
            image = self._denoise(image)
            if save_steps:
                self._save_step(image, original_name, step_counter, "denoised")
                step_counter += 1
            
            # 4. Kontrasta uzlabošana
            image = self._enhance_contrast(image)
            if save_steps:
                self._save_step(image, original_name, step_counter, "contrast")
                step_counter += 1
            
            # 5. Binarizācija (melnbalts)
            image = self._binarize(image)
            if save_steps:
                self._save_step(image, original_name, step_counter, "binary")
                step_counter += 1
            
            # 6. Morfologiskās operācijas
            image = self._morphological_operations(image)
            if save_steps:
                self._save_step(image, original_name, step_counter, "morphology")
            
            # Saglabāt finālo rezultātu
            output_path = self.temp_dir / f"{original_name}_processed.png"
            cv2.imwrite(str(output_path), image)
            
            logger.info(f"Attēls priekšapstrādāts: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Kļūda priekšapstrādējot attēlu {image_path}: {e}")
            return image_path  # Atgriež oriģinālo, ja kļūda
    
    def _normalize_size(self, image: np.ndarray, target_dpi: int = 300) -> np.ndarray:
        """
        Normalizē attēla izmēru optimālam OCR
        
        Args:
            image: OpenCV attēls
            target_dpi: Mērķa DPI vērtība
            
        Returns:
            np.ndarray: Izmēra normalizēts attēls
        """
        height, width = image.shape[:2]
        
        # Minimālais izmērs OCR kvalitātei
        min_height = 600
        min_width = 800
        
        # Ja attēls pārāk mazs, palielinām
        if height < min_height or width < min_width:
            scale_factor = max(min_height / height, min_width / width)
            new_height = int(height * scale_factor)
            new_width = int(width * scale_factor)
            
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            logger.debug(f"Attēls palielināts: {width}x{height} -> {new_width}x{new_height}")
        
        # Ja attēls pārāk liels (>4000px), samazinām
        elif height > 4000 or width > 4000:
            scale_factor = min(4000 / height, 4000 / width)
            new_height = int(height * scale_factor)
            new_width = int(width * scale_factor)
            
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            logger.debug(f"Attēls samazināts: {width}x{height} -> {new_width}x{new_height}")
        
        return image
    
    def _correct_rotation(self, image: np.ndarray) -> np.ndarray:
        """
        Koriģē attēla rotāciju, izmantojot teksta līniju analīzi
        
        Args:
            image: OpenCV attēls
            
        Returns:
            np.ndarray: Rotācijas koriģēts attēls
        """
        try:
            # Konvertē uz pelēktoņu
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Atrod malas
            edges = cv2.Canny(gray, 100, 200, apertureSize=3)
            
            # Hough līniju detekcija
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                angles = []
                for rho, theta in lines[:20]:  # Analizē tikai pirmo 20 līniju
                    angle = theta * 180 / np.pi
                    # Normalizē leņķi
                    if angle > 90:
                        angle = angle - 180
                    angles.append(angle)
                
                # Aprēķina vidējo rotācijas leņķi
                if angles:
                    rotation_angle = np.median(angles)
                    
                    # Rotē attēlu tikai ja leņķis > 0.5 grādi
                    if abs(rotation_angle) > 0.5:
                        center = (image.shape[1]//2, image.shape[0]//2)
                        rotation_matrix = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
                        image = cv2.warpAffine(image, rotation_matrix, (image.shape[1], image.shape[0]), 
                                             flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                        logger.debug(f"Attēls pagriezts par {rotation_angle:.2f} grādiem")
        
        except Exception as e:
            logger.warning(f"Nevarēja koriģēt rotāciju: {e}")
        
        return image
    
    def _denoise(self, image: np.ndarray) -> np.ndarray:
        """
        Samazina troksni attēlā
        
        Args:
            image: OpenCV attēls
            
        Returns:
            np.ndarray: Trokšņa samazināts attēls
        """
        # Non-local means denoising
        if len(image.shape) == 3:  # Krāsains attēls
            denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        else:  # Pelēktoņu attēls
            denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
        
        return denoised
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Uzlabo attēla kontrastu
        
        Args:
            image: OpenCV attēls
            
        Returns:
            np.ndarray: Kontrasta uzlabots attēls
        """
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        if len(image.shape) == 3:
            # Krāsainiem attēliem - konvertē uz LAB krāsu telpu
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            lab[:,:,0] = clahe.apply(lab[:,:,0])
            image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            # Pelēktoņu attēliem
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            image = clahe.apply(image)
        
        return image
    
    def _binarize(self, image: np.ndarray) -> np.ndarray:
        """
        Pārveido attēlu uz melnbaltu (binarizācija)
        
        Args:
            image: OpenCV attēls
            
        Returns:
            np.ndarray: Binarizēts attēls
        """
        # Konvertē uz pelēktoņu, ja vajag
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Adaptive threshold - labāk strādā ar dažādu apgaismojumu
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return binary
    
    def _morphological_operations(self, image: np.ndarray) -> np.ndarray:
        """
        Morfologiskās operācijas teksta uzlabošanai
        
        Args:
            image: Binarizēts OpenCV attēls
            
        Returns:
            np.ndarray: Morfologiski uzlabots attēls
        """
        # Izveidojam kernel teksta tīrīšanai
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        
        # Opening - noņem mazos trokšņa punktus
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Closing - aiztaisa mazās starpes burtros
        kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel2, iterations=1)
        
        return image
    
    def _save_step(self, image: np.ndarray, name: str, step: int, description: str):
        """Saglabā apstrādes soli debug vajadzībām"""
        debug_dir = self.temp_dir / "debug"
        debug_dir.mkdir(exist_ok=True)
        
        filename = f"{name}_{step:02d}_{description}.png"
        cv2.imwrite(str(debug_dir / filename), image)
    
    def preprocess_for_invoice(self, image_path: str) -> str:
        """
        Specializēta priekšapstrāde pavadzīmēm
        
        Args:
            image_path: Ceļš uz pavadzīmes attēlu
            
        Returns:
            str: Ceļš uz priekšapstrādāto attēlu
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Nevarēja ielādēt attēlu: {image_path}")
            
            # Specializēti uzstādījumi pavadzīmēm
            original_name = Path(image_path).stem
            
            # 1. Agresīvāka kontrasta uzlabošana (pavadzīmes bieži ir vājā kvalitātē)
            if len(image.shape) == 3:
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
                lab[:,:,0] = clahe.apply(lab[:,:,0])
                image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            # 2. Gamma korekcija 
            gamma = 1.2
            image = np.power(image / 255.0, gamma) * 255.0
            image = image.astype(np.uint8)
            
            # 3. Uzlabota binarizācija pavadzīmēm
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Otsu threshold kombinācijā ar Gaussian adaptive
            _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                           cv2.THRESH_BINARY, 15, 2)
            
            # Kombinē abas metodes
            binary = cv2.bitwise_and(otsu, adaptive)
            
            # 4. Specializēta morfologija pavadzīmju tekstam
            kernel_line = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            kernel_text = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            
            # Uzlabo horizontālās līnijas (tabulas)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_line, iterations=1)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_text, iterations=1)
            
            # Saglabāt rezultātu
            output_path = self.temp_dir / f"{original_name}_invoice_processed.png"
            cv2.imwrite(str(output_path), binary)
            
            logger.info(f"Pavadzīme priekšapstrādāta: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Kļūda priekšapstrādējot pavadzīmi {image_path}: {e}")
            return image_path
    
    def cleanup_temp_files(self, keep_recent: int = 10):
        """
        Iztīra vecākos temporary failus
        
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
                    
                logger.info(f"Iztīrīti {len(temp_files) - keep_recent} temporary faili")
        except Exception as e:
            logger.warning(f"Nevarēja iztīrīt temporary failus: {e}")
