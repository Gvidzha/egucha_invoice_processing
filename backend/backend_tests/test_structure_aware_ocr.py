"""
Tests for StructureAware OCR - POSM 4.5 Week 3
Testi zone-specific OCR optimization, table-aware extraction, confidence weighting
"""

import pytest
import asyncio
import tempfile
import json
import cv2
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.ocr.structure_aware_ocr import (
    StructureAwareOCR, StructureAwareOCRResult, ZoneOCRConfig
)
from app.services.ocr.ocr_main import OCRService
from app.services.document_structure_service import (
    DocumentStructureAnalyzer, DocumentStructure, DocumentZone, 
    TableRegion, BoundingBox, ZoneType
)

@pytest.fixture
def sample_image():
    """Izveido sample attēlu testiem"""
    # Izveido vienkāršu baltu attēlu ar melnu tekstu
    image = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # Pievieno tekstu dažādās zonās
    cv2.putText(image, "INVOICE HEADER", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(image, "Body content here", (50, 250), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(image, "Footer information", (50, 550), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Saglabā uz temp failu
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        cv2.imwrite(f.name, image)
        return f.name

@pytest.fixture
def mock_ocr_service():
    """Mock OCR service"""
    mock_service = Mock(spec=OCRService)
    mock_service.extract_text = AsyncMock(return_value={
        'text': 'Sample OCR text',
        'confidence': 0.85
    })
    mock_service.text_cleaner = Mock()
    mock_service.text_cleaner.basic_clean = Mock(return_value="cleaned text")
    mock_service.text_cleaner.clean_text = Mock(return_value="cleaned text")
    mock_service.text_cleaner.advanced_clean = Mock(return_value="advanced cleaned text")
    return mock_service

@pytest.fixture
def sample_document_structure():
    """Sample DocumentStructure priekš testiem"""
    zones = [
        DocumentZone(
            zone_type=ZoneType.HEADER,
            bounds=BoundingBox(0, 0, 800, 100),
            confidence=0.9
        ),
        DocumentZone(
            zone_type=ZoneType.BODY,
            bounds=BoundingBox(0, 100, 800, 500),
            confidence=0.85
        ),
        DocumentZone(
            zone_type=ZoneType.FOOTER,
            bounds=BoundingBox(0, 500, 800, 600),
            confidence=0.8
        )
    ]
    
    tables = [
        TableRegion(
            bounds=BoundingBox(100, 200, 700, 400),
            rows=3,
            columns=4,
            confidence=0.88,
            cells=[]
        )
    ]
    
    return DocumentStructure(
        image_width=800,
        image_height=600,
        zones=zones,
        tables=tables,
        text_blocks=[BoundingBox(50, 50, 750, 550)]
    )

@pytest.fixture
def structure_aware_ocr(mock_ocr_service):
    """StructureAwareOCR instance ar mock servisu"""
    return StructureAwareOCR(mock_ocr_service)

class TestStructureAwareOCR:
    """Test klase priekš StructureAwareOCR"""
    
    def test_initialization(self, mock_ocr_service):
        """Testē inicializāciju"""
        ocr = StructureAwareOCR(mock_ocr_service)
        
        assert ocr.ocr_service == mock_ocr_service
        assert isinstance(ocr.structure_analyzer, DocumentStructureAnalyzer)
        assert len(ocr.zone_configs) == 5  # Visiem ZoneType
        assert ZoneType.HEADER in ocr.zone_configs
        assert ZoneType.TABLE in ocr.zone_configs
    
    def test_zone_configurations(self, structure_aware_ocr):
        """Testē zone-specific konfigurācijas"""
        # Header config
        header_config = structure_aware_ocr.zone_configs[ZoneType.HEADER]
        assert header_config.confidence_threshold == 0.7
        assert "deskew" in header_config.preprocessing_steps
        assert header_config.text_cleaning_level == "medium"
        
        # Table config
        table_config = structure_aware_ocr.zone_configs[ZoneType.TABLE]
        assert table_config.confidence_threshold == 0.75
        assert "morphology" in table_config.preprocessing_steps
        
        # Summary config
        summary_config = structure_aware_ocr.zone_configs[ZoneType.SUMMARY]
        assert summary_config.confidence_threshold == 0.8
        assert summary_config.text_cleaning_level == "aggressive"
    
    def test_confidence_weights(self, structure_aware_ocr):
        """Testē confidence weighting sistēmu"""
        weights = structure_aware_ocr.confidence_weights
        
        assert weights[ZoneType.HEADER] == 1.2  # Higher weight
        assert weights[ZoneType.TABLE] == 1.3   # Highest weight
        assert weights[ZoneType.BODY] == 1.0    # Standard weight
        assert weights[ZoneType.FOOTER] == 0.9  # Lower weight
    
    @pytest.mark.asyncio
    async def test_process_with_structure_success(self, structure_aware_ocr, sample_image, sample_document_structure):
        """Testē veiksmīgu structure-aware processing"""
        
        # Mock structure analyzer
        structure_aware_ocr.structure_analyzer.analyze_document = AsyncMock(
            return_value=sample_document_structure
        )
        
        # Mock zone processing
        async def mock_process_zone(image_path, zone):
            return {
                'text': f'Zone {zone.zone_type.value} text',
                'raw_text': f'Raw {zone.zone_type.value} text',
                'confidence': 0.8,
                'zone_type': zone.zone_type.value,
                'bounds': {'x1': zone.bounds.x1, 'y1': zone.bounds.y1, 
                          'x2': zone.bounds.x2, 'y2': zone.bounds.y2},
                'config_used': 'test_config'
            }
        
        structure_aware_ocr._process_zone_ocr = mock_process_zone
        
        # Mock table processing
        async def mock_process_table(image_path, table):
            return {
                'cells': [{'text': 'cell1', 'confidence': 0.9, 'row': 0, 'column': 0}],
                'matrix': [['cell1', 'cell2'], ['cell3', 'cell4']],
                'table_bounds': {'x1': table.bounds.x1, 'y1': table.bounds.y1,
                               'x2': table.bounds.x2, 'y2': table.bounds.y2},
                'rows': table.rows,
                'columns': table.columns,
                'confidence': table.confidence
            }
        
        structure_aware_ocr._process_table_ocr = mock_process_table
        
        # Test processing
        result = await structure_aware_ocr.process_with_structure(sample_image)
        
        # Assertions
        assert isinstance(result, StructureAwareOCRResult)
        assert result.text == 'Sample OCR text'  # From mock OCR service
        assert result.confidence > 0
        assert len(result.zone_results) == 3  # Header, Body, Footer
        assert len(result.table_results) == 1
        assert result.enhanced_text != ''
        assert result.processing_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_process_zone_ocr_header(self, structure_aware_ocr, sample_image):
        """Testē header zonas OCR apstrādi"""
        zone = DocumentZone(
            zone_type=ZoneType.HEADER,
            bounds=BoundingBox(0, 0, 800, 100),
            confidence=0.9
        )
        
        # Mock image reading
        with patch('cv2.imread') as mock_imread:
            mock_image = np.ones((100, 800, 3), dtype=np.uint8) * 255
            mock_imread.return_value = mock_image
            
            # Mock OCR extraction
            structure_aware_ocr._extract_text_from_zone = AsyncMock(return_value={
                'text': 'Header text',
                'confidence': 0.85
            })
            
            # Mock text cleaning
            structure_aware_ocr._clean_zone_text = AsyncMock(return_value='Cleaned header text')
            
            result = await structure_aware_ocr._process_zone_ocr(sample_image, zone)
            
            assert result['text'] == 'Cleaned header text'
            assert result['zone_type'] == 'header'
            assert result['confidence'] == 0.85
            assert 'bounds' in result
    
    @pytest.mark.asyncio
    async def test_process_table_ocr(self, structure_aware_ocr, sample_image):
        """Testē tabulas OCR apstrādi"""
        from app.services.document_structure_service import TableCell
        
        cells = [
            TableCell(bounds=BoundingBox(10, 10, 90, 40), row_index=0, column_index=0),
            TableCell(bounds=BoundingBox(100, 10, 190, 40), row_index=0, column_index=1),
            TableCell(bounds=BoundingBox(10, 50, 90, 80), row_index=1, column_index=0),
            TableCell(bounds=BoundingBox(100, 50, 190, 80), row_index=1, column_index=1)
        ]
        
        table = TableRegion(
            bounds=BoundingBox(100, 200, 700, 400),
            rows=2,
            columns=2,
            confidence=0.88,
            cells=cells
        )
        
        # Mock image reading
        with patch('cv2.imread') as mock_imread:
            mock_image = np.ones((400, 800, 3), dtype=np.uint8) * 255
            mock_imread.return_value = mock_image
            
            # Mock cell OCR
            structure_aware_ocr._extract_text_from_zone = AsyncMock(return_value={
                'text': 'Cell text',
                'confidence': 0.9
            })
            
            result = await structure_aware_ocr._process_table_ocr(sample_image, table)
            
            assert len(result['cells']) == 4
            assert result['matrix'] != []
            assert result['rows'] == 2
            assert result['columns'] == 2
    
    def test_calculate_weighted_confidence(self, structure_aware_ocr):
        """Testē weighted confidence aprēķinu"""
        zone_results = {
            'header': {'confidence': 0.9},
            'body': {'confidence': 0.8},
            'footer': {'confidence': 0.7}
        }
        
        table_results = [
            {'confidence': 0.85}
        ]
        
        weighted_confidence = structure_aware_ocr._calculate_weighted_confidence(
            base_confidence=0.75,
            zone_results=zone_results,
            table_results=table_results
        )
        
        assert 0.7 <= weighted_confidence <= 1.0
        assert weighted_confidence > 0.75  # Should be higher than base
    
    def test_create_enhanced_text(self, structure_aware_ocr, sample_document_structure):
        """Testē enhanced text izveidošanu"""
        zone_results = {
            'header': {'text': 'Header text'},
            'body': {'text': 'Body content'},
            'footer': {'text': 'Footer info'}
        }
        
        table_results = [
            {
                'matrix': [
                    ['Product', 'Quantity', 'Price'],
                    ['Item 1', '2', '10.00'],
                    ['Item 2', '1', '15.00']
                ]
            }
        ]
        
        enhanced_text = structure_aware_ocr._create_enhanced_text(
            base_text="Original text",
            zone_results=zone_results,
            table_results=table_results,
            structure=sample_document_structure
        )
        
        assert '[HEADER]' in enhanced_text
        assert '[BODY]' in enhanced_text
        assert '[FOOTER]' in enhanced_text
        assert '[TABLE_1]' in enhanced_text
        assert 'Product | Quantity | Price' in enhanced_text
    
    @pytest.mark.asyncio
    async def test_preprocess_zone_image(self, structure_aware_ocr):
        """Testē zone image preprocessing"""
        test_image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        steps = ["deskew", "denoise", "enhance_contrast"]
        
        with patch.object(structure_aware_ocr, '_deskew_image', return_value=test_image):
            with patch('cv2.fastNlMeansDenoisingColored', return_value=test_image):
                with patch.object(structure_aware_ocr, '_enhance_contrast', return_value=test_image):
                    result = await structure_aware_ocr._preprocess_zone_image(test_image, steps)
                    
                    assert result.shape == test_image.shape
    
    def test_deskew_image(self, structure_aware_ocr):
        """Testē attēla deskewing"""
        # Izveido test attēlu ar līnijām
        test_image = np.ones((200, 200, 3), dtype=np.uint8) * 255
        cv2.line(test_image, (10, 50), (190, 60), (0, 0, 0), 2)  # Slightly skewed line
        
        result = structure_aware_ocr._deskew_image(test_image)
        
        assert result.shape == test_image.shape
        assert isinstance(result, np.ndarray)
    
    def test_enhance_contrast(self, structure_aware_ocr):
        """Testē kontrasta uzlabošanu"""
        test_image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        result = structure_aware_ocr._enhance_contrast(test_image)
        
        assert result.shape == test_image.shape
        assert isinstance(result, np.ndarray)
    
    def test_apply_morphology(self, structure_aware_ocr):
        """Testē morphological operācijas"""
        test_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        
        result = structure_aware_ocr._apply_morphology(test_image)
        
        assert result.shape == test_image.shape
        assert isinstance(result, np.ndarray)
    
    @pytest.mark.asyncio
    async def test_clean_zone_text_levels(self, structure_aware_ocr):
        """Testē text cleaning dažādos līmeņos"""
        test_text = "  Dirty   text  with   noise  "
        
        # Test light cleaning
        light_result = await structure_aware_ocr._clean_zone_text(test_text, "light")
        assert isinstance(light_result, str)
        
        # Test medium cleaning
        medium_result = await structure_aware_ocr._clean_zone_text(test_text, "medium")
        assert isinstance(medium_result, str)
        
        # Test aggressive cleaning
        aggressive_result = await structure_aware_ocr._clean_zone_text(test_text, "aggressive")
        assert isinstance(aggressive_result, str)
    
    def test_build_table_matrix(self, structure_aware_ocr):
        """Testē tabulas matricas izveidošanu"""
        cell_results = [
            {'text': 'A1', 'row': 0, 'column': 0},
            {'text': 'B1', 'row': 0, 'column': 1},
            {'text': 'A2', 'row': 1, 'column': 0},
            {'text': 'B2', 'row': 1, 'column': 1}
        ]
        
        matrix = structure_aware_ocr._build_table_matrix(cell_results)
        
        assert len(matrix) == 2  # 2 rows
        assert len(matrix[0]) == 2  # 2 columns
        assert matrix[0][0] == 'A1'
        assert matrix[0][1] == 'B1'
        assert matrix[1][0] == 'A2'
        assert matrix[1][1] == 'B2'
    
    def test_build_table_matrix_empty(self, structure_aware_ocr):
        """Testē tukšu cell results"""
        matrix = structure_aware_ocr._build_table_matrix([])
        assert matrix == []
    
    @pytest.mark.asyncio
    async def test_error_handling_structure_analysis_fails(self, structure_aware_ocr, sample_image):
        """Testē error handling kad structure analysis fails"""
        
        # Mock structure analyzer to fail
        structure_aware_ocr.structure_analyzer.analyze_document = AsyncMock(
            side_effect=Exception("Structure analysis failed")
        )
        
        result = await structure_aware_ocr.process_with_structure(sample_image)
        
        # Should fallback to standard OCR
        assert isinstance(result, StructureAwareOCRResult)
        assert result.text == 'Sample OCR text'  # From mock
        assert len(result.zone_results) == 0
        assert len(result.table_results) == 0
    
    @pytest.mark.asyncio
    async def test_extract_text_from_zone_with_custom_config(self, structure_aware_ocr):
        """Testē OCR ar custom Tesseract config"""
        test_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        cv2.putText(test_image, "TEST", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        config = "--psm 6"
        threshold = 0.7
        
        with patch('pytesseract.image_to_string', return_value="TEST"):
            with patch('pytesseract.image_to_data', return_value={'conf': [80, 90, 85]}):
                result = await structure_aware_ocr._extract_text_from_zone(test_image, config, threshold)
                
                assert result['text'] == "TEST"
                assert 0 <= result['confidence'] <= 1

@pytest.mark.asyncio
async def test_structure_aware_ocr_result_creation():
    """Testē StructureAwareOCRResult objekta izveidošanu"""
    from app.services.document_structure_service import DocumentStructure
    
    structure = DocumentStructure(
        image_width=800,
        image_height=600,
        zones=[],
        tables=[],
        text_blocks=[]
    )
    
    result = StructureAwareOCRResult(
        text="Test text",
        confidence=0.85,
        structure=structure,
        zone_results={'header': {'text': 'Header'}},
        table_results=[],
        enhanced_text="Enhanced test text"
    )
    
    assert result.text == "Test text"
    assert result.confidence == 0.85
    assert result.enhanced_text == "Enhanced test text"
    assert result.created_at is not None
    assert isinstance(result.created_at, datetime)

def test_zone_ocr_config_creation():
    """Testē ZoneOCRConfig objekta izveidošanu"""
    config = ZoneOCRConfig(
        zone_type=ZoneType.HEADER,
        tesseract_config="--psm 6",
        preprocessing_steps=["deskew", "denoise"],
        confidence_threshold=0.8,
        text_cleaning_level="medium"
    )
    
    assert config.zone_type == ZoneType.HEADER
    assert config.tesseract_config == "--psm 6"
    assert "deskew" in config.preprocessing_steps
    assert config.confidence_threshold == 0.8
    assert config.text_cleaning_level == "medium"

# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_temp_files(sample_image):
    """Iztīra temp failus pēc testiem"""
    yield
    try:
        if Path(sample_image).exists():
            Path(sample_image).unlink()
    except:
        pass
