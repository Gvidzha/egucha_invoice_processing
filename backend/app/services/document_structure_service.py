"""
Document Structure Analysis Service
Analizē dokumentu fizisko struktūru (tabulas, zonas, kolonnas)
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import asyncio
import json
from enum import Enum

logger = logging.getLogger(__name__)

class ZoneType(Enum):
    """Dokumenta zonu tipi"""
    HEADER = "header"
    SUPPLIER_INFO = "supplier_info"
    RECIPIENT_INFO = "recipient_info"
    INVOICE_DETAILS = "invoice_details"
    AMOUNTS = "amounts"
    TABLE = "table"
    FOOTER = "footer"
    BODY = "body"
    SUMMARY = "summary"

@dataclass
class BoundingBox:
    """Koordināšu taisnstūris"""
    x1: int
    y1: int
    x2: int
    y2: int
    
    @property
    def width(self) -> int:
        return self.x2 - self.x1
    
    @property
    def height(self) -> int:
        return self.y2 - self.y1
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    @property
    def center(self) -> Tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

@dataclass
class TableCell:
    """Tabulas šūna"""
    bounds: BoundingBox
    text: Optional[str] = None
    confidence: float = 0.0
    row_index: int = 0
    column_index: int = 0

@dataclass
class TableRegion:
    """Tabulas reģions dokumentā"""
    bounds: BoundingBox
    cells: List[TableCell]  # Flat list of cells
    confidence: float = 0.0
    rows: int = 0
    columns: int = 0
    
    def __post_init__(self):
        # Backward compatibility - if cells is 2D list, convert to flat
        if self.cells and isinstance(self.cells[0], list):
            flat_cells = []
            for row_cells in self.cells:
                flat_cells.extend(row_cells)
            self.cells = flat_cells
    
    @property
    def headers(self) -> List[str]:
        """Atgriež header row kā string list"""
        if not self.cells:
            return []
        # Atgriež pirmo rindu kā headers
        header_cells = [cell for cell in self.cells if cell.row_index == 0]
        return [cell.text or "" for cell in sorted(header_cells, key=lambda x: x.column_index)]
    
    @property
    def row_count(self) -> int:
        return self.rows
    
    @property
    def column_count(self) -> int:
        return self.columns

@dataclass
class DocumentZone:
    """Dokumenta zona (header/body/footer)"""
    zone_type: ZoneType  # Izmanto enum nevis string
    bounds: BoundingBox
    confidence: float = 0.0
    text_blocks: List[BoundingBox] = None
    
    def __post_init__(self):
        if self.text_blocks is None:
            self.text_blocks = []

    # Backward compatibility property
    @property
    def type(self) -> str:
        """Backward compatibility - atgriež zone_type kā string"""
        return self.zone_type.value

@dataclass
class DocumentStructure:
    """Pilna dokumenta struktūras informācija"""
    image_width: int
    image_height: int
    zones: List[DocumentZone]
    tables: List[TableRegion]
    text_blocks: List[BoundingBox]
    confidence: float = 0.0
    processing_time_ms: int = 0
    detected_at: datetime = None
    
    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertē uz dictionary JSON serialization vajadzībām"""
        return {
            "image_width": self.image_width,
            "image_height": self.image_height,
            "zones": [asdict(zone) for zone in self.zones],
            "tables": [asdict(table) for table in self.tables],
            "text_blocks": [asdict(block) for block in self.text_blocks],
            "confidence": self.confidence,
            "processing_time_ms": self.processing_time_ms,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None
        }

