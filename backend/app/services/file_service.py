"""
Failu apstrādes utilīti serviss
Atbild par failu saglabāšanu, validāciju un metadatu iegūšanu
"""

import os
import shutil
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from PIL import Image
import uuid

from app.config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)

class FileService:
    """Failu apstrādes serviss"""
    
    def __init__(self):
        """Inicializē failu servisu"""
        self.upload_dir = Path(UPLOAD_DIR)
        self.max_file_size = MAX_FILE_SIZE
        self.allowed_extensions = ALLOWED_EXTENSIONS
        
        # Izveidot upload direktoriju ja neeksistē
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def validate_file(self, file_content: bytes, filename: str) -> Dict[str, any]:
        """
        Publiskā faila validācijas metode
        
        Args:
            file_content: Faila saturs
            filename: Faila nosaukums
            
        Returns:
            dict: Validācijas rezultāts
        """
        return await self._validate_file(file_content, filename)
    
    async def save_uploaded_file(self, 
                               file_content: bytes, 
                               original_filename: str) -> Dict[str, any]:
        """
        Saglabā augšupielādēto failu un atgriež metadatus
        
        Args:
            file_content: Faila saturs
            original_filename: Oriģinālais faila nosaukums
            
        Returns:
            dict: Faila informācija un saglabāšanas ceļš
        """
        try:
            # Validēt failu
            validation_result = await self._validate_file(file_content, original_filename)
            if not validation_result["valid"]:
                return {"error": validation_result["error"]}
            
            # Ģenerēt unikālu faila nosaukumu
            unique_filename = await self._generate_unique_filename(original_filename)
            file_path = self.upload_dir / unique_filename
            
            # Saglabāt failu
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # Iegūt faila metadatus
            metadata = await self._get_file_metadata(file_path, original_filename)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "unique_filename": unique_filename,
                "original_filename": original_filename,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"File save failed: {e}")
            return {"error": f"Failed to save file: {str(e)}"}
    
    async def _validate_file(self, 
                           file_content: bytes, 
                           filename: str) -> Dict[str, any]:
        """
        Validē failu (izmērs, formāts, saturs)
        
        Args:
            file_content: Faila saturs
            filename: Faila nosaukums
            
        Returns:
            dict: Validācijas rezultāts
        """
        # Pārbaudīt faila izmēru
        if len(file_content) > self.max_file_size:
            return {
                "valid": False, 
                "error": f"File too large. Max size: {self.max_file_size} bytes"
            }
        
        # Pārbaudīt faila paplašinājumu
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            return {
                "valid": False,
                "error": f"Invalid file type. Allowed: {self.allowed_extensions}"
            }
        
        # TODO: Pārbaudīt faila saturu (magic bytes)
        # TODO: Pārbaudīt, vai attēls nav bojāts
        # TODO: Antivirus skenēšana (ja nepieciešams)
        
        return {"valid": True}
    
    async def _generate_unique_filename(self, original_filename: str) -> str:
        """
        Ģenerē unikālu faila nosaukumu
        
        Args:
            original_filename: Oriģinālais nosaukums
            
        Returns:
            str: Unikālais faila nosaukums
        """
        # Iegūt paplašinājumu
        file_ext = Path(original_filename).suffix.lower()
        
        # Ģenerēt UUID + timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        return f"{timestamp}_{unique_id}{file_ext}"
    
    async def _get_file_metadata(self, 
                               file_path: Path, 
                               original_filename: str) -> Dict[str, any]:
        """
        Iegūst faila metadatus
        
        Args:
            file_path: Ceļš uz saglabāto failu
            original_filename: Oriģinālais nosaukums
            
        Returns:
            dict: Faila metadati
        """
        try:
            stat = file_path.stat()
            
            metadata = {
                "file_size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "mime_type": mimetypes.guess_type(str(file_path))[0],
                "file_hash": await self._calculate_file_hash(file_path)
            }
            
            # Ja ir attēls, iegūt attēla specifiskos metadatus
            if metadata["mime_type"] and metadata["mime_type"].startswith("image/"):
                image_metadata = await self._get_image_metadata(file_path)
                metadata.update(image_metadata)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get metadata for {file_path}: {e}")
            return {}
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Aprēķina faila SHA-256 hash"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    async def _get_image_metadata(self, file_path: Path) -> Dict[str, any]:
        """
        Iegūst attēla specifiskos metadatus
        
        Args:
            file_path: Ceļš uz attēlu
            
        Returns:
            dict: Attēla metadati
        """
        try:
            with Image.open(file_path) as img:
                return {
                    "image_width": img.width,
                    "image_height": img.height,
                    "image_mode": img.mode,
                    "image_format": img.format,
                    "has_transparency": img.mode in ("RGBA", "LA") or "transparency" in img.info
                }
        except Exception as e:
            logger.error(f"Failed to get image metadata: {e}")
            return {}
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Dzēš failu no diska
        
        Args:
            file_path: Ceļš uz failu
            
        Returns:
            bool: Vai dzēšana bija veiksmīga
        """
        try:
            path = Path(file_path)
            if path.is_file():
                path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    async def cleanup_old_files(self, days_old: int = 30) -> Dict[str, int]:
        """
        Iztīra vecus failus
        
        Args:
            days_old: Vecuma slieksnis dienās
            
        Returns:
            dict: Iztīrīšanas statistika
        """
        # TODO: Implementēt veco failu tīrīšanu
        # - Meklēt failus vecākus par norādīto periodu
        # - Pārbaudīt, vai faili nav vēl lietošanā
        # - Dzēst failus un atjaunināt datubāzi
        
        return {
            "files_deleted": 0,
            "space_freed_mb": 0,
            "errors": 0
        }
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, any]]:
        """
        Iegūst faila informāciju
        
        Args:
            file_path: Ceļš uz failu
            
        Returns:
            dict: Faila informācija vai None
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None
                
            stat = path.stat()
            return {
                "exists": True,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "is_readable": os.access(path, os.R_OK)
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return None
