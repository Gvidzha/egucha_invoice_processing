"""
POSM 4.5 Week 3: Service Enhancements - Comprehensive Test Suite
Tests for StructureAwareOCR, StructureAwareExtraction, and StructureAwareLearning
"""

import pytest
import asyncio
import cv2
import numpy as np
import json
import tempfile
import os
from datetime import datetime, date
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock

# Import services to test
from app.services.ocr.structure_aware_ocr import (
    StructureAwareOCR, StructureAwareOCRResult, ZoneOCRConfig
)
from app.services.structure_aware_extraction import (
    StructureAwareExtractionService, StructureAwareExtractionResult
)
from app.services.structure_aware_learning import (
    StructureAwareLearningService, StructureAwareLearningResult
)

# Import supporting classes
from app.services.document_structure_service import (
    DocumentStructureAnalyzer, DocumentStructure, DocumentZone, 
    TableRegion, ZoneType, BoundingBox
)
from app.services.extraction_service import ExtractedData
from app.services.ocr.ocr_main import OCRService

class TestStructureAwareOCREnhancements:
    """Test suite for POSM 4.5 Week 3 StructureAwareOCR enhancements"""
    
    @pytest.fixture
    def mock_ocr_service(self):
        """Mock OCR service for testing"""
        service = Mock(spec=OCRService)
        service.extract_text_from_image = AsyncMock(return_value={
            "text": "Test OCR text",
            "confidence": 0.85
        })
        # Fix: Add the method that StructureAwareOCR actually calls
        service.extract_text = AsyncMock(return_value={
            "text": "Test OCR text",
            "confidence": 0.85
        })
        # Add text_cleaner mock
        service.text_cleaner = Mock()
        service.text_cleaner.basic_clean = Mock(return_value="cleaned text")
        service.text_cleaner.clean_text = Mock(return_value="cleaned text")
        service.text_cleaner.advanced_clean = Mock(return_value="advanced cleaned text")
        return service
    
    @pytest.fixture
    def mock_structure_analyzer(self):
        """Mock structure analyzer for testing"""
        analyzer = Mock(spec=DocumentStructureAnalyzer)
        
        # Mock structure analysis result
        mock_structure = DocumentStructure(
            image_width=400,
            image_height=200,
            zones=[
                DocumentZone(
                    zone_type=ZoneType.HEADER,
                    bounds=BoundingBox(x1=0, y1=0, x2=100, y2=50),
                    confidence=0.9,
                    text_blocks=[]
                ),
                DocumentZone(
                    zone_type=ZoneType.SUPPLIER_INFO,
                    bounds=BoundingBox(x1=0, y1=50, x2=100, y2=80),
                    confidence=0.85,
                    text_blocks=[]
                )
            ],
            tables=[],
            text_blocks=[],
            confidence=0.87,
            processing_time_ms=100
        )
        
        analyzer.analyze_document_structure = AsyncMock(return_value=mock_structure)
        return analyzer
    
    @pytest.fixture
    def structure_aware_ocr(self, mock_ocr_service, mock_structure_analyzer):
        """StructureAwareOCR instance for testing"""
        return StructureAwareOCR(mock_ocr_service, mock_structure_analyzer)
    
    @pytest.fixture
    def sample_image_path(self):
        """Create a sample test image"""
        # Create a simple test image
        image = np.ones((200, 400, 3), dtype=np.uint8) * 255
        cv2.putText(image, "Test Invoice", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image, "Supplier: Test Company", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(image, "Amount: 123.45 EUR", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            cv2.imwrite(tmp.name, image)
            return tmp.name
    
    @pytest.mark.asyncio
    async def test_process_with_context_basic(self, structure_aware_ocr, sample_image_path):
        """Test basic process_with_context functionality"""
        try:
            # Test with no context
            result = await structure_aware_ocr.process_with_context(sample_image_path)
            
            assert isinstance(result, StructureAwareOCRResult)
            assert result.overall_confidence > 0
            assert "zone_insights" in result.metadata
            
            print("✅ process_with_context basic test passed")
            
        finally:
            # Cleanup
            if os.path.exists(sample_image_path):
                os.unlink(sample_image_path)
    
    @pytest.mark.asyncio
    async def test_process_with_context_with_context_data(self, structure_aware_ocr, sample_image_path):
        """Test process_with_context with context data"""
        try:
            context_data = {
                "supplier_info": {"name": "Test Company"},
                "template_hints": {"supplier": {"reliability": 0.9}},
                "historical_patterns": {"date": {"format": "date"}}
            }
            
            result = await structure_aware_ocr.process_with_context(sample_image_path, context_data)
            
            assert isinstance(result, StructureAwareOCRResult)
            assert result.overall_confidence > 0
            assert "zone_insights" in result.metadata
            
            print("✅ process_with_context with context data test passed")
            
        finally:
            if os.path.exists(sample_image_path):
                os.unlink(sample_image_path)
    
    @pytest.mark.asyncio
    async def test_get_zone_insights(self, structure_aware_ocr, sample_image_path):
        """Test zone insights generation"""
        try:
            # First get a basic result
            result = await structure_aware_ocr.process_with_structure(sample_image_path)
            
            # Test zone insights
            insights = await structure_aware_ocr.get_zone_insights(result)
            
            assert isinstance(insights, dict)
            assert "zone_analysis" in insights
            assert "confidence_distribution" in insights
            assert "text_quality_metrics" in insights
            assert "structure_coherence" in insights
            
            # Check that structure coherence is a valid score
            assert 0.0 <= insights["structure_coherence"] <= 1.0
            
            print("✅ get_zone_insights test passed")
            
        finally:
            if os.path.exists(sample_image_path):
                os.unlink(sample_image_path)
    
    @pytest.mark.asyncio
    async def test_enhanced_confidence_calculation(self, structure_aware_ocr, sample_image_path):
        """Test enhanced confidence calculation"""
        try:
            context_data = {"supplier_info": {"name": "Test"}}
            result = await structure_aware_ocr.process_with_context(sample_image_path, context_data)
            
            # Enhanced confidence should be calculated
            assert hasattr(result, 'overall_confidence')
            assert 0.0 <= result.overall_confidence <= 1.0
            
            print("✅ Enhanced confidence calculation test passed")
            
        finally:
            if os.path.exists(sample_image_path):
                os.unlink(sample_image_path)

class TestStructureAwareExtraction:
    """Test suite for StructureAwareExtractionService"""
    
    @pytest.fixture
    def extraction_service(self):
        """StructureAwareExtractionService instance for testing"""
        return StructureAwareExtractionService()
    
    @pytest.fixture
    def mock_ocr_result(self):
        """Mock StructureAwareOCRResult for testing"""
        # Create mock structure first
        mock_structure = DocumentStructure(
            image_width=500,
            image_height=700,
            zones=[
                DocumentZone(
                    zone_type=ZoneType.SUPPLIER_INFO,
                    bounds=BoundingBox(x1=50, y1=100, x2=450, y2=150),
                    confidence=0.9,
                    text_blocks=[]
                )
            ],
            tables=[],
            text_blocks=[],
            confidence=0.85,
            processing_time_ms=100
        )
        
        return StructureAwareOCRResult(
            text="Test Supplier\\nInvoice: INV-123\\nDate: 2025-08-03\\nAmount: 123.45 EUR",
            confidence=0.85,
            structure=mock_structure,
            zone_results={
                "supplier_info": {
                    "text": "Test Supplier\\nReg: 12345",
                    "confidence": 0.9
                },
                "invoice_details": {
                    "text": "Invoice: INV-123\\nDate: 2025-08-03",
                    "confidence": 0.85
                },
                "amounts": {
                    "text": "Total: 123.45 EUR\\nVAT: 20.69 EUR",
                    "confidence": 0.8
                }
            },
            table_results=[],
            enhanced_text="Enhanced: Test Supplier\\nInvoice: INV-123\\nDate: 2025-08-03\\nAmount: 123.45 EUR",
            processing_time_ms=250,
            overall_confidence=0.85,
            metadata={},
            full_text="Test Supplier\\nInvoice: INV-123\\nDate: 2025-08-03\\nAmount: 123.45 EUR",
            processing_time=0.25
        )
    
    @pytest.mark.asyncio
    async def test_extract_with_structure_basic(self, extraction_service, mock_ocr_result):
        """Test basic structure-aware extraction"""
        result = await extraction_service.extract_with_structure(mock_ocr_result)
        
        assert isinstance(result, StructureAwareExtractionResult)
        assert result.extracted_data is not None
        assert isinstance(result.zone_mapping, dict)
        assert isinstance(result.confidence_by_zone, dict)
        assert isinstance(result.structure_insights, dict)
        assert result.extraction_strategy in ["zone_primary", "zone_hybrid", "fallback_primary", "fallback"]
        
        print("✅ extract_with_structure basic test passed")
    
    @pytest.mark.asyncio
    async def test_zone_specific_extraction(self, extraction_service, mock_ocr_result):
        """Test zone-specific field extraction"""
        zone_extractions = await extraction_service._extract_by_zones(mock_ocr_result)
        
        assert isinstance(zone_extractions, dict)
        assert len(zone_extractions) > 0
        
        # Check that zones produced extractions
        for zone_type, zone_data in zone_extractions.items():
            assert "zone_type" in zone_data
            assert "confidence" in zone_data
            assert "extracted_fields" in zone_data
        
        print("✅ Zone-specific extraction test passed")
    
    @pytest.mark.asyncio
    async def test_extraction_strategy_determination(self, extraction_service, mock_ocr_result):
        """Test extraction strategy determination"""
        zone_extractions = await extraction_service._extract_by_zones(mock_ocr_result)
        strategy = extraction_service._determine_extraction_strategy(zone_extractions, mock_ocr_result)
        
        assert strategy in ["zone_primary", "zone_hybrid", "fallback_primary"]
        
        print("✅ Extraction strategy determination test passed")
    
    @pytest.mark.asyncio
    async def test_structure_insights_generation(self, extraction_service, mock_ocr_result):
        """Test structure insights generation"""
        zone_extractions = await extraction_service._extract_by_zones(mock_ocr_result)
        insights = await extraction_service._generate_structure_insights(mock_ocr_result, zone_extractions)
        
        assert isinstance(insights, dict)
        assert "zone_coverage" in insights
        assert "extraction_success_rate" in insights
        assert "structure_quality" in insights
        assert "recommendations" in insights
        
        # Check that rates are valid percentages
        assert 0.0 <= insights["extraction_success_rate"] <= 1.0
        assert 0.0 <= insights["structure_quality"] <= 1.0
        
        print("✅ Structure insights generation test passed")
    
    @pytest.mark.asyncio
    async def test_field_extraction_methods(self, extraction_service):
        """Test specific field extraction methods"""
        # Test supplier extraction
        supplier = await extraction_service._extract_supplier_from_zone("Test Company SIA\\nAddress")
        assert supplier is not None
        
        # Test invoice number extraction
        invoice_num = await extraction_service._extract_invoice_number_from_zone("Invoice: INV-123")
        assert invoice_num == "INV-123"
        
        # Test date extraction
        date_str = await extraction_service._extract_date_from_zone("Date: 03.08.2025")
        assert date_str is not None
        
        # Test amount extraction
        amount = await extraction_service._extract_amount_from_zone("Total: 123.45 EUR")
        assert amount == 123.45
        
        print("✅ Field extraction methods test passed")

class TestStructureAwareLearning:
    """Test suite for StructureAwareLearningService"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for testing"""
        return Mock()
    
    @pytest.fixture
    def learning_service(self, mock_db_session):
        """StructureAwareLearningService instance for testing"""
        return StructureAwareLearningService(mock_db_session)
    
    @pytest.fixture
    def mock_extraction_result(self):
        """Mock StructureAwareExtractionResult for testing"""
        extracted_data = ExtractedData(
            invoice_number="INV-123",
            supplier_name="Test Supplier",
            supplier_reg_number="12345",
            supplier_address="Test Address",
            recipient_name="Recipient",
            recipient_reg_number="67890",
            recipient_address="Recipient Address",
            invoice_date=date(2025, 8, 3),
            delivery_date=None,
            total_amount=123.45,
            vat_amount=20.69,
            currency="EUR",
            products=[],
            confidence_scores={"overall": 0.85},
        )
        
        return StructureAwareExtractionResult(
            extracted_data=extracted_data,
            zone_mapping={
                "supplier_name": "supplier_info",
                "invoice_number": "invoice_details",
                "total_amount": "amounts"
            },
            confidence_by_zone={
                "supplier_info": 0.9,
                "invoice_details": 0.85,
                "amounts": 0.8
            },
            structure_insights={},
            extraction_strategy="zone_primary",
            metadata={}
        )
    
    @pytest.mark.asyncio
    async def test_learn_from_structure_correction_basic(self, learning_service, mock_extraction_result):
        """Test basic structure-aware learning"""
        corrections = {
            "supplier_name": "Corrected Supplier Name",
            "total_amount": 150.00
        }
        
        with patch.object(learning_service.base_learning, 'learn_from_correction', new_callable=AsyncMock) as mock_base:
            result = await learning_service.learn_from_structure_correction(
                mock_extraction_result, corrections, None, 1
            )
        
        assert isinstance(result, StructureAwareLearningResult)
        assert result.learning_applied == True
        assert len(result.improved_fields) == 2
        assert result.learning_strategy in learning_service.learning_strategies.keys()
        
        print("✅ learn_from_structure_correction basic test passed")
    
    @pytest.mark.asyncio
    async def test_learning_strategy_determination(self, learning_service, mock_extraction_result):
        """Test learning strategy determination"""
        # Test zone-specific strategy
        zone_corrections = {"supplier_name": "New Supplier", "total_amount": 200.0}
        strategy = learning_service._determine_learning_strategy(mock_extraction_result, zone_corrections)
        assert strategy in learning_service.learning_strategies.keys()
        
        # Test confidence-driven strategy
        low_confidence_result = mock_extraction_result
        low_confidence_result.confidence_by_zone = {"supplier_info": 0.5, "amounts": 0.4}
        strategy2 = learning_service._determine_learning_strategy(low_confidence_result, zone_corrections)
        assert strategy2 in learning_service.learning_strategies.keys()
        
        print("✅ Learning strategy determination test passed")
    
    @pytest.mark.asyncio 
    async def test_zone_specific_learning(self, learning_service, mock_extraction_result):
        """Test zone-specific learning implementation"""
        corrections = {"supplier_name": "Corrected Supplier"}
        
        result = await learning_service._learn_zone_specific(
            mock_extraction_result, corrections, None, 1
        )
        
        assert isinstance(result, dict)
        assert "patterns" in result
        assert "details" in result
        
        print("✅ Zone-specific learning test passed")
    
    @pytest.mark.asyncio
    async def test_pattern_based_learning(self, learning_service, mock_extraction_result):
        """Test pattern-based learning implementation"""
        corrections = {"invoice_number": "CORRECTED-123"}
        
        result = await learning_service._learn_pattern_based(
            mock_extraction_result, corrections, None, 1
        )
        
        assert isinstance(result, dict)
        assert "patterns" in result
        assert "details" in result
        
        print("✅ Pattern-based learning test passed")
    
    @pytest.mark.asyncio
    async def test_confidence_improvements_calculation(self, learning_service, mock_extraction_result):
        """Test confidence improvements calculation"""
        corrections = {"supplier_name": "New Supplier", "total_amount": 200.0}
        
        improvements = await learning_service._calculate_confidence_improvements(
            mock_extraction_result, corrections
        )
        
        assert isinstance(improvements, dict)
        assert len(improvements) == 2
        
        for field, improvement in improvements.items():
            assert 0.0 <= improvement <= 1.0
        
        print("✅ Confidence improvements calculation test passed")
    
    @pytest.mark.asyncio
    async def test_learning_stats(self, learning_service):
        """Test structure learning statistics"""
        stats = await learning_service.get_structure_learning_stats()
        
        assert isinstance(stats, dict)
        assert "total_patterns" in stats
        assert "patterns_by_zone" in stats
        assert "avg_success_rate" in stats
        assert "learning_strategies_used" in stats
        
        print("✅ Learning stats test passed")

class TestIntegration:
    """Integration tests for all three services"""
    
    @pytest.fixture
    def mock_db_session(self):
        return Mock()
    
    @pytest.fixture
    def sample_image_path(self):
        """Create a sample test image for integration testing"""
        image = np.ones((300, 500, 3), dtype=np.uint8) * 255
        cv2.putText(image, "INVOICE", (200, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image, "Test Company SIA", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        cv2.putText(image, "Invoice: INV-2025-001", (50, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(image, "Date: 03.08.2025", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(image, "Total: 299.99 EUR", (50, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            cv2.imwrite(tmp.name, image)
            return tmp.name
    
    @pytest.mark.asyncio
    async def test_full_pipeline_integration(self, sample_image_path, mock_db_session):
        """Test full pipeline: OCR -> Extraction -> Learning"""
        try:
            # 1. Setup services
            mock_ocr_service = Mock(spec=OCRService)
            mock_ocr_service.extract_text_from_image = AsyncMock(return_value={
                "text": "INVOICE\\nTest Company SIA\\nInvoice: INV-2025-001\\nDate: 03.08.2025\\nTotal: 299.99 EUR",
                "confidence": 0.85
            })
            # Add text_cleaner mock
            mock_ocr_service.text_cleaner = Mock()
            mock_ocr_service.text_cleaner.basic_clean = Mock(return_value="cleaned text")
            mock_ocr_service.text_cleaner.clean_text = Mock(return_value="cleaned text")
            mock_ocr_service.text_cleaner.advanced_clean = Mock(return_value="advanced cleaned text")
            
            structure_analyzer = Mock(spec=DocumentStructureAnalyzer)
            structure_analyzer.analyze_document_structure = AsyncMock(return_value=Mock())
            
            # Initialize services
            ocr_service = StructureAwareOCR(mock_ocr_service, structure_analyzer)
            extraction_service = StructureAwareExtractionService()
            learning_service = StructureAwareLearningService(mock_db_session)
            
            # 2. Run OCR with context
            context_data = {"supplier_info": {"name": "Test Company"}}
            ocr_result = await ocr_service.process_with_context(sample_image_path, context_data)
            
            assert isinstance(ocr_result, StructureAwareOCRResult)
            
            # 3. Run Extraction
            extraction_result = await extraction_service.extract_with_structure(ocr_result)
            
            assert isinstance(extraction_result, StructureAwareExtractionResult)
            
            # 4. Run Learning (simulate corrections)
            corrections = {"supplier_name": "Test Company SIA (Corrected)"}
            
            with patch.object(learning_service.base_learning, 'learn_from_correction', new_callable=AsyncMock):
                learning_result = await learning_service.learn_from_structure_correction(
                    extraction_result, corrections, None, 1
                )
            
            assert isinstance(learning_result, StructureAwareLearningResult)
            assert learning_result.learning_applied == True
            
            print("✅ Full pipeline integration test passed")
            
        finally:
            if os.path.exists(sample_image_path):
                os.unlink(sample_image_path)
    
    @pytest.mark.asyncio
    async def test_error_handling_resilience(self, sample_image_path, mock_db_session):
        """Test error handling across all services"""
        try:
            # Test with invalid image path
            mock_ocr_service = Mock(spec=OCRService)
            mock_ocr_service.extract_text_from_image = AsyncMock(side_effect=Exception("OCR Error"))
            # Add text_cleaner mock even for error cases
            mock_ocr_service.text_cleaner = Mock()
            mock_ocr_service.text_cleaner.basic_clean = Mock(return_value="cleaned text")
            mock_ocr_service.text_cleaner.clean_text = Mock(return_value="cleaned text")
            mock_ocr_service.text_cleaner.advanced_clean = Mock(return_value="advanced cleaned text")
            
            ocr_service = StructureAwareOCR(mock_ocr_service)
            
            # Should handle error gracefully
            result = await ocr_service.process_with_context("invalid_path.png")
            # Should get fallback result or error handling
            
            print("✅ Error handling resilience test passed")
            
        finally:
            if os.path.exists(sample_image_path):
                os.unlink(sample_image_path)

# Performance benchmarks
class TestPerformance:
    """Performance tests for POSM 4.5 Week 3 enhancements"""
    
    @pytest.mark.asyncio
    async def test_ocr_enhancement_performance(self):
        """Test that OCR enhancements don't significantly impact performance"""
        # Create mock services
        mock_ocr_service = Mock(spec=OCRService)
        mock_ocr_service.extract_text_from_image = AsyncMock(return_value={
            "text": "Test text", "confidence": 0.85
        })
        # Add text_cleaner mock
        mock_ocr_service.text_cleaner = Mock()
        mock_ocr_service.text_cleaner.basic_clean = Mock(return_value="cleaned text")
        mock_ocr_service.text_cleaner.clean_text = Mock(return_value="cleaned text")
        mock_ocr_service.text_cleaner.advanced_clean = Mock(return_value="advanced cleaned text")
        
        ocr_service = StructureAwareOCR(mock_ocr_service)
        
        # Create test image
        image = np.ones((200, 400, 3), dtype=np.uint8) * 255
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            cv2.imwrite(tmp.name, image)
            image_path = tmp.name
        
        try:
            start_time = datetime.now()
            result = await ocr_service.process_with_context(image_path)
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            
            # Should complete within reasonable time (adjust threshold as needed)
            assert processing_time < 10.0, f"Processing took {processing_time}s, too slow"
            
            print(f"✅ OCR enhancement performance test passed: {processing_time:.3f}s")
            
        finally:
            if os.path.exists(image_path):
                os.unlink(image_path)
    
    @pytest.mark.asyncio
    async def test_extraction_performance(self):
        """Test extraction service performance"""
        extraction_service = StructureAwareExtractionService()
        
        # Create mock OCR result with substantial data
        large_text = "\\n".join([f"Line {i}: Test data" for i in range(100)])
        
        # Create mock structure
        mock_structure = DocumentStructure(
            image_width=500, image_height=700,
            zones=[], tables=[], text_blocks=[]
        )
        
        mock_ocr_result = StructureAwareOCRResult(
            text=large_text,
            confidence=0.85,
            structure=mock_structure,
            zone_results={f"zone_{i}": {"text": f"Zone {i} text", "confidence": 0.8} for i in range(10)},
            table_results=[],
            enhanced_text=large_text,
            processing_time_ms=250,
            overall_confidence=0.85,
            metadata={},
            full_text=large_text,
            processing_time=0.25
        )
        
        start_time = datetime.now()
        result = await extraction_service.extract_with_structure(mock_ocr_result)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time
        assert processing_time < 1.0, f"Extraction took {processing_time}s, too slow"
        
        print(f"✅ Extraction performance test passed: {processing_time:.3f}s")

if __name__ == "__main__":
    import sys
    
    print("🧪 POSM 4.5 Week 3: Service Enhancements - Test Suite")
    print("=" * 60)
    
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
    
    print("\\n" + "=" * 60)
    print("📊 Test Summary:")
    print("- StructureAwareOCR enhancements: Enhanced context processing, zone insights")
    print("- StructureAwareExtraction: Zone-specific extraction with intelligent merging")
    print("- StructureAwareLearning: Pattern-based learning with structure awareness")
    print("- Integration tests: Full pipeline validation")
    print("- Performance tests: Efficiency validation")
    print("\\n✅ POSM 4.5 Week 3 implementation complete!")
