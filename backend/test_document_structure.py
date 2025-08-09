"""
Tests for Document Structure Analysis service - POSM 4.5
Pārbauda DocumentStructureAnalyzer servisa darbību un visu objektu importus
"""

import pytest
import asyncio
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import os
import json

# Test imports
try:
    from app.services.document_structure_service import (
        DocumentStructureAnalyzer,
        BoundingBox,
        TableCell,
        TableRegion,
        DocumentZone,
        DocumentStructure
    )
    print("✅ Visi document structure servisa objekti veiksmīgi importēti")
except ImportError as e:
    print(f"❌ Kļūda importējot document structure objektus: {e}")
    raise

try:
    from app.models import Invoice
    print("✅ Invoice modelis veiksmīgi importēts")
except ImportError as e:
    print(f"❌ Kļūda importējot Invoice modeli: {e}")
    raise

try:
    import cv2
    import numpy as np
    print("✅ OpenCV un NumPy bibliotēkas pieejamas")
except ImportError as e:
    print(f"❌ Kļūda importējot CV bibliotēkas: {e}")
    raise


class TestDocumentStructureObjects:
    """Testi document structure objektiem"""
    
    def test_bounding_box_creation(self):
        """Testa BoundingBox objekta izveidi"""
        bbox = BoundingBox(10, 20, 100, 150)
        assert bbox.x1 == 10
        assert bbox.y1 == 20
        assert bbox.x2 == 100
        assert bbox.y2 == 150
        print("✅ BoundingBox objekts darbojas korekti")
    
    def test_table_cell_creation(self):
        """Testa TableCell objekta izveidi"""
        bbox = BoundingBox(0, 0, 50, 25)
        cell = TableCell(bounds=bbox, text="Test cell", confidence=0.85)
        assert cell.bounds == bbox
        assert cell.text == "Test cell"
        assert cell.confidence == 0.85
        print("✅ TableCell objekts darbojas korekti")
    
    def test_table_region_creation(self):
        """Testa TableRegion objekta izveidi"""
        bbox = BoundingBox(0, 0, 200, 100)
        cells = [
            [TableCell(BoundingBox(0, 0, 50, 25), "Cell 1", 0.9),
             TableCell(BoundingBox(50, 0, 100, 25), "Cell 2", 0.8)]
        ]
        
        table = TableRegion(
            bounds=bbox,
            cells=cells,
            headers=["Header 1", "Header 2"],
            confidence=0.9
        )
        
        assert table.bounds == bbox
        assert len(table.cells) == 1
        assert len(table.cells[0]) == 2
        assert len(table.headers) == 2
        assert table.confidence == 0.9
        print("✅ TableRegion objekts darbojas korekti")
    
    def test_document_zone_creation(self):
        """Testa DocumentZone objekta izveidi"""
        bbox = BoundingBox(0, 0, 800, 200)
        zone = DocumentZone(type="header", bounds=bbox, confidence=0.95)
        
        assert zone.type == "header"
        assert zone.bounds == bbox
        assert zone.confidence == 0.95
        print("✅ DocumentZone objekts darbojas korekti")
    
    def test_document_structure_creation(self):
        """Testa DocumentStructure objekta izveidi"""
        zones = [DocumentZone("header", BoundingBox(0, 0, 800, 100), 0.9)]
        tables = [TableRegion(BoundingBox(0, 100, 800, 300), [[]], [], 0.8)]
        text_blocks = [BoundingBox(0, 300, 800, 500)]
        
        structure = DocumentStructure(
            image_width=800,
            image_height=600,
            zones=zones,
            tables=tables,
            text_blocks=text_blocks,
            confidence=0.85,
            processing_time_ms=150
        )
        
        assert structure.image_width == 800
        assert structure.image_height == 600
        assert len(structure.zones) == 1
        assert len(structure.tables) == 1
        assert len(structure.text_blocks) == 1
        assert structure.confidence == 0.85
        assert structure.processing_time_ms == 150
        print("✅ DocumentStructure objekts darbojas korekti")


