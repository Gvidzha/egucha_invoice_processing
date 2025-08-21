"""
Structure-Aware OCR Service - POSM 4.5 Week 3
Paplašina OCR funkcionalitāti ar dokumenta struktūras kontekstu
"""

from ast import pattern
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging
import asyncio
from datetime import datetime, timezone
import json

from ..document_structure_service import (
    DocumentStructureAnalyzer, DocumentStructure, DocumentZone, 
    TableRegion, TableCell, BoundingBox, ZoneType
)

logger = logging.getLogger(__name__)

@dataclass
class StructureAwareOCRResult:
    """
    OCR rezultāts ar struktūras kontekstu
    """
    text: str
    confidence: float
    structure: DocumentStructure
    zone_results: Dict[str, Any]  # OCR rezultāti pa zonām
    table_results: List[Dict[str, Any]]  # Tabulu OCR rezultāti
    enhanced_text: str  # Teksts ar struktūras kontekstu
    processing_time_ms: int = 0
    created_at: datetime = None
    
    # POSM 4.5 Week 3 enhancements
    overall_confidence: float = 0.0  # Enhanced confidence score
    metadata: Dict[str, Any] = None  # Additional metadata
    full_text: str = ""  # Full extracted text for compatibility
    processing_time: float = 0.0  # Processing time in seconds
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.metadata is None:
            self.metadata = {}
        if not self.full_text:
            self.full_text = self.text
        if not self.overall_confidence:
            self.overall_confidence = self.confidence
        if not self.processing_time:
            self.processing_time = self.processing_time_ms / 1000.0

@dataclass
class ZoneOCRConfig:
    """
    Zone-specific OCR konfigurācija
    """
    zone_type: ZoneType
    tesseract_config: str
    preprocessing_steps: List[str]
    confidence_threshold: float
    text_cleaning_level: str  # 'light', 'medium', 'aggressive'