class DocumentStructureAnalyzer:
    """
    Galvenais Document Structure Analysis serviss
    
    Capabilities:
    - Table detection ar computer vision
    - Zone classification (header/body/footer)
    - Cell boundary detection
    - Column header recognition
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Table detection parametri
        self.table_detection_params = {
            "min_table_area": 5000,  # Minimālais tabulas laukums pikseļos
            "line_thickness": 2,     # Līniju biezums
            "min_line_length": 100,  # Minimālais līnijas garums
            "max_line_gap": 10,      # Maksimālais līnijas pārtraukums
        }
        
        # Zone detection parametri
        self.zone_detection_params = {
            "header_zone_ratio": 0.25,    # Header = top 25%
            "footer_zone_ratio": 0.15,    # Footer = bottom 15%
            "summary_zone_ratio": 0.20,   # Summary = bottom 20%
        }
        
        self.logger.info("DocumentStructureAnalyzer inicializēts")
    
    async def analyze_document(self, image_path: str) -> DocumentStructure:
        """
        Galvenā metode - analizē dokumenta struktūru
        
        Args:
            image_path: Ceļš uz attēlu
            
        Returns:
            DocumentStructure: Pilna struktūras informācija
        """
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"Sākam dokumenta struktūras analīzi: {image_path}")
            
            # Ielādēt attēlu
            image = await self._load_image(image_path)
            if image is None:
                raise ValueError(f"Nevarēja ielādēt attēlu: {image_path}")
            
            height, width = image.shape[:2]
            
            # Paralēlās operācijas
            tasks = [
                self._detect_zones(image),
                self._detect_tables(image),
                self._detect_text_blocks(image)
            ]
            
            zones, tables, text_blocks = await asyncio.gather(*tasks)
            
            # Aprēķināt kopējo confidence
            confidence = self._calculate_overall_confidence(zones, tables)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            structure = DocumentStructure(
                image_width=width,
                image_height=height,
                zones=zones,
                tables=tables,
                text_blocks=text_blocks,
                confidence=confidence,
                processing_time_ms=int(processing_time),
                detected_at=start_time
            )
            
            self.logger.info(f"Struktūras analīze pabeigta: {processing_time:.2f}ms, confidence: {confidence:.2f}")
            return structure
            
        except Exception as e:
            self.logger.error(f"Kļūda struktūras analīzē: {str(e)}")
            # Atgriež tukšu struktūru ar kļūdas informāciju
            return DocumentStructure(
                image_width=0,
                image_height=0,
                zones=[],
                tables=[],
                text_blocks=[],
                confidence=0.0,
                processing_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
            )
    
    async def _load_image(self, image_path: str) -> Optional[np.ndarray]:
        """Asinhronā attēla ielāde"""
        try:
            # OpenCV ielāde loop thread, lai nebloķētu
            loop = asyncio.get_event_loop()
            image = await loop.run_in_executor(None, cv2.imread, image_path)
            return image
        except Exception as e:
            self.logger.error(f"Kļūda attēla ielādē: {str(e)}")
            return None
    
    async def _detect_zones(self, image: np.ndarray) -> List[DocumentZone]:
        """
        Atpazīst dokumenta zonas (header, body, footer, summary)
        """
        height, width = image.shape[:2]
        zones = []
        
        # Header zone (top 25%)
        header_height = int(height * self.zone_detection_params["header_zone_ratio"])
        header_zone = DocumentZone(
            zone_type=ZoneType.HEADER,
            bounds=BoundingBox(0, 0, width, header_height),
            confidence=0.85  # Šobrīd static, vēlāk ar ML
        )
        zones.append(header_zone)
        
        # Footer zone (bottom 15%)
        footer_height = int(height * self.zone_detection_params["footer_zone_ratio"])
        footer_start = height - footer_height
        footer_zone = DocumentZone(
            zone_type=ZoneType.FOOTER,
            bounds=BoundingBox(0, footer_start, width, height),
            confidence=0.75
        )
        zones.append(footer_zone)
        
        # Summary zone (bottom 20%, overlaps with footer)
        summary_height = int(height * self.zone_detection_params["summary_zone_ratio"])
        summary_start = height - summary_height
        summary_zone = DocumentZone(
            zone_type=ZoneType.SUMMARY,
            bounds=BoundingBox(0, summary_start, width, height),
            confidence=0.70
        )
        zones.append(summary_zone)
        
        # Body zone (middle part)
        body_zone = DocumentZone(
            zone_type=ZoneType.BODY,
            bounds=BoundingBox(0, header_height, width, footer_start),
            confidence=0.90
        )
        zones.append(body_zone)
        
        self.logger.debug(f"Atpazītas {len(zones)} zonas")
        return zones
    
    async def _detect_tables(self, image: np.ndarray) -> List[TableRegion]:
        """
        Uzlabota tabulu atpazīšana ar vairākām metodēm un kvalitātes pārbaudi
        """
        try:
            tables = []
            
            # 1. Uzlabota morfologiskā pieeja
            tables_morphological = await self._detect_tables_morphological_enhanced(image)
            tables.extend(tables_morphological)
            
            # 2. Hough line detection ar adaptīviem parametriem
            tables_hough = await self._detect_tables_hough_enhanced(image)
            tables.extend(tables_hough)
            
            # 3. Contour-based ar uzlabotu filtrēšanu
            tables_contour = await self._detect_tables_contour_enhanced(image)
            tables.extend(tables_contour)
            
            # Apvienot overlapping tabulas un filtrēt kvalitāti
            tables = self._merge_overlapping_tables(tables)
            tables = self._filter_table_quality(tables, image.shape)
            
            self.logger.debug(f"Atpazītas {len(tables)} augstas kvalitātes tabulas")
            return tables
            
        except Exception as e:
            self.logger.error(f"Kļūda tabulu atpazīšanā: {e}")
            return []
    
    async def _detect_tables_morphological_enhanced(self, image: np.ndarray) -> List[TableRegion]:
        """Uzlabota morfologiskā tabulu atpazīšana"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Adaptīva binarizācija
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV, 15, 10)
        
        # Horizontālo līniju atpazīšana ar adaptīvu kernel izmēru
        h_kernel_size = max(30, image.shape[1] // 30)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_kernel_size, 1))
        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
        
        # Vertikālo līniju atpazīšana
        v_kernel_size = max(15, image.shape[0] // 50)
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_kernel_size))
        vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
        
        # Apvienot līnijas
        table_mask = cv2.bitwise_or(horizontal_lines, vertical_lines)
        
        # Morfologiskā slēgšana lai savienotu pārtrauktās līnijas
        closing_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        table_mask = cv2.morphologyEx(table_mask, cv2.MORPH_CLOSE, closing_kernel)
        
        # Atrast kontūras
        contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        tables = []
        min_area = max(5000, (image.shape[0] * image.shape[1]) * 0.005)  # Min 0.5% no attēla
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Pārbaudīt aspect ratio - tabulas parasti nav pārāk šauras
                aspect_ratio = w / h if h > 0 else 0
                if 0.3 <= aspect_ratio <= 10:
                    
                    # Analizēt šūnu struktūru
                    cells = await self._analyze_table_cells_enhanced(image[y:y+h, x:x+w])
                    
                    # Aprēķināt confidence balstoties uz struktūru
                    confidence = self._calculate_table_confidence(cells, w, h, area)
                    
                    table = TableRegion(
                        bounds=BoundingBox(x, y, x + w, y + h),
                        cells=cells,
                        confidence=confidence
                    )
                    tables.append(table)
        
        return tables
    
    async def _detect_tables_hough_enhanced(self, image: np.ndarray) -> List[TableRegion]:
        """Uzlabota Hough line tabulu atpazīšana"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Gaussian blur ar adaptīvu kernel
        kernel_size = max(3, min(7, image.shape[0] // 200))
        if kernel_size % 2 == 0:
            kernel_size += 1
        blurred = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)
        
        # Canny edge detection ar adaptīviem sliekšņiem
        median_val = np.median(blurred)
        lower = int(max(0, 0.7 * median_val))
        upper = int(min(255, 1.3 * median_val))
        edges = cv2.Canny(blurred, lower, upper)
        
        # Hough line detection
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 
                              threshold=max(50, image.shape[1] // 15),
                              minLineLength=image.shape[1] // 10,
                              maxLineGap=image.shape[1] // 25)
        
        if lines is None:
            return []
        
        # Klasificēt un apvienot līnijas
        horizontal_lines = []
        vertical_lines = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            
            if abs(angle) <= 10 or abs(angle) >= 170:
                horizontal_lines.append(line[0])
            elif abs(angle - 90) <= 10 or abs(angle + 90) <= 10:
                vertical_lines.append(line[0])
        
        # Apvienot paralēlās līnijas
        horizontal_lines = self._merge_parallel_lines(horizontal_lines, True)
        vertical_lines = self._merge_parallel_lines(vertical_lines, False)
        
        # Atrast tabulu reģionus no līniju krustpunktiem
        tables = []
        for i, h_line in enumerate(horizontal_lines[:-1]):
            for j, v_line in enumerate(vertical_lines[:-1]):
                # Aprēķināt iespējamo tabulas reģionu
                next_h = horizontal_lines[i + 1] if i + 1 < len(horizontal_lines) else None
                next_v = vertical_lines[j + 1] if j + 1 < len(vertical_lines) else None
                
                if next_h and next_v:
                    x1 = min(v_line[0], v_line[2])
                    y1 = min(h_line[1], h_line[3])
                    x2 = max(next_v[0], next_v[2])
                    y2 = max(next_h[1], next_h[3])
                    
                    if x2 > x1 and y2 > y1:
                        w, h = x2 - x1, y2 - y1
                        if w * h > 5000:  # Minimālais tabulas izmērs
                            table = TableRegion(
                                bounds=BoundingBox(x1, y1, x2, y2),
                                cells=[],
                                confidence=0.75
                            )
                            tables.append(table)
        
        return tables
    
    async def _detect_tables_contour_enhanced(self, image: np.ndarray) -> List[TableRegion]:
        """Uzlabota contour-based tabulu atpazīšana"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Adaptīva threshold
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV, 11, 2)
        
        # Morfologiskās operācijas lai uzlabotu struktūru
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Atrast kontūras
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        tables = []
        image_area = image.shape[0] * image.shape[1]
        
        for contour in contours:
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            
            # Filtrēt pēc izmēra un formas
            if area > image_area * 0.002 and perimeter > 0:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Pārbaudīt vai forma ir taisnstūrveida (tabulas pazīme)
                rect_area = w * h
                area_ratio = area / rect_area if rect_area > 0 else 0
                
                if area_ratio > 0.5:  # Pietiekami taisnstūrveida
                    aspect_ratio = w / h if h > 0 else 0
                    if 0.2 <= aspect_ratio <= 15:  # Ļoti plašs diapazons
                        confidence = min(0.8, area_ratio * 0.8 + 0.3)
                        
                        table = TableRegion(
                            bounds=BoundingBox(x, y, x + w, y + h),
                            cells=[],
                            confidence=confidence
                        )
                        tables.append(table)
        
        return tables
    
    async def _analyze_table_cells_enhanced(self, table_region: np.ndarray) -> List[TableCell]:
        """Uzlabota šūnu analīze tabulas reģionā"""
        if table_region.size == 0:
            return []
        
        gray = cv2.cvtColor(table_region, cv2.COLOR_BGR2GRAY) if len(table_region.shape) == 3 else table_region
        
        # Adaptīva binarizācija šūnu robežu atpazīšanai
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV, 11, 2)
        
        # Atrast potenciālās šūnu robežas
        contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        cells = []
        min_cell_area = max(100, table_region.shape[0] * table_region.shape[1] * 0.001)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_cell_area:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Pārbaudīt vai forma ir šūnas veida
                if w > 10 and h > 10:  # Minimālais šūnas izmērs
                    cell = TableCell(
                        bounds=BoundingBox(x, y, x + w, y + h),
                        text="",  # Teksts tiks pievienots ar OCR
                        confidence=0.7
                    )
                    cells.append(cell)
        
        return cells
    
    def _merge_parallel_lines(self, lines: List, is_horizontal: bool) -> List:
        """Apvieno paralēlās līnijas"""
        if not lines:
            return []
        
        merged = []
        tolerance = 15  # Pikseļu tolerance
        
        # Kārtot līnijas
        if is_horizontal:
            lines.sort(key=lambda line: (line[1] + line[3]) // 2)
        else:
            lines.sort(key=lambda line: (line[0] + line[2]) // 2)
        
        current_group = [lines[0]]
        
        for i in range(1, len(lines)):
            current_line = lines[i]
            last_line = current_group[-1]
            
            if is_horizontal:
                current_pos = (current_line[1] + current_line[3]) // 2
                last_pos = (last_line[1] + last_line[3]) // 2
            else:
                current_pos = (current_line[0] + current_line[2]) // 2
                last_pos = (last_line[0] + last_line[2]) // 2
            
            if abs(current_pos - last_pos) <= tolerance:
                current_group.append(current_line)
            else:
                if current_group:
                    merged_line = self._merge_line_group(current_group, is_horizontal)
                    merged.append(merged_line)
                current_group = [current_line]
        
        if current_group:
            merged_line = self._merge_line_group(current_group, is_horizontal)
            merged.append(merged_line)
        
        return merged
    
    def _merge_line_group(self, lines: List, is_horizontal: bool) -> List:
        """Apvieno līniju grupu"""
        if not lines:
            return []
        
        if is_horizontal:
            avg_y1 = sum(line[1] for line in lines) // len(lines)
            avg_y2 = sum(line[3] for line in lines) // len(lines)
            min_x = min(min(line[0], line[2]) for line in lines)
            max_x = max(max(line[0], line[2]) for line in lines)
            return [min_x, avg_y1, max_x, avg_y2]
        else:
            avg_x1 = sum(line[0] for line in lines) // len(lines)
            avg_x2 = sum(line[2] for line in lines) // len(lines)
            min_y = min(min(line[1], line[3]) for line in lines)
            max_y = max(max(line[1], line[3]) for line in lines)
            return [avg_x1, min_y, avg_x2, max_y]
    
    def _merge_overlapping_tables(self, tables: List[TableRegion]) -> List[TableRegion]:
        """Apvieno pārklājošās tabulas"""
        if len(tables) <= 1:
            return tables
        
        merged = []
        used = set()
        
        for i, table1 in enumerate(tables):
            if i in used:
                continue
                
            current_group = [table1]
            used.add(i)
            
            for j, table2 in enumerate(tables[i+1:], i+1):
                if j in used:
                    continue
                    
                # Pārbaudīt pārklāšanos
                overlap = self._calculate_bbox_overlap(table1.bounds, table2.bounds)
                if overlap > 0.3:  # 30% pārklāšanās
                    current_group.append(table2)
                    used.add(j)
            
            # Apvienot grupu
            if len(current_group) == 1:
                merged.append(current_group[0])
            else:
                merged_table = self._merge_table_group(current_group)
                merged.append(merged_table)
        
        return merged
    
    def _calculate_bbox_overlap(self, bbox1: BoundingBox, bbox2: BoundingBox) -> float:
        """Aprēķina bounding box pārklāšanās koeficientu"""
        # Aprēķināt krustojuma laukumu
        x_overlap = max(0, min(bbox1.x2, bbox2.x2) - max(bbox1.x1, bbox2.x1))
        y_overlap = max(0, min(bbox1.y2, bbox2.y2) - max(bbox1.y1, bbox2.y1))
        intersection_area = x_overlap * y_overlap
        
        # Aprēķināt savienojuma laukumu
        area1 = (bbox1.x2 - bbox1.x1) * (bbox1.y2 - bbox1.y1)
        area2 = (bbox2.x2 - bbox2.x1) * (bbox2.y2 - bbox2.y1)
        union_area = area1 + area2 - intersection_area
        
        return intersection_area / union_area if union_area > 0 else 0
    
    def _merge_table_group(self, tables: List[TableRegion]) -> TableRegion:
        """Apvieno tabulu grupu vienā tabulā"""
        if not tables:
            return None
        
        # Aprēķināt apvienoto bounding box
        min_x = min(table.bounds.x1 for table in tables)
        min_y = min(table.bounds.y1 for table in tables)
        max_x = max(table.bounds.x2 for table in tables)
        max_y = max(table.bounds.y2 for table in tables)
        
        # Apvienot šūnas
        all_cells = []
        for table in tables:
            all_cells.extend(table.cells)
        
        # Aprēķināt vidējo confidence
        avg_confidence = sum(table.confidence for table in tables) / len(tables)
        
        return TableRegion(
            bounds=BoundingBox(min_x, min_y, max_x, max_y),
            cells=all_cells,
            confidence=min(0.95, avg_confidence * 1.1)  # Nedaudz paaugstina confidence apvienotajām
        )
    
    def _filter_table_quality(self, tables: List[TableRegion], image_shape: tuple) -> List[TableRegion]:
        """Filtrē tabulas pēc kvalitātes kritērijiem"""
        if not tables:
            return []
        
        filtered = []
        image_area = image_shape[0] * image_shape[1]
        
        for table in tables:
            # Aprēķināt tabulas laukumu
            table_area = (table.bounds.x2 - table.bounds.x1) * (table.bounds.y2 - table.bounds.y1)
            
            # Kvalitātes kritēriji
            min_area = image_area * 0.002  # Min 0.2% no attēla
            max_area = image_area * 0.8    # Max 80% no attēla
            
            if min_area <= table_area <= max_area:
                # Pārbaudīt aspect ratio
                width = table.bounds.x2 - table.bounds.x1
                height = table.bounds.y2 - table.bounds.y1
                aspect_ratio = width / height if height > 0 else 0
                
                if 0.1 <= aspect_ratio <= 20:  # Ļoti plašs diapazons
                    # Pārbaudīt confidence
                    if table.confidence >= 0.3:
                        filtered.append(table)
        
        return filtered
    
    def _calculate_table_confidence(self, cells: List[TableCell], width: int, height: int, area: float) -> float:
        """Aprēķina tabulas confidence balstoties uz struktūru"""
        base_confidence = 0.5
        
        # Šūnu daudzums palielina confidence
        if len(cells) >= 4:
            base_confidence += 0.2
        if len(cells) >= 9:
            base_confidence += 0.1
        
        # Tabulas izmērs - vidējas tabulas ir visticamākās
        if 10000 <= area <= 100000:
            base_confidence += 0.1
        
        # Aspect ratio - tabulas parasti nav kvadrātveida
        aspect_ratio = width / height if height > 0 else 0
        if 1.5 <= aspect_ratio <= 8:
            base_confidence += 0.1
        
        return min(0.95, base_confidence)
    
    async def _detect_text_blocks(self, image: np.ndarray) -> List[BoundingBox]:
        """
        Teksta bloku atpazīšana
        """
        # Šobrīd vienkāršota implementācija
        # Vēlāk var izmantot EAST text detector vai līdzīgu
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Simple contour-based text block detection
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Morphological operations to connect text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        text_blocks = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter tiny regions
            if w < 10 or h < 10:
                continue
                
            text_blocks.append(BoundingBox(x, y, x + w, y + h))
        
        self.logger.debug(f"Atpazīti {len(text_blocks)} teksta bloki")
        return text_blocks
    
    def _calculate_overall_confidence(self, zones: List[DocumentZone], tables: List[TableRegion]) -> float:
        """Aprēķina kopējo struktūras analīzes confidence"""
        if not zones and not tables:
            return 0.0
        
        # Weighted average
        zone_confidence = sum(zone.confidence for zone in zones) / len(zones) if zones else 0.0
        table_confidence = sum(table.confidence for table in tables) / len(tables) if tables else 0.0
        
        # Zones are more reliable than table detection currently
        if zones and tables:
            return (zone_confidence * 0.7) + (table_confidence * 0.3)
        elif zones:
            return zone_confidence * 0.8  # Slightly lower if no tables
        else:
            return table_confidence * 0.6  # Much lower if only tables

# Factory function priekš async creation
async def create_document_structure_analyzer() -> DocumentStructureAnalyzer:
    """Factory function DocumentStructureAnalyzer izveidošanai"""
    return DocumentStructureAnalyzer()
