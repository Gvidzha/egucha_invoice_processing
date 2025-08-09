"""
Tesseract konfigurācijas un instalācijas pārvaldība
"""

import os
import subprocess
import platform
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class TesseractManager:
    """Tesseract OCR konfigurācijas pārvaldnieks"""
    
    def __init__(self):
        self.tesseract_cmd = None
        self.supported_languages = []
        self.config = {
            # OCR konfigurācijas parametri
            'psm': '6',  # Page Segmentation Mode (6 = uniform text block)
            'oem': '3',  # OCR Engine Mode (3 = default)
            'lang': 'lav+eng',  # Latviešu + angļu valoda
            'config': '--dpi 300 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzĀĒĪŌŪāēīōūčĢģĶķĻļŅņŠšŽž.,€$%-'
        }
        
    def check_installation(self) -> bool:
        """
        Pārbauda vai Tesseract ir instalēts un pieejams
        
        Returns:
            bool: True ja instalēts un darbojas
        """
        try:
            # Mēģina atrast tesseract executable
            if platform.system() == "Windows":
                possible_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    "tesseract.exe"
                ]
            else:
                possible_paths = [
                    "/usr/bin/tesseract",
                    "/usr/local/bin/tesseract", 
                    "tesseract"
                ]
            
            for path in possible_paths:
                if self._test_tesseract_path(path):
                    self.tesseract_cmd = path
                    logger.info(f"Tesseract atrasts: {path}")
                    return True
                    
            logger.error("Tesseract nav atrasts sistēmā")
            return False
            
        except Exception as e:
            logger.error(f"Kļūda pārbaudot Tesseract: {e}")
            return False
    
    def _test_tesseract_path(self, path: str) -> bool:
        """Testē vai dots ceļš uz tesseract darbojas"""
        try:
            result = subprocess.run(
                [path, '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def get_available_languages(self) -> List[str]:
        """
        Iegūst pieejamo valodu sarakstu
        
        Returns:
            List[str]: Pieejamo valodu kodi
        """
        if not self.tesseract_cmd:
            return []
            
        try:
            result = subprocess.run(
                [self.tesseract_cmd, '--list-langs'], 
                capture_output=True, 
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Pirmā rindiņa ir virsraksts, tālāk valodas
                languages = result.stdout.strip().split('\n')[1:]
                self.supported_languages = languages
                logger.info(f"Pieejamās valodas: {languages}")
                return languages
            else:
                logger.warning("Nevarēja iegūt valodu sarakstu")
                return []
                
        except Exception as e:
            logger.error(f"Kļūda iegūstot valodas: {e}")
            return []
    
    def check_latvian_support(self) -> bool:
        """
        Pārbauda vai latviešu valoda ir pieejama
        
        Returns:
            bool: True ja latviešu valoda ir atbalstīta
        """
        languages = self.get_available_languages()
        has_latvian = 'lav' in languages
        
        if not has_latvian:
            logger.warning("Latviešu valoda nav instalēta Tesseract!")
            logger.info("Instalācijas instrukcijas:")
            if platform.system() == "Windows":
                logger.info("1. Lejupielādēt no: https://github.com/UB-Mannheim/tesseract/wiki")
                logger.info("2. Instalācijas laikā izvēlēties 'Additional language data'")
                logger.info("3. Atzīmēt 'Latvian' valodu")
            else:
                logger.info("Ubuntu/Debian: sudo apt-get install tesseract-ocr-lav")
                logger.info("CentOS/RHEL: sudo yum install tesseract-langpack-lav")
        
        return has_latvian
    
    def get_ocr_config(self, custom_config: Optional[Dict] = None) -> str:
        """
        Sagatavo Tesseract konfigurācijas string
        
        Args:
            custom_config: Papildu konfigurācijas parametri
            
        Returns:
            str: Konfigurācijas string Tesseract
        """
        config = self.config.copy()
        if custom_config:
            config.update(custom_config)
        
        # Salikts konfigurācijas string
        config_string = f"--psm {config['psm']} --oem {config['oem']} -l {config['lang']}"
        
        if 'config' in config and config['config']:
            config_string += f" {config['config']}"
            
        return config_string
    
    def install_instructions(self) -> Dict[str, str]:
        """
        Atgriež instalācijas instrukcijas pašreizējai sistēmai
        
        Returns:
            Dict[str, str]: Instrukcijas dažādām sistēmām
        """
        instructions = {
            "Windows": {
                "method1": "winget install UB-Mannheim.TesseractOCR",
                "method2": "Lejupielādēt no: https://github.com/UB-Mannheim/tesseract/wiki",
                "latvian": "Instalācijas laikā izvēlēties 'Additional language data' un atzīmēt 'Latvian'"
            },
            "Ubuntu/Debian": {
                "tesseract": "sudo apt-get update && sudo apt-get install tesseract-ocr",
                "latvian": "sudo apt-get install tesseract-ocr-lav"
            },
            "CentOS/RHEL": {
                "tesseract": "sudo yum install tesseract",
                "latvian": "sudo yum install tesseract-langpack-lav"
            },
            "macOS": {
                "tesseract": "brew install tesseract",
                "latvian": "brew install tesseract-lang"
            }
        }
        
        current_os = platform.system()
        return instructions.get(current_os, instructions["Ubuntu/Debian"])
    
    def setup_tesseract(self) -> Dict[str, any]:
        """
        Veic pilnu Tesseract setup un konfigurāciju
        
        Returns:
            Dict: Setup rezultāts ar status un info
        """
        setup_result = {
            "installed": False,
            "latvian_support": False,
            "available_languages": [],
            "tesseract_path": None,
            "instructions": self.install_instructions()
        }
        
        # Pārbaudam instalāciju
        if self.check_installation():
            setup_result["installed"] = True
            setup_result["tesseract_path"] = self.tesseract_cmd
            
            # Pārbaudam valodas
            languages = self.get_available_languages()
            setup_result["available_languages"] = languages
            setup_result["latvian_support"] = self.check_latvian_support()
            
            if setup_result["latvian_support"]:
                logger.info("✅ Tesseract ir pilnībā konfigurēts ar latviešu valodas atbalstu")
            else:
                logger.warning("⚠️ Tesseract instalēts, bet nav latviešu valodas atbalsta")
        else:
            logger.error("❌ Tesseract nav instalēts")
            
        return setup_result