class TestDocumentStructureAnalyzer:
    """Testi DocumentStructureAnalyzer servisam"""
    
    @pytest.fixture
    def analyzer(self):
        """Izveido DocumentStructureAnalyzer instanci testiem"""
        return DocumentStructureAnalyzer()
    
    @pytest.fixture
    def test_image(self):
        """Izveido testa attēlu"""
        # Izveido vienkāršu testa attēlu ar tabulas struktūru
        image = np.ones((600, 800, 3), dtype=np.uint8) * 255  # Balts fons
        
        # Pievienot horizontālās līnijas (tabulas rindas)
        cv2.line(image, (50, 100), (750, 100), (0, 0, 0), 2)  # Header līnija
        cv2.line(image, (50, 150), (750, 150), (0, 0, 0), 1)  # Rindu līnijas
        cv2.line(image, (50, 200), (750, 200), (0, 0, 0), 1)
        cv2.line(image, (50, 250), (750, 250), (0, 0, 0), 1)
        
        # Pievienot vertikālās līnijas (tabulas kolonnas)
        cv2.line(image, (50, 100), (50, 250), (0, 0, 0), 2)   # Kreisā mala
        cv2.line(image, (200, 100), (200, 250), (0, 0, 0), 1) # Kolonna 1
        cv2.line(image, (400, 100), (400, 250), (0, 0, 0), 1) # Kolonna 2
        cv2.line(image, (600, 100), (600, 250), (0, 0, 0), 1) # Kolonna 3
        cv2.line(image, (750, 100), (750, 250), (0, 0, 0), 2) # Labā mala
        
        # Pievienot tekstu simulācijai
        cv2.putText(image, "Invoice Header", (300, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image, "Product", (75, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        cv2.putText(image, "Quantity", (220, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        cv2.putText(image, "Price", (450, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        cv2.putText(image, "Total", (650, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        
        return image
    
    def test_analyzer_initialization(self, analyzer):
        """Testa analyzer inicializāciju"""
        assert analyzer is not None
        assert hasattr(analyzer, 'zone_detection_params')
        assert hasattr(analyzer, 'table_detection_params')
        assert hasattr(analyzer, 'logger')
        print("✅ DocumentStructureAnalyzer inicializācija veiksmīga")
    
    @pytest.mark.asyncio
    async def test_zone_detection(self, analyzer, test_image):
        """Testa zonu atpazīšanu"""
        zones = await analyzer._detect_zones(test_image)
        
        assert len(zones) > 0, "Jāatpazīst vismaz viena zona"
        
        # Pārbaudīt ka ir galvenās zonas
        zone_types = [zone.type for zone in zones]
        assert "header" in zone_types, "Jāatpazīst header zona"
        assert "body" in zone_types, "Jāatpazīst body zona"
        assert "footer" in zone_types, "Jāatpazīst footer zona"
        
        # Pārbaudīt confidence vērtības
        for zone in zones:
            assert 0 <= zone.confidence <= 1, f"Zone confidence ārpus diapazona: {zone.confidence}"
        
        print(f"✅ Zonu atpazīšana veiksmīga: {len(zones)} zonas atrastas")
        for zone in zones:
            print(f"  - {zone.type}: confidence {zone.confidence:.2f}")
    
    @pytest.mark.asyncio
    async def test_table_detection_morphological(self, analyzer, test_image):
        """Testa uzlaboto morfologisko tabulu atpazīšanu"""
        tables = await analyzer._detect_tables_morphological_enhanced(test_image)
        
        assert len(tables) > 0, "Jāatpazīst vismaz viena tabula"
        
        for table in tables:
            assert table.bounds is not None, "Tabulas bounds nedrīkst būt None"
            assert 0 <= table.confidence <= 1, f"Table confidence ārpus diapazona: {table.confidence}"
            
            # Pārbaudīt ka tabula nav pārāk maza
            width = table.bounds.x2 - table.bounds.x1
            height = table.bounds.y2 - table.bounds.y1
            assert width > 50, f"Tabula pārāk šaura: {width}"
            assert height > 30, f"Tabula pārāk zema: {height}"
        
        print(f"✅ Morfologiskā tabulu atpazīšana: {len(tables)} tabulas atrastas")
    
    @pytest.mark.asyncio
    async def test_table_detection_hough(self, analyzer, test_image):
        """Testa Hough line tabulu atpazīšanu"""
        tables = await analyzer._detect_tables_hough_enhanced(test_image)
        
        # Hough metode var neatrast tabulas vienkāršā testā, bet nedrīkst crashot
        assert isinstance(tables, list), "Tables jābūt list objektam"
        
        for table in tables:
            assert table.bounds is not None
            assert 0 <= table.confidence <= 1
        
        print(f"✅ Hough tabulu atpazīšana: {len(tables)} tabulas atrastas")
    
    @pytest.mark.asyncio
    async def test_full_document_analysis(self, analyzer, test_image):
        """Testa pilnu dokumenta struktūras analīzi"""
        # Izveidot temporary failu testam
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            cv2.imwrite(tmp_path, test_image)
        
        try:
            # Veikt pilnu analīzi
            structure = await analyzer.analyze_document(tmp_path)
            
            assert structure is not None, "Struktūra nedrīkst būt None"
            assert structure.image_width == test_image.shape[1]
            assert structure.image_height == test_image.shape[0]
            assert len(structure.zones) > 0, "Jāatrod vismaz viena zona"
            assert 0 <= structure.confidence <= 1, "Confidence ārpus diapazona"
            assert structure.processing_time_ms > 0, "Processing time jābūt pozitīvam"
            
            print("✅ Pilna dokumenta struktūras analīze veiksmīga:")
            print(f"  - Attēla izmērs: {structure.image_width}x{structure.image_height}")
            print(f"  - Zonas: {len(structure.zones)}")
            print(f"  - Tabulas: {len(structure.tables)}")
            print(f"  - Teksta bloki: {len(structure.text_blocks)}")
            print(f"  - Confidence: {structure.confidence:.2f}")
            print(f"  - Apstrādes laiks: {structure.processing_time_ms}ms")
            
        finally:
            # Izdzēst temporary failu
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_merge_parallel_lines(self, analyzer):
        """Testa paralēlo līniju apvienošanu"""
        # Horizontālas līnijas ar nedaudz atšķirīgām Y koordinātām
        lines = [
            [10, 100, 200, 100],  # Tieša horizontāla līnija
            [15, 102, 195, 103],  # Nedaudz novirzīta
            [12, 99, 198, 101],   # Vēl nedaudz novirzīta
            [20, 150, 180, 151]   # Cita līnija tālāk
        ]
        
        merged = analyzer._merge_parallel_lines(lines, True)
        
        # Jāapvieno pirmās 3 līnijas, 4. jāpaliek atsevišķi
        assert len(merged) == 2, f"Sagaidītas 2 apvienotas līnijas, bet ir {len(merged)}"
        print("✅ Paralēlo līniju apvienošana darbojas korekti")
    
    def test_bbox_overlap_calculation(self, analyzer):
        """Testa bounding box pārklāšanās aprēķinu"""
        bbox1 = BoundingBox(10, 10, 100, 100)
        bbox2 = BoundingBox(50, 50, 150, 150)  # 50% pārklāšanās
        bbox3 = BoundingBox(200, 200, 300, 300)  # Nav pārklāšanās
        
        overlap1 = analyzer._calculate_bbox_overlap(bbox1, bbox2)
        overlap2 = analyzer._calculate_bbox_overlap(bbox1, bbox3)
        
        assert 0 < overlap1 < 1, f"Pārklāšanās starp bbox1 un bbox2: {overlap1}"
        assert overlap2 == 0, f"Nav pārklāšanās starp bbox1 un bbox3: {overlap2}"
        
        print(f"✅ BBox overlap aprēķins: {overlap1:.2f} un {overlap2:.2f}")
    
    def test_table_quality_filtering(self, analyzer):
        """Testa tabulu kvalitātes filtrēšanu"""
        # Izveidot tabulas ar dažādām kvalitātēm
        good_table = TableRegion(
            bounds=BoundingBox(10, 10, 200, 100),
            cells=[],
            confidence=0.8
        )
        
        too_small_table = TableRegion(
            bounds=BoundingBox(10, 10, 30, 20),  # Pārāk maza
            cells=[],
            confidence=0.9
        )
        
        low_confidence_table = TableRegion(
            bounds=BoundingBox(10, 10, 150, 80),
            cells=[],
            confidence=0.2  # Pārāk zema confidence
        )
        
        tables = [good_table, too_small_table, low_confidence_table]
        image_shape = (600, 800, 3)  # Height, Width, Channels
        
        filtered = analyzer._filter_table_quality(tables, image_shape)
        
        assert len(filtered) == 1, f"Jāpaliek tikai 1 tabula, bet ir {len(filtered)}"
        assert filtered[0] == good_table, "Jāpaliek tikai labai tabulai"
        
        print("✅ Tabulu kvalitātes filtrēšana darbojas korekti")


class TestInvoiceModelIntegration:
    """Testi Invoice modeļa integrācijai ar struktūras analīzi"""
    
    def test_invoice_structure_fields(self):
        """Testa vai Invoice modelim ir nepieciešamie struktūras lauki"""
        # Pārbaudīt ka Invoice klases definīcijā ir jaunie lauki
        from sqlalchemy import inspect
        
        # Simulēt Invoice objektu bez datubāzes
        invoice_attrs = dir(Invoice)
        
        required_fields = [
            'document_structure',
            'detected_zones', 
            'table_regions',
            'structure_confidence',
            'has_structure_analysis',
            'structure_analyzed_at'
        ]
        
        for field in required_fields:
            assert field in invoice_attrs, f"Invoice modelim trūkst lauka: {field}"
        
        print("✅ Invoice modelis satur visus nepieciešamos struktūras laukus")
    
    def test_structure_json_serialization(self):
        """Testa struktūras objektu JSON serializāciju"""
        # Izveidot struktūras objektu
        zone = DocumentZone("header", BoundingBox(0, 0, 100, 50), 0.9)
        table = TableRegion(BoundingBox(0, 50, 100, 150), [], [], 0.8)
        
        structure = DocumentStructure(
            image_width=800,
            image_height=600,
            zones=[zone],
            tables=[table], 
            text_blocks=[],
            confidence=0.85,
            processing_time_ms=120
        )
        
        # Konvertēt uz dict (simulē JSON serializāciju)
        try:
            structure_dict = {
                'image_width': structure.image_width,
                'image_height': structure.image_height,
                'zones': [
                    {
                        'type': z.type,
                        'bounds': {
                            'x1': z.bounds.x1, 'y1': z.bounds.y1,
                            'x2': z.bounds.x2, 'y2': z.bounds.y2
                        },
                        'confidence': z.confidence
                    } for z in structure.zones
                ],
                'tables': [
                    {
                        'bounds': {
                            'x1': t.bounds.x1, 'y1': t.bounds.y1, 
                            'x2': t.bounds.x2, 'y2': t.bounds.y2
                        },
                        'confidence': t.confidence,
                        'cell_count': len(t.cells)
                    } for t in structure.tables
                ],
                'confidence': structure.confidence,
                'processing_time_ms': structure.processing_time_ms
            }
            
            # Pārbaudīt JSON serializāciju
            json_str = json.dumps(structure_dict)
            parsed = json.loads(json_str)
            
            assert parsed['confidence'] == 0.85
            assert len(parsed['zones']) == 1
            assert len(parsed['tables']) == 1
            
            print("✅ Struktūras objektu JSON serializācija darbojas korekti")
            
        except Exception as e:
            pytest.fail(f"JSON serializācijas kļūda: {e}")


def run_all_tests():
    """Palaistīt visus testus"""
    print("🔍 Sākam POSM 4.5 Document Structure Analysis testus...")
    print("=" * 60)
    
    # Test objektu imports
    test_objects = TestDocumentStructureObjects()
    test_objects.test_bounding_box_creation()
    test_objects.test_table_cell_creation()
    test_objects.test_table_region_creation()
    test_objects.test_document_zone_creation()
    test_objects.test_document_structure_creation()
    
    print("\n📋 Objektu testi pabeigti")
    print("=" * 60)
    
    # Test analyzer functionality
    analyzer = DocumentStructureAnalyzer()
    test_analyzer = TestDocumentStructureAnalyzer()
    
    # Izveidot test image bez fixture izmantošanas
    def create_test_image():
        """Izveido testa attēlu"""
        # Izveido vienkāršu testa attēlu ar tabulas struktūru
        image = np.ones((600, 800, 3), dtype=np.uint8) * 255  # Balts fons
        
        # Pievienot horizontālās līnijas (tabulas rindas)
        cv2.line(image, (50, 100), (750, 100), (0, 0, 0), 2)  # Header līnija
        cv2.line(image, (50, 150), (750, 150), (0, 0, 0), 1)  # Rindu līnijas
        cv2.line(image, (50, 200), (750, 200), (0, 0, 0), 1)
        cv2.line(image, (50, 250), (750, 250), (0, 0, 0), 1)
        
        # Pievienot vertikālās līnijas (tabulas kolonnas)
        cv2.line(image, (50, 100), (50, 250), (0, 0, 0), 2)   # Kreisā mala
        cv2.line(image, (200, 100), (200, 250), (0, 0, 0), 1) # Kolonna 1
        cv2.line(image, (400, 100), (400, 250), (0, 0, 0), 1) # Kolonna 2
        cv2.line(image, (600, 100), (600, 250), (0, 0, 0), 1) # Kolonna 3
        cv2.line(image, (750, 100), (750, 250), (0, 0, 0), 2) # Labā mala
        
        # Pievienot tekstu simulācijai
        cv2.putText(image, "Invoice Header", (300, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image, "Product", (75, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        cv2.putText(image, "Quantity", (220, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        cv2.putText(image, "Price", (450, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        cv2.putText(image, "Total", (650, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        
        return image
    
    test_image = create_test_image()
    
    # Sync testi
    test_analyzer.test_analyzer_initialization(analyzer)
    test_analyzer.test_merge_parallel_lines(analyzer)
    test_analyzer.test_bbox_overlap_calculation(analyzer)
    test_analyzer.test_table_quality_filtering(analyzer)
    
    print("\n🔧 Sync funkcionalitātes testi pabeigti")
    print("=" * 60)
    
    # Async testi
    async def run_async_tests():
        await test_analyzer.test_zone_detection(analyzer, test_image)
        await test_analyzer.test_table_detection_morphological(analyzer, test_image)
        await test_analyzer.test_table_detection_hough(analyzer, test_image)
        await test_analyzer.test_full_document_analysis(analyzer, test_image)
    
    # Palaist async testus
    asyncio.run(run_async_tests())
    
    print("\n⚡ Async funkcionalitātes testi pabeigti")
    print("=" * 60)
    
    # Test integration
    test_integration = TestInvoiceModelIntegration()
    test_integration.test_invoice_structure_fields()
    test_integration.test_structure_json_serialization()
    
    print("\n🔗 Integrācijas testi pabeigti")
    print("=" * 60)
    
    print("\n🎉 Visi POSM 4.5 Document Structure Analysis testi veiksmīgi!")
    print("✅ Imports: OK")
    print("✅ Objektu funkcionalitāte: OK") 
    print("✅ Servisa funkcionalitāte: OK")
    print("✅ Async operācijas: OK")
    print("✅ Invoice integrācija: OK")
    print("✅ JSON serializācija: OK")


if __name__ == "__main__":
    run_all_tests()
