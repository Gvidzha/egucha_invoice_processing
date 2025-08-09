"""
Structure-Aware Extraction Service - POSM 4.5 Week 3
Papildu intelligent extraction ar document structure context
"""

import re
import asyncio
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
import json
import logging
from dataclasses import dataclass, asdict

from app.services.extraction_service import ExtractionService, ExtractedData
from app.services.document_structure_service import DocumentStructure, DocumentZone, ZoneType
from app.services.ocr.structure_aware_ocr import StructureAwareOCRResult

logger = logging.getLogger(__name__)

@dataclass
class StructureAwareExtractionResult:
    """Structure-aware extraction rezultāta konteiners"""
    extracted_data: ExtractedData
    zone_mapping: Dict[str, str]  # field -> zone_type mapping
    confidence_by_zone: Dict[str, float]
    structure_insights: Dict[str, Any]
    extraction_strategy: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertē uz dictionary"""
        result = asdict(self)
        # Convert ExtractedData
        if hasattr(self.extracted_data, '__dict__'):
            result['extracted_data'] = self.extracted_data.__dict__
        return result

class StructureAwareExtractionService:
    """
    Structure-Aware Extraction Service
    
    Capabilities:
    - Zone-specific extraction strategies
    - Structure-context-aware field mapping
    - Confidence weighting based on structure quality
    - Adaptive extraction patterns based on document type
    """
    
    def __init__(self):
        """Inicializē structure-aware extraction servisu"""
        self.base_extractor = ExtractionService()
        self.logger = logging.getLogger(__name__)
        
        # Zone-to-field mapping strategies
        self.zone_field_mapping = {
            ZoneType.HEADER: ["supplier_name", "invoice_number", "invoice_date"],
            ZoneType.SUPPLIER_INFO: ["supplier_name", "supplier_reg_number", "supplier_address"],
            ZoneType.RECIPIENT_INFO: ["recipient_name", "recipient_reg_number", "recipient_address"],
            ZoneType.INVOICE_DETAILS: ["invoice_number", "invoice_date", "delivery_date"],
            ZoneType.AMOUNTS: ["total_amount", "vat_amount", "currency"],
            ZoneType.TABLE: ["products"],
            ZoneType.FOOTER: ["supplier_bank_account", "recipient_bank_account"]
        }
        
        # Extraction confidence weights by zone type
        self.zone_confidence_weights = {
            ZoneType.SUPPLIER_INFO: 1.3,
            ZoneType.AMOUNTS: 1.4,
            ZoneType.INVOICE_DETAILS: 1.2,
            ZoneType.TABLE: 1.1,
            ZoneType.HEADER: 1.0,
            ZoneType.RECIPIENT_INFO: 0.9,
            ZoneType.FOOTER: 0.8
        }
    
    async def extract_with_structure(self, 
                                   ocr_result: StructureAwareOCRResult,
                                   document_structure: Optional[DocumentStructure] = None) -> StructureAwareExtractionResult:
        """
        Galvenā extraction metode ar structure awareness
        
        Args:
            ocr_result: StructureAwareOCRResult no OCR processing
            document_structure: Optional DocumentStructure instance
        
        Returns:
            StructureAwareExtractionResult: Enhanced extraction rezultāts
        """
        try:
            self.logger.info("🎯 Starting structure-aware extraction")
            
            # 1. Zone-specific extraction
            zone_extractions = await self._extract_by_zones(ocr_result)
            
            # 2. Fallback extraction no full text
            fallback_extraction = await self.base_extractor.extract_invoice_data(ocr_result.full_text)
            
            # 3. Intelligent merging
            merged_data = await self._merge_extractions(zone_extractions, fallback_extraction, ocr_result)
            
            # 4. Structure insights generation
            structure_insights = await self._generate_structure_insights(ocr_result, zone_extractions)
            
            # 5. Zone mapping analysis
            zone_mapping = self._analyze_zone_mapping(zone_extractions)
            
            # 6. Confidence calculation per zone
            confidence_by_zone = self._calculate_zone_confidences(zone_extractions, ocr_result)
            
            # 7. Determine extraction strategy
            extraction_strategy = self._determine_extraction_strategy(zone_extractions, ocr_result)
            
            result = StructureAwareExtractionResult(
                extracted_data=merged_data,
                zone_mapping=zone_mapping,
                confidence_by_zone=confidence_by_zone,
                structure_insights=structure_insights,
                extraction_strategy=extraction_strategy,
                metadata={
                    "processing_time": datetime.now().isoformat(),
                    "zone_count": len(zone_extractions),
                    "overall_confidence": merged_data.confidence if hasattr(merged_data, 'confidence') else 0.0
                }
            )
            
            self.logger.info(f"✅ Structure-aware extraction completed: strategy={extraction_strategy}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Structure-aware extraction failed: {e}")
            # Fallback to base extraction
            fallback_data = await self.base_extractor.extract_invoice_data(ocr_result.full_text)
            return StructureAwareExtractionResult(
                extracted_data=fallback_data,
                zone_mapping={},
                confidence_by_zone={},
                structure_insights={},
                extraction_strategy="fallback",
                metadata={"error": str(e)}
            )
    
    async def _extract_by_zones(self, ocr_result: StructureAwareOCRResult) -> Dict[str, Dict[str, Any]]:
        """Ekstraktē datus pa zonām"""
        zone_extractions = {}
        
        for zone_type, zone_data in ocr_result.zone_results.items():
            if isinstance(zone_data, dict) and "text" in zone_data:
                zone_text = zone_data["text"]
                zone_confidence = zone_data.get("confidence", 0.0)
                
                # Zone-specific extraction
                zone_extraction = await self._extract_from_zone(zone_type, zone_text, zone_confidence)
                if zone_extraction:
                    zone_extractions[zone_type] = zone_extraction
        
        return zone_extractions
    
    async def _extract_from_zone(self, zone_type: str, text: str, confidence: float) -> Optional[Dict[str, Any]]:
        """Ekstraktē datus no konkrētas zones"""
        try:
            extraction = {
                "zone_type": zone_type,
                "confidence": confidence,
                "extracted_fields": {}
            }
            
            # Get expected fields for this zone type
            zone_enum = self._get_zone_enum(zone_type)
            expected_fields = self.zone_field_mapping.get(zone_enum, [])
            
            # Extract each expected field
            for field in expected_fields:
                field_value = await self._extract_specific_field(field, text, zone_type)
                if field_value:
                    extraction["extracted_fields"][field] = field_value
            
            return extraction if extraction["extracted_fields"] else None
            
        except Exception as e:
            self.logger.error(f"❌ Zone extraction failed for {zone_type}: {e}")
            return None
    
    def _get_zone_enum(self, zone_type_str: str) -> Optional[ZoneType]:
        """Konvertē zone type string uz ZoneType enum"""
        try:
            # Handle both string and enum cases
            if isinstance(zone_type_str, str):
                # Try direct enum value mapping
                for zone_enum in ZoneType:
                    if zone_enum.value == zone_type_str or zone_enum.name.lower() == zone_type_str.lower():
                        return zone_enum
            return None
        except:
            return None
    
    async def _extract_specific_field(self, field: str, text: str, zone_type: str) -> Optional[Any]:
        """Ekstraktē konkrētu field no zone text"""
        try:
            # Use zone-optimized patterns
            if field == "supplier_name" and "supplier" in zone_type.lower():
                return await self._extract_supplier_from_zone(text)
            elif field == "invoice_number" and "invoice" in zone_type.lower():
                return await self._extract_invoice_number_from_zone(text)
            elif field in ["invoice_date", "delivery_date"] and any(x in zone_type.lower() for x in ["date", "header", "invoice"]):
                return await self._extract_date_from_zone(text)
            elif field == "total_amount" and "amount" in zone_type.lower():
                return await self._extract_amount_from_zone(text)
            elif field == "products" and "table" in zone_type.lower():
                return await self._extract_products_from_zone(text)
            
            # Fallback to base extraction methods
            return await self._fallback_field_extraction(field, text)
            
        except Exception as e:
            self.logger.error(f"❌ Field extraction failed for {field}: {e}")
            return None
    
    async def _extract_supplier_from_zone(self, text: str) -> Optional[str]:
        """Zone-optimized supplier extraction"""
        # Supplier-specific patterns for supplier zones
        patterns = [
            r'^([A-ZĀČĒĢĪĶĻŅŠŪŽ][a-zāčēģīķļņšūž\s]+(?:SIA|AS|Ltd|Inc)?)',
            r'([A-ZĀČĒĢĪĶĻŅŠŪŽ][a-zāčēģīķļņšūž\s]+(?:SIA|AS))',
            r'Piegādātājs[:\s]+([^\n\r]+)',
            r'Seller[:\s]+([^\n\r]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    async def _extract_invoice_number_from_zone(self, text: str) -> Optional[str]:
        """Zone-optimized invoice number extraction"""
        patterns = [
            r'(?:Rēķins|Invoice|Nr\.?)[:\s]*([A-Z0-9\-/]+)',
            r'(?:Pavadzīme|Document)[:\s]*([A-Z0-9\-/]+)',
            r'(?:Dok\.|Doc\.)[:\s]*([A-Z0-9\-/]+)',
            r'^([A-Z]{2,4}[0-9\-/]+)',  # Starting pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    async def _extract_date_from_zone(self, text: str) -> Optional[str]:
        """Zone-optimized date extraction"""
        # Date patterns specific to header/invoice zones
        patterns = [
            r'(?:Datums|Date)[:\s]*(\d{1,2}[./\-]\d{1,2}[./\-]\d{4})',
            r'(\d{1,2}[./\-]\d{1,2}[./\-]\d{4})',
            r'(\d{4}[./\-]\d{1,2}[./\-]\d{1,2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    async def _extract_amount_from_zone(self, text: str) -> Optional[float]:
        """Zone-optimized amount extraction"""
        # Amount patterns for amount zones
        patterns = [
            r'(?:Kopā|Total|Summa)[:\s]*([0-9.,]+)',
            r'(?:EUR|€)[:\s]*([0-9.,]+)',
            r'([0-9.,]+)\s*(?:EUR|€)',
            r'([0-9]+[.,][0-9]{2})'  # Standard money format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '.')
                    return float(amount_str)
                except ValueError:
                    continue
        return None
    
    async def _extract_products_from_zone(self, text: str) -> Optional[List[Dict[str, Any]]]:
        """Zone-optimized products extraction from table zones"""
        products = []
        
        # Split by lines and process table-like structure
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            # Skip header lines
            if any(header in line.lower() for header in ['nosaukums', 'produkts', 'prece', 'daudzums', 'cena']):
                continue
            
            # Try to extract product info from line
            product = await self._parse_product_line(line)
            if product:
                products.append(product)
        
        return products if products else None
    
    async def _parse_product_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse individual product line from table"""
        # Simple table parsing - can be enhanced
        parts = re.split(r'\s{2,}|\t', line)  # Split by multiple spaces or tabs
        
        if len(parts) >= 2:
            product = {
                "name": parts[0].strip(),
                "raw_line": line
            }
            
            # Try to find quantity and price
            for part in parts[1:]:
                if re.match(r'^\d+([.,]\d+)?$', part):
                    if "quantity" not in product:
                        product["quantity"] = part
                    elif "price" not in product:
                        product["price"] = part
                elif re.match(r'^\d+[.,]\d{2}$', part):
                    product["price"] = part
            
            return product
        
        return None
    
    async def _fallback_field_extraction(self, field: str, text: str) -> Optional[Any]:
        """Fallback extraction using base extraction service"""
        try:
            # Create temporary ExtractedData for fallback
            temp_data = await self.base_extractor.extract_invoice_data(text)
            return getattr(temp_data, field, None)
        except:
            return None
    
    async def _merge_extractions(self, zone_extractions: Dict[str, Dict[str, Any]], 
                               fallback_data: ExtractedData,
                               ocr_result: StructureAwareOCRResult) -> ExtractedData:
        """Intelligent merging no zone un fallback extractions"""
        merged = ExtractedData(
            invoice_number=None,
            supplier_name=None,
            supplier_reg_number=None,
            supplier_address=None,
            recipient_name=None,
            recipient_reg_number=None,
            recipient_address=None,
            invoice_date=None,
            delivery_date=None,
            total_amount=None,
            vat_amount=None,
            currency="EUR",
            products=[],
            supplier_bank_account=None,
            confidence_scores={},
            raw_extracted_text=None
        )
        
        # Priority: zone extractions > fallback data
        field_sources = {}
        
        # Extract from zones first (higher priority)
        for zone_type, zone_data in zone_extractions.items():
            confidence = zone_data.get("confidence", 0.0)
            weight = self.zone_confidence_weights.get(self._get_zone_enum(zone_type), 1.0)
            weighted_confidence = confidence * weight
            
            for field, value in zone_data.get("extracted_fields", {}).items():
                if value and (field not in field_sources or field_sources[field]["confidence"] < weighted_confidence):
                    field_sources[field] = {
                        "value": value,
                        "confidence": weighted_confidence,
                        "source": f"zone_{zone_type}"
                    }
        
        # Fill remaining fields from fallback
        fallback_fields = {
            "invoice_number": fallback_data.invoice_number,
            "supplier_name": fallback_data.supplier_name,
            "supplier_reg_number": fallback_data.supplier_reg_number,
            "supplier_address": fallback_data.supplier_address,
            "recipient_name": fallback_data.recipient_name,
            "recipient_reg_number": fallback_data.recipient_reg_number,
            "recipient_address": fallback_data.recipient_address,
            "invoice_date": fallback_data.invoice_date,
            "delivery_date": fallback_data.delivery_date,
            "total_amount": fallback_data.total_amount,
            "vat_amount": fallback_data.vat_amount,
            "currency": fallback_data.currency,
            "products": fallback_data.products,
            "supplier_bank_account": fallback_data.supplier_bank_account
        }
        
        for field, fallback_value in fallback_fields.items():
            if field not in field_sources and fallback_value:
                field_sources[field] = {
                    "value": fallback_value,
                    "confidence": getattr(fallback_data, 'confidence_scores', {}).get('overall', 0.8) * 0.8,  # Lower confidence for fallback
                    "source": "fallback"
                }
        
        # Apply best values to merged result
        for field, source_data in field_sources.items():
            if hasattr(merged, field):
                setattr(merged, field, source_data["value"])
        
        # Calculate overall confidence
        if field_sources:
            overall_confidence = sum(data["confidence"] for data in field_sources.values()) / len(field_sources)
        else:
            overall_confidence = getattr(fallback_data, 'confidence_scores', {}).get('overall', 0.0)
        
        # Set confidence in confidence_scores
        merged.confidence_scores = {
            'overall': overall_confidence,
            **{field: data["confidence"] for field, data in field_sources.items()}
        }
        
        # Set raw_extracted_text for debugging
        merged.raw_extracted_text = f"extraction_method=structure_aware;field_sources={len(field_sources)};zone_count={len(zone_extractions)}"
        
        return merged
    
    async def _generate_structure_insights(self, ocr_result: StructureAwareOCRResult, 
                                         zone_extractions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate structure-based insights"""
        insights = {
            "zone_coverage": {},
            "extraction_success_rate": 0.0,
            "structure_quality": 0.0,
            "recommendations": []
        }
        
        try:
            # Zone coverage analysis
            total_zones = len(ocr_result.zone_results)
            successful_extractions = len(zone_extractions)
            
            insights["zone_coverage"] = {
                "total_zones": total_zones,
                "successful_extractions": successful_extractions,
                "coverage_rate": successful_extractions / max(total_zones, 1)
            }
            
            # Extraction success rate
            total_expected_fields = sum(len(self.zone_field_mapping.get(self._get_zone_enum(zone), [])) 
                                      for zone in ocr_result.zone_results.keys())
            total_extracted_fields = sum(len(data.get("extracted_fields", {})) 
                                       for data in zone_extractions.values())
            
            insights["extraction_success_rate"] = total_extracted_fields / max(total_expected_fields, 1)
            
            # Structure quality assessment
            avg_zone_confidence = sum(data.get("confidence", 0) for data in ocr_result.zone_results.values() 
                                    if isinstance(data, dict)) / max(len(ocr_result.zone_results), 1)
            
            insights["structure_quality"] = avg_zone_confidence
            
            # Recommendations
            if insights["zone_coverage"]["coverage_rate"] < 0.7:
                insights["recommendations"].append("Consider image quality improvement")
            if insights["extraction_success_rate"] < 0.5:
                insights["recommendations"].append("Manual review recommended")
            if avg_zone_confidence < 0.6:
                insights["recommendations"].append("Structure detection may be inaccurate")
            
        except Exception as e:
            self.logger.error(f"❌ Structure insights generation failed: {e}")
        
        return insights
    
    def _analyze_zone_mapping(self, zone_extractions: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """Analyze which fields were extracted from which zones"""
        zone_mapping = {}
        
        for zone_type, zone_data in zone_extractions.items():
            for field in zone_data.get("extracted_fields", {}):
                zone_mapping[field] = zone_type
        
        return zone_mapping
    
    def _calculate_zone_confidences(self, zone_extractions: Dict[str, Dict[str, Any]], 
                                  ocr_result: StructureAwareOCRResult) -> Dict[str, float]:
        """Calculate confidence scores per zone"""
        confidence_by_zone = {}
        
        for zone_type, zone_data in zone_extractions.items():
            base_confidence = zone_data.get("confidence", 0.0)
            field_count = len(zone_data.get("extracted_fields", {}))
            
            # Bonus for successful field extraction
            extraction_bonus = min(0.2, field_count * 0.05)
            zone_confidence = min(1.0, base_confidence + extraction_bonus)
            
            confidence_by_zone[zone_type] = zone_confidence
        
        return confidence_by_zone
    
    def _determine_extraction_strategy(self, zone_extractions: Dict[str, Dict[str, Any]], 
                                     ocr_result: StructureAwareOCRResult) -> str:
        """Determine which extraction strategy was most effective"""
        zone_success_rate = len(zone_extractions) / max(len(ocr_result.zone_results), 1)
        
        if zone_success_rate > 0.8:
            return "zone_primary"
        elif zone_success_rate > 0.5:
            return "zone_hybrid"
        else:
            return "fallback_primary"