class StructureAwareOCR:
    """
    Structure-Aware OCR Service
    
    Capabilities:
    - Zone-specific OCR optimization
    - Table-aware text extraction
    - Confidence weighting systems
    - Structure context integration
    """
    
    def __init__(
        self,
        ocr_service,
        structure_analyzer: Optional[DocumentStructureAnalyzer] = None,
        template_reliability_threshold: float = 0.8,
        template_confidence_boost: float = 1.1,
    ):
        """
        Inicializē ar atsauci uz esošo OCR servisu
        
        Args:
            ocr_service: Atsauce uz OCRService instanci
            structure_analyzer: DocumentStructureAnalyzer instance
        """
        self.ocr_service = ocr_service
        self.structure_analyzer = structure_analyzer or DocumentStructureAnalyzer()
        self.logger = logging.getLogger(__name__)
        self.template_reliability_threshold = template_reliability_threshold
        self.template_confidence_boost = template_confidence_boost
        self.ocr_service = ocr_service
        self.structure_analyzer = structure_analyzer or DocumentStructureAnalyzer()
        self.logger = logging.getLogger(__name__)
        
        # Zone-specific configurations
        self.zone_configs = self._initialize_zone_configs()
        
        # Table extraction configurations
        self.table_configs = {
            "cell_padding": 5,  # Padding ap šūnām
            "min_cell_area": 100,  # Minimālais šūnas laukums
            "header_enhancement": True,  # Uzlabo kolonnu virsrakstus
            "data_type_detection": True,  # Nosaka datu tipus
        }
        
        # Confidence weighting
        self.confidence_weights = {
            ZoneType.HEADER: 1.2,     # Header zones get higher weight
            ZoneType.BODY: 1.0,       # Standard weight
            ZoneType.FOOTER: 0.9,     # Footer slightly lower
            ZoneType.SUMMARY: 1.1,    # Summary important
            ZoneType.TABLE: 1.3,      # Tables need high accuracy
        }
        
        self.logger.info("StructureAwareOCR inicializēts")
    
    def _initialize_zone_configs(self) -> Dict[ZoneType, ZoneOCRConfig]:
        """Inicializē zone-specific konfigurācijas"""
        return {
            ZoneType.HEADER: ZoneOCRConfig(
                zone_type=ZoneType.HEADER,
                tesseract_config="--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,:-/ ",
                preprocessing_steps=["deskew", "denoise", "enhance_contrast"],
                confidence_threshold=0.7,
                text_cleaning_level="medium"
            ),
            ZoneType.BODY: ZoneOCRConfig(
                zone_type=ZoneType.BODY,
                tesseract_config="--psm 6",
                preprocessing_steps=["deskew", "denoise"],
                confidence_threshold=0.6,
                text_cleaning_level="medium"
            ),
            ZoneType.FOOTER: ZoneOCRConfig(
                zone_type=ZoneType.FOOTER,
                tesseract_config="--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,:-/ ",
                preprocessing_steps=["denoise", "enhance_contrast"],
                confidence_threshold=0.5,
                text_cleaning_level="light"
            ),
            ZoneType.SUMMARY: ZoneOCRConfig(
                zone_type=ZoneType.SUMMARY,
                tesseract_config="--psm 6 -c tessedit_char_whitelist=0123456789.,€$+-= ",
                preprocessing_steps=["deskew", "denoise", "enhance_contrast"],
                confidence_threshold=0.8,
                text_cleaning_level="aggressive"
            ),
            ZoneType.TABLE: ZoneOCRConfig(
                zone_type=ZoneType.TABLE,
                tesseract_config="--psm 6",
                preprocessing_steps=["deskew", "denoise", "enhance_contrast", "morphology"],
                confidence_threshold=0.75,
                text_cleaning_level="medium"
            ),
        }
    
    async def process_with_structure(self, image_path: str) -> StructureAwareOCRResult:
        """
        Galvenā metode - OCR ar struktūras kontekstu
        
        Args:
            image_path: Ceļš uz attēlu
            
        Returns:
            StructureAwareOCRResult: OCR rezultāts ar struktūras informāciju
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # 1. Analizē dokumenta struktūru
            self.logger.info(f"Analizē struktūru: {image_path}")
            structure = await self.structure_analyzer.analyze_document(image_path)
            
            # 2. Parallēli apstrādā zonas
            zone_tasks = []
            for zone in structure.zones:
                task = self._process_zone_ocr(image_path, zone)
                zone_tasks.append(task)
            
            zone_results = await asyncio.gather(*zone_tasks, return_exceptions=True)
            
            # 3. Apstrādā tabulas
            table_results = []
            for table in structure.tables:
                table_result = await self._process_table_ocr(image_path, table)
                table_results.append(table_result)
            
            # 4. Veic standard OCR kā backup
            standard_ocr_result = await self.ocr_service.extract_text_from_image(image_path)
            
            # 5. Kombinē rezultātus
            zone_dict = {
                zone.zone_type.value: zone_results[i]
                for i, zone in enumerate(structure.zones)
                if i < len(zone_results) and not isinstance(zone_results[i], Exception)
            }
            
            # 6. Izveido enhanced text ar struktūras kontekstu
            enhanced_text = self._create_enhanced_text(
                standard_ocr_result.get('text', ''),
                zone_dict,
                table_results,
                structure
            )
            
            # 7. Aprēķina weighted confidence
            weighted_confidence = self._calculate_weighted_confidence(
                standard_ocr_result.get('confidence', 0.0),
                zone_dict,
                table_results
            )
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = StructureAwareOCRResult(
                text=standard_ocr_result.get('text', ''),
                confidence=weighted_confidence,
                structure=structure,
                zone_results=zone_dict,
                table_results=table_results,
                enhanced_text=enhanced_text,
                processing_time_ms=processing_time
            )
            
            self.logger.info(f"StructureAware OCR pabeigts: {processing_time}ms, confidence: {weighted_confidence:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Kļūda StructureAware OCR: {str(e)}")
            # Safe fallback - return minimal result
            return StructureAwareOCRResult(
                text="",
                confidence=0.0,
                structure=DocumentStructure(
                    image_width=0, image_height=0,
                    zones=[], tables=[], text_blocks=[]
                ),
                zone_results={},
                table_results=[],
                enhanced_text="",
                processing_time_ms=0
            )
    
    async def _process_zone_ocr(self, image_path: str, zone: DocumentZone) -> Dict[str, Any]:
        """
        Apstrādā konkrētu zonu ar optimizētu OCR
        
        Args:
            image_path: Ceļš uz attēlu
            zone: Zona ko apstrādāt
            
        Returns:
            OCR rezultāts šai zonai
        """
        try:
            config = self.zone_configs.get(zone.zone_type)
            if not config:
                self.logger.warning(f"Nav konfigurācijas priekš zona tipa: {zone.zone_type}")
                return await self._process_standard_zone(image_path, zone)
            
            # 1. Izgriezīs zonas attēlu
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Nevar ielādēt attēlu: {image_path}")
            
            zone_image = image[
                zone.bounds.y1:zone.bounds.y2,
                zone.bounds.x1:zone.bounds.x2
            ]
            
            # 2. Preprocess ar zone-specific parametriem
            processed_image = await self._preprocess_zone_image(zone_image, config.preprocessing_steps)
            
            # 3. OCR ar zone-specific config
            # Šeit izmantojam esošo OCR servisu ar custom parametriem
            zone_result = await self._extract_text_from_zone(
                processed_image, 
                config.tesseract_config,
                config.confidence_threshold
            )
            
            # 4. Text cleaning ar zone-specific līmeni
            cleaned_text = await self._clean_zone_text(
                zone_result.get('text', ''),
                config.text_cleaning_level
            )
            
            return {
                'text': cleaned_text,
                'raw_text': zone_result.get('text', ''),
                'confidence': zone_result.get('confidence', 0.0),
                'zone_type': zone.zone_type.value,
                'bounds': asdict(zone.bounds),
                'config_used': asdict(config)
            }
            
        except Exception as e:
            self.logger.error(f"Kļūda zone OCR: {str(e)}")
            return await self._process_standard_zone(image_path, zone)
    
    async def _process_table_ocr(self, image_path: str, table: TableRegion) -> Dict[str, Any]:
        """
        Apstrādā tabulas ar cell-aware OCR
        
        Args:
            image_path: Ceļš uz attēlu
            table: Tabulas informācija
            
        Returns:
            Strukturēts tabulas rezultāts
        """
        try:
            # 1. Izgriezīs tabulas attēlu
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Nevar ielādēt attēlu: {image_path}")
            
            table_image = image[
                table.bounds.y1:table.bounds.y2,
                table.bounds.x1:table.bounds.x2
            ]
            
            # 2. Process katru šūnu atsevišķi
            cell_results = []
            for cell in table.cells:
                # Adjust cell coordinates to table-relative
                rel_cell = BoundingBox(
                    x1=max(0, cell.bounds.x1 - table.bounds.x1),
                    y1=max(0, cell.bounds.y1 - table.bounds.y1),
                    x2=min(table_image.shape[1], cell.bounds.x2 - table.bounds.x1),
                    y2=min(table_image.shape[0], cell.bounds.y2 - table.bounds.y1)
                )
                
                # Izgriezīs šūnas attēlu ar padding
                padding = self.table_configs["cell_padding"]
                cell_image = table_image[
                    max(0, rel_cell.y1 - padding):min(table_image.shape[0], rel_cell.y2 + padding),
                    max(0, rel_cell.x1 - padding):min(table_image.shape[1], rel_cell.x2 + padding)
                ]
                
                if cell_image.size > 0:
                    # OCR šūnai ar table-specific config
                    cell_ocr = await self._extract_text_from_zone(
                        cell_image,
                        self.zone_configs[ZoneType.TABLE].tesseract_config,
                        self.zone_configs[ZoneType.TABLE].confidence_threshold
                    )
                    
                    cell_results.append({
                        'text': cell_ocr.get('text', '').strip(),
                        'confidence': cell_ocr.get('confidence', 0.0),
                        'row': cell.row_index,
                        'column': cell.column_index,
                        'bounds': asdict(cell.bounds)
                    })
            
            # 3. Konstruē tabulas matricu
            table_matrix = self._build_table_matrix(cell_results)
            
            return {
                'cells': cell_results,
                'matrix': table_matrix,
                'table_bounds': asdict(table.bounds),
                'rows': table.rows,
                'columns': table.columns,
                'confidence': table.confidence
            }
            
        except Exception as e:
            self.logger.error(f"Kļūda table OCR: {str(e)}")
            return {
                'cells': [],
                'matrix': [],
                'table_bounds': asdict(table.bounds),
                'rows': 0,
                'columns': 0,
                'confidence': 0.0
            }
    
    async def _preprocess_zone_image(self, image: np.ndarray, steps: List[str]) -> np.ndarray:
        """Preprocess attēlu ar zone-specific soļiem"""
        processed = image.copy()
        
        for step in steps:
            if step == "deskew":
                processed = self._deskew_image(processed)
            elif step == "denoise":
                processed = cv2.fastNlMeansDenoisingColored(processed)
            elif step == "enhance_contrast":
                processed = self._enhance_contrast(processed)
            elif step == "morphology":
                processed = self._apply_morphology(processed)
        
        return processed
    
    async def _extract_text_from_zone(self, image: np.ndarray, tesseract_config: str, threshold: float) -> Dict[str, Any]:
        """
        Izvelk tekstu no zonas ar custom parametriem
        
        Args:
            image: Preprocessēts attēls
            tesseract_config: Tesseract konfigurācija
            threshold: Confidence slieksnis
            
        Returns:
            OCR rezultāts
        """
        try:
            # Izmantojam esošo OCR servisu ar custom parametriem
            # Šeit varētu būt vajadzīga paplašināšana OCRService
            
            # Pagaidām izmantojam standard metodi
            # TODO: Paplašināt OCRService lai atbalsta custom tesseract config
            
            import pytesseract
            import tempfile
            import os
            import time
            
            # Saglabā temp failu ar unique name
            temp_suffix = f"_{int(time.time() * 1000000)}.png"
            with tempfile.NamedTemporaryFile(suffix=temp_suffix, delete=False) as tmp_file:
                temp_path = tmp_file.name
                
            try:
                cv2.imwrite(temp_path, image)
                
                # OCR ar custom config
                text = pytesseract.image_to_string(image, config=tesseract_config)
                
                # Get confidence data
                data = pytesseract.image_to_data(image, config=tesseract_config, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                return {
                    'text': text,
                    'confidence': avg_confidence / 100.0  # Convert to 0-1 range
                }
                
            finally:
                # Cleanup temp file
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except Exception as cleanup_error:
                    self.logger.warning(f"Nevarēja iztīrīt temp failu {temp_path}: {cleanup_error}")
                
        except Exception as e:
            self.logger.error(f"Kļūda zone OCR extraction: {str(e)}")
            return {'text': '', 'confidence': 0.0}
    
    async def _clean_zone_text(self, text: str, level: str) -> str:
        """
        Tīra tekstu ar zone-specific līmeni
        
        Args:
            text: Sākotnējais teksts
            level: Tīrīšanas līmenis ('light', 'medium', 'aggressive')
            
        Returns:
            Iztīrītais teksts
        """
        if not text:
            return text
        
        # Izmantojam esošo text_cleaner ar dažādām intensitātēm
        if hasattr(self.ocr_service, 'text_cleaner'):
            if level == "light":
                return self.ocr_service.text_cleaner.basic_clean(text)
            elif level == "medium":
                return self.ocr_service.text_cleaner.clean_text(text)
            elif level == "aggressive":
                # Vairākas tīrīšanas fāzes
                cleaned = self.ocr_service.text_cleaner.clean_text(text)
                return self.ocr_service.text_cleaner.advanced_clean(cleaned)
        
        # Fallback uz basic cleaning
        return text.strip()
    
    def _create_enhanced_text(self, base_text: str, zone_results: Dict[str, Any], 
                            table_results: List[Dict[str, Any]], structure: DocumentStructure) -> str:
        """
        Izveido uzlabotu tekstu ar struktūras kontekstu
        
        Args:
            base_text: Pamata OCR teksts
            zone_results: Zonu rezultāti
            table_results: Tabulu rezultāti
            structure: Struktūras informācija
            
        Returns:
            Enhanced teksts ar strukturālām iezīmēm
        """
        enhanced_lines = []
        
        # Pievienojam zone-specific content
        for zone_type in [ZoneType.HEADER, ZoneType.BODY, ZoneType.SUMMARY, ZoneType.FOOTER]:
            if zone_type.value in zone_results:
                zone_data = zone_results[zone_type.value]
                zone_text = zone_data.get('text', '').strip()
                if zone_text:
                    enhanced_lines.extend([
                        f"[{zone_type.value.upper()}]",
                        zone_text,
                        ""
                    ])
        
        # Pievienojam tabulu saturu strukturētā veidā
        for i, table_result in enumerate(table_results):
            if table_result.get('matrix'):
                enhanced_lines.append(f"[TABLE_{i+1}]")
                enhanced_lines.extend(
                    " | ".join(str(cell) for cell in row)
                    for row in table_result['matrix']
                )
                enhanced_lines.append("")
        
        # Ja nav struktūras rezultātu, atgriežam base text
        return "\n".join(enhanced_lines) if enhanced_lines else base_text
    
    def _calculate_weighted_confidence(self, base_confidence: float, 
                                     zone_results: Dict[str, Any], 
                                     table_results: List[Dict[str, Any]]) -> float:
        """
        Aprēķina svērto confidence balstoties uz zonu svarīgumu
        
        Args:
            base_confidence: Pamata confidence
            zone_results: Zonu rezultāti
            table_results: Tabulu rezultāti
            
        Returns:
            Svērtais confidence
        """
        if not zone_results and not table_results:
            return base_confidence
        
        total_weight = 0
        weighted_sum = 0
        
        # Zonu confidence ar weight
        for zone_type_str, zone_data in zone_results.items():
            try:
                zone_type = ZoneType(zone_type_str)
                weight = self.confidence_weights.get(zone_type, 1.0)
                confidence = zone_data.get('confidence', 0.0)
                
                weighted_sum += confidence * weight
                total_weight += weight
            except ValueError:
                continue
        
        # Tabulu confidence
        for table_result in table_results:
            weight = self.confidence_weights.get(ZoneType.TABLE, 1.0)
            confidence = table_result.get('confidence', 0.0)
            
            weighted_sum += confidence * weight
            total_weight += weight
        
        if total_weight > 0:
            weighted_confidence = weighted_sum / total_weight
            # Kombinē ar base confidence
            return (weighted_confidence + base_confidence) / 2
        
        return base_confidence
    
    async def _process_standard_zone(self, image_path: str, zone: DocumentZone) -> Dict[str, Any]:
        """Fallback uz standard OCR zonai"""
        try:
            # Izmantojam standard OCR
            result = await self.ocr_service.extract_text_from_image(image_path)
            return {
                'text': result.get('text', ''),
                'raw_text': result.get('text', ''),
                'confidence': result.get('confidence', 0.0),
                'zone_type': zone.zone_type.value,
                'bounds': asdict(zone.bounds),
                'config_used': 'standard'
            }
        except Exception as e:
            self.logger.error(f"Standard zone fallback kļūda: {str(e)}")
            return {
                'text': '',
                'raw_text': '',
                'confidence': 0.0,
                'zone_type': zone.zone_type.value,
                'bounds': asdict(zone.bounds),
                'config_used': 'error'
            }
    
    def _build_table_matrix(self, cell_results: List[Dict[str, Any]]) -> List[List[str]]:
        """Konstruē tabulas matricu no šūnu rezultātiem"""
        if not cell_results:
            return []
        
        # Atrod maksimālos row/column indeksus
        max_row = max(cell.get('row', 0) for cell in cell_results)
        max_col = max(cell.get('column', 0) for cell in cell_results)
        
        # Inicializē matricu
        matrix = [["" for _ in range(max_col + 1)] for _ in range(max_row + 1)]
        
        # Aizpilda matricu
        for cell in cell_results:
            row = cell.get('row', 0)
            col = cell.get('column', 0)
            text = cell.get('text', '').strip()
            
            if 0 <= row <= max_row and 0 <= col <= max_col:
                matrix[row][col] = text
        
        return matrix
    
    # Helper methods for image preprocessing
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Izlabo attēla slīpumu"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None and len(lines) > 0:
            angles = []
            for line in lines[:10]:  # Izmanto pirmas 10 līnijas
                if len(line) >= 2:  # Pārbauda vai line ir pareizā formā
                    rho, theta = line[0], line[1] if len(line) > 1 else line[0][1]
                elif len(line[0]) >= 2:  # Ja line ir nested array
                    rho, theta = line[0][0], line[0][1]
                else:
                    continue  # Skip malformed lines
                    
                angle = theta * 180 / np.pi
                angles.append(angle)
            
            if angles:
                median_angle = np.median(angles)
                if abs(median_angle - 90) < abs(median_angle - 180):
                    skew_angle = median_angle - 90
                else:
                    skew_angle = median_angle - 180
                
                if abs(skew_angle) > 0.5:  # Tikai ja skew > 0.5 grādi
                    (h, w) = image.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
                    return cv2.warpAffine(image, M, (w, h), 
                                        flags=cv2.INTER_CUBIC, 
                                        borderMode=cv2.BORDER_REPLICATE)
        
        return image
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Uzlabo attēla kontrastu"""
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Adaptive histogram equalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    def _apply_morphology(self, image: np.ndarray) -> np.ndarray:
        """Piemēro morfoloģiskās operācijas"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Structural element
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        
        # Opening to remove noise
        opening = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
        
        # Convert back to BGR
        return cv2.cvtColor(opening, cv2.COLOR_GRAY2BGR)
    
    # POSM 4.5 Week 3 Enhancements
    async def process_with_context(self, image_path: str, context_data: Dict[str, Any] = None) -> StructureAwareOCRResult:
        """
        Enhanced OCR ar extended context integration
        
        Args:
            image_path: Ceļš uz attēla failu
            context_data: Papildu konteksta dati (supplier info, template hints, etc.)
        
        Returns:
            StructureAwareOCRResult: Enhanced rezultāts ar context insights
        """
        try:
            self.logger.info(f"🔍 Processing with enhanced context: {image_path}")
            
            # 1. Pamata structure-aware processing
            base_result = await self.process_with_structure(image_path)
            
            # 2. Context integration
            if context_data:
                await self._integrate_context(base_result, context_data)
            
            # 3. Zone insights generation
            zone_insights = await self.get_zone_insights(base_result)
            base_result.metadata["zone_insights"] = zone_insights
            
            # 4. Enhanced confidence calculation
            enhanced_confidence = await self._calculate_enhanced_confidence(base_result, context_data)
            base_result.overall_confidence = enhanced_confidence
            
            self.logger.info(f"✅ Enhanced processing completed: confidence={enhanced_confidence:.3f}")
            return base_result
            
        except Exception as e:
            self.logger.error(f"❌ Enhanced processing failed: {e}")
            # Safe fallback - return minimal result
            return StructureAwareOCRResult(
                full_text="",
                zone_texts={},
                confidence=0.0,
                overall_confidence=0.0,
                structure_analysis=None,
                processing_time_ms=0,
                zone_confidences={},
                metadata={"error": str(e), "fallback_mode": True}
            )
    
    async def get_zone_insights(self, result: StructureAwareOCRResult) -> Dict[str, Any]:
        """
        Analizē zone-specific insights no OCR rezultāta
        
        Args:
            result: StructureAwareOCRResult instance
        
        Returns:
            Dict ar zone insights
        """
        insights = {
            "zone_analysis": {},
            "confidence_distribution": {},
            "text_quality_metrics": {},
            "structure_coherence": 0.0
        }
        
        try:
            total_confidence = 0.0
            zone_count = 0
            
            # Analyze each zone
            for zone_type, zone_data in result.zone_results.items():
                if isinstance(zone_data, dict) and "confidence" in zone_data:
                    confidence = zone_data["confidence"]
                    text_length = len(zone_data.get("text", ""))
                    
                    insights["zone_analysis"][zone_type] = {
                        "confidence": confidence,
                        "text_length": text_length,
                        "quality_score": confidence * min(1.0, text_length / 50),  # Length-weighted quality
                        "issues": self._detect_zone_issues(zone_data)
                    }
                    
                    insights["confidence_distribution"][zone_type] = confidence
                    total_confidence += confidence
                    zone_count += 1
            
            # Calculate structure coherence
            if zone_count > 0:
                avg_confidence = total_confidence / zone_count
                confidence_variance = sum(
                    (conf - avg_confidence) ** 2 
                    for conf in insights["confidence_distribution"].values()
                ) / zone_count if zone_count > 0 else 0
                
                insights["structure_coherence"] = max(0.0, 1.0 - (confidence_variance / 0.25))  # Normalized variance
            
            # Text quality metrics
            insights["text_quality_metrics"] = {
                "average_confidence": total_confidence / zone_count if zone_count > 0 else 0.0,
                "confidence_variance": confidence_variance if zone_count > 0 else 0.0,
                "zone_count": zone_count,
                "total_text_length": sum(
                    len(data.get("text", "")) for data in result.zone_results.values() 
                    if isinstance(data, dict)
                )
            }
            
            self.logger.info(f"📊 Zone insights generated: coherence={insights['structure_coherence']:.3f}")
            return insights
            
        except Exception as e:
            self.logger.error(f"❌ Zone insights generation failed: {e}")
            return insights
    
    def _detect_zone_issues(self, zone_data: Dict[str, Any]) -> List[str]:
        """Analizē iespējamās problēmas zone datos"""
        issues = []
        
        if zone_data.get("confidence", 0) < 0.5:
            issues.append("low_confidence")
        
        text = zone_data.get("text", "")
        if len(text) < 10:
            issues.append("short_text")
        
        if len([c for c in text if c.isdigit()]) / max(len(text), 1) > 0.8:
            issues.append("mostly_numeric")
        
        if "?" in text or "�" in text:
            issues.append("encoding_issues")
        
        return issues
    
    async def _integrate_context(self, result: StructureAwareOCRResult, context_data: Dict[str, Any]):
        """Integrē konteksta datus rezultātā"""
        try:
            # Template-based optimization
            if "template_hints" in context_data:
                template_hints = context_data["template_hints"]
                await self._apply_template_optimization(result, template_hints)
            
            # Supplier-specific adjustments
            if "supplier_info" in context_data:
                supplier_info = context_data["supplier_info"]
                await self._apply_supplier_optimization(result, supplier_info)
            
            # Historical data integration
            if "historical_patterns" in context_data:
                patterns = context_data["historical_patterns"]
                await self._apply_pattern_optimization(result, patterns)
            
        except Exception as e:
            self.logger.error(f"❌ Context integration failed: {e}")
    
    async def _apply_template_optimization(self, result: StructureAwareOCRResult, template_hints: Dict[str, Any]):
        """Piemēro template-based optimizācijas"""
        # Template-specific zone adjustments
        for zone_type, hints in template_hints.items():
            if (
                zone_type in result.zone_results
                and isinstance(result.zone_results[zone_type], dict)
                and hints.get("reliability", 0) > 0.8
            ):
                zone_data = result.zone_results[zone_type]
                zone_data["confidence"] = min(1.0, zone_data.get("confidence", 0) * 1.1)
    
    async def _apply_supplier_optimization(self, result: StructureAwareOCRResult, supplier_info: Dict[str, Any]):
        """Piemēro supplier-specific optimizācijas"""
        # Known supplier format adjustments
        supplier_name = supplier_info.get("name", "")
        if supplier_name and "supplier" in result.zone_results:
            supplier_zone = result.zone_results["supplier"]
            if isinstance(supplier_zone, dict):
                # Boost confidence if extracted name matches known supplier
                extracted_text = supplier_zone.get("text", "")
                if supplier_name.lower() in extracted_text.lower():
                    supplier_zone["confidence"] = min(1.0, supplier_zone.get("confidence", 0) * 1.2)
    
    async def _apply_pattern_optimization(self, result: StructureAwareOCRResult, patterns: Dict[str, Any]):
        """Piemēro historical pattern optimizācijas"""
        # Apply pattern-based confidence adjustments
        for zone_type, pattern_data in patterns.items():
            if zone_type in result.zone_results and isinstance(result.zone_results[zone_type], dict):
                zone_data = result.zone_results[zone_type]
                expected_format = pattern_data.get("format", "")
                
                # Simple format validation boost
                if expected_format and self._matches_pattern(zone_data.get("text", ""), expected_format):
                    zone_data["confidence"] = min(1.0, zone_data.get("confidence", 0) * 1.15)
    
    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """Vienkārša pattern matching funkcija"""
        checks = {
            "date": lambda t: any(c.isdigit() for c in t) and any(c in "./-" for c in t),
            "amount": lambda t: any(c.isdigit() for c in t) and any(c in ".,€$" for c in t),
        }
        return checks.get(pattern, lambda t: False)(text)
    
    async def _calculate_enhanced_confidence(self, result: StructureAwareOCRResult, context_data: Dict[str, Any] = None) -> float:
        """Aprēķina enhanced confidence score"""
        try:
            # Base confidence from zones
            zone_confidences = [
                zone_data["confidence"]
                for zone_data in result.zone_results.values()
                if isinstance(zone_data, dict) and "confidence" in zone_data
            ]

            if not zone_confidences:
                return result.overall_confidence
            
            # Weighted average with emphasis on critical zones
            weights = {
                "supplier": 1.2,
                "document_number": 1.1, 
                "date": 1.0,
                "amount": 1.3,
                "table": 0.9
            }
            
            weighted_sum = 0.0
            total_weight = 0.0
            
            for zone_type, zone_data in result.zone_results.items():
                if isinstance(zone_data, dict) and "confidence" in zone_data:
                    weight = weights.get(zone_type, 1.0)
                    weighted_sum += zone_data["confidence"] * weight
                    total_weight += weight
            
            enhanced_confidence = weighted_sum / total_weight if total_weight > 0 else result.overall_confidence
            
            # Context bonus
            if context_data:
                context_bonus = min(0.1, len(context_data) * 0.02)  # Up to 10% bonus
                enhanced_confidence = min(1.0, enhanced_confidence + context_bonus)
            
            return enhanced_confidence
            
        except Exception as e:
            self.logger.error(f"❌ Enhanced confidence calculation failed: {e}")
            return result.overall_confidence
