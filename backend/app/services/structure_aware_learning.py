"""
Structure-Aware Learning Service - POSM 4.5 Week 3
Papildu intelligent learning ar document structure context
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session

from app.models import ErrorCorrection
from app.services.learning_service import LearningService
from app.services.document_structure_service import DocumentStructure, ZoneType
from app.services.structure_aware_extraction import StructureAwareExtractionResult

logger = logging.getLogger(__name__)

@dataclass
class StructureAwareLearningResult:
    """Structure-aware learning rezultāta konteiners"""
    learning_applied: bool
    improved_fields: List[str]
    structure_patterns: Dict[str, Any]
    confidence_improvements: Dict[str, float]
    learning_strategy: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertē uz dictionary"""
        return asdict(self)

@dataclass
class StructurePattern:
    """Structure pattern for learning"""
    zone_type: str
    field_type: str
    pattern: str
    confidence: float
    usage_count: int
    success_rate: float
    last_updated: datetime

class StructureAwareLearningService:
    """
    Structure-Aware Learning Service
    
    Capabilities:
    - Zone-specific pattern learning
    - Structure-context-aware error correction
    - Template-based learning optimization
    - Confidence improvement through structure insights
    """
    
    def __init__(self, db: Session):
        """Inicializē structure-aware learning servisu"""
        self.db = db
        self.base_learning = LearningService(db)
        self.logger = logging.getLogger(__name__)
        
        # Structure-specific learning patterns
        self.structure_patterns: Dict[str, List[StructurePattern]] = {}
        
        # Zone-specific learning weights
        self.zone_learning_weights = {
            ZoneType.SUPPLIER_INFO: 1.5,
            ZoneType.AMOUNTS: 1.4,
            ZoneType.INVOICE_DETAILS: 1.3,
            ZoneType.TABLE: 1.2,
            ZoneType.HEADER: 1.1,
            ZoneType.RECIPIENT_INFO: 1.0,
            ZoneType.FOOTER: 0.9
        }
        
        # Learning strategies
        self.learning_strategies = {
            "zone_specific": self._learn_zone_specific,
            "pattern_based": self._learn_pattern_based,
            "template_aware": self._learn_template_aware,
            "confidence_driven": self._learn_confidence_driven
        }
    
    async def learn_from_structure_correction(self,
                                            original_extraction: StructureAwareExtractionResult,
                                            corrected_values: Dict[str, Any],
                                            document_structure: Optional[DocumentStructure] = None,
                                            invoice_id: Optional[int] = None) -> StructureAwareLearningResult:
        """
        Galvenā learning metode ar structure awareness
        
        Args:
            original_extraction: Oriģinālais extraction rezultāts
            corrected_values: Lietotāja labotās vērtības {field: corrected_value}
            document_structure: Document structure information
            invoice_id: Pavadzīmes ID
        
        Returns:
            StructureAwareLearningResult: Learning rezultāts
        """
        try:
            self.logger.info(f"🧠 Starting structure-aware learning for {len(corrected_values)} corrections")
            
            # 1. Determine learning strategy
            learning_strategy = self._determine_learning_strategy(original_extraction, corrected_values)
            
            # 2. Apply structure-aware learning
            learning_result = await self.learning_strategies[learning_strategy](
                original_extraction, corrected_values, document_structure, invoice_id
            )
            
            # 3. Update base learning service
            await self._update_base_learning(original_extraction, corrected_values, invoice_id)
            
            # 4. Update structure patterns
            await self._update_structure_patterns(original_extraction, corrected_values, document_structure)
            
            # 5. Calculate confidence improvements
            confidence_improvements = await self._calculate_confidence_improvements(
                original_extraction, corrected_values
            )
            
            result = StructureAwareLearningResult(
                learning_applied=True,
                improved_fields=list(corrected_values.keys()),
                structure_patterns=learning_result.get("patterns", {}),
                confidence_improvements=confidence_improvements,
                learning_strategy=learning_strategy,
                metadata={
                    "processing_time": datetime.now().isoformat(),
                    "correction_count": len(corrected_values),
                    "strategy_details": learning_result.get("details", {})
                }
            )
            
            self.logger.info(f"✅ Structure-aware learning completed: strategy={learning_strategy}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Structure-aware learning failed: {e}")
            return StructureAwareLearningResult(
                learning_applied=False,
                improved_fields=[],
                structure_patterns={},
                confidence_improvements={},
                learning_strategy="error",
                metadata={"error": str(e)}
            )
    
    def _determine_learning_strategy(self, 
                                   extraction_result: StructureAwareExtractionResult,
                                   corrections: Dict[str, Any]) -> str:
        """Noteic optimālo learning strategy"""
        try:
            # Analyze correction patterns
            zone_based_corrections = 0
            confidence_based_corrections = 0
            
            for field in corrections.keys():
                # Check if field has zone mapping
                if field in extraction_result.zone_mapping:
                    zone_based_corrections += 1
                
                # Check if field has low confidence
                zone_type = extraction_result.zone_mapping.get(field)
                if zone_type and extraction_result.confidence_by_zone.get(zone_type, 1.0) < 0.7:
                    confidence_based_corrections += 1
            
            # Determine strategy based on correction patterns
            if zone_based_corrections > len(corrections) * 0.7:
                return "zone_specific"
            elif confidence_based_corrections > len(corrections) * 0.6:
                return "confidence_driven"
            elif extraction_result.extraction_strategy in ["zone_primary", "zone_hybrid"]:
                return "pattern_based"
            else:
                return "template_aware"
            
        except Exception as e:
            self.logger.error(f"❌ Strategy determination failed: {e}")
            return "zone_specific"  # Default strategy
    
    async def _learn_zone_specific(self,
                                 extraction_result: StructureAwareExtractionResult,
                                 corrections: Dict[str, Any],
                                 document_structure: Optional[DocumentStructure],
                                 invoice_id: Optional[int]) -> Dict[str, Any]:
        """Zone-specific learning implementation"""
        learned_patterns = {}
        
        try:
            for field, corrected_value in corrections.items():
                zone_type = extraction_result.zone_mapping.get(field)
                if zone_type:
                    # Learn zone-specific patterns
                    pattern = await self._extract_zone_pattern(field, corrected_value, zone_type, extraction_result)
                    if pattern:
                        learned_patterns[f"{zone_type}_{field}"] = pattern
                        
                        # Update pattern database
                        await self._store_zone_pattern(zone_type, field, pattern)
            
            return {
                "patterns": learned_patterns,
                "details": {
                    "zone_patterns_learned": len(learned_patterns),
                    "zones_involved": list(set(extraction_result.zone_mapping.get(f) for f in corrections.keys() if f in extraction_result.zone_mapping))
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Zone-specific learning failed: {e}")
            return {"patterns": {}, "details": {"error": str(e)}}
    
    async def _learn_pattern_based(self,
                                 extraction_result: StructureAwareExtractionResult,
                                 corrections: Dict[str, Any],
                                 document_structure: Optional[DocumentStructure],
                                 invoice_id: Optional[int]) -> Dict[str, Any]:
        """Pattern-based learning implementation"""
        learned_patterns = {}
        
        try:
            for field, corrected_value in corrections.items():
                # Analyze what pattern should have been used
                improved_pattern = await self._generate_improved_pattern(field, corrected_value, extraction_result)
                if improved_pattern:
                    learned_patterns[field] = improved_pattern
            
            return {
                "patterns": learned_patterns,
                "details": {
                    "patterns_improved": len(learned_patterns),
                    "pattern_types": list(learned_patterns.keys())
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Pattern-based learning failed: {e}")
            return {"patterns": {}, "details": {"error": str(e)}}
    
    async def _learn_template_aware(self,
                                  extraction_result: StructureAwareExtractionResult,
                                  corrections: Dict[str, Any],
                                  document_structure: Optional[DocumentStructure],
                                  invoice_id: Optional[int]) -> Dict[str, Any]:
        """Template-aware learning implementation"""
        template_insights = {}
        
        try:
            # Identify template characteristics
            if document_structure:
                template_features = await self._extract_template_features(document_structure, extraction_result)
                
                for field, corrected_value in corrections.items():
                    # Learn template-specific correction patterns
                    template_pattern = await self._generate_template_pattern(
                        field, corrected_value, template_features
                    )
                    if template_pattern:
                        template_insights[field] = template_pattern
            
            return {
                "patterns": template_insights,
                "details": {
                    "template_patterns": len(template_insights),
                    "template_identified": document_structure is not None
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Template-aware learning failed: {e}")
            return {"patterns": {}, "details": {"error": str(e)}}
    
    async def _learn_confidence_driven(self,
                                     extraction_result: StructureAwareExtractionResult,
                                     corrections: Dict[str, Any],
                                     document_structure: Optional[DocumentStructure],
                                     invoice_id: Optional[int]) -> Dict[str, Any]:
        """Confidence-driven learning implementation"""
        confidence_adjustments = {}
        
        try:
            for field, corrected_value in corrections.items():
                zone_type = extraction_result.zone_mapping.get(field)
                if zone_type:
                    current_confidence = extraction_result.confidence_by_zone.get(zone_type, 0.0)
                    
                    # Learn confidence adjustment patterns
                    adjustment = await self._calculate_confidence_adjustment(
                        field, corrected_value, current_confidence, extraction_result
                    )
                    
                    if adjustment:
                        confidence_adjustments[f"{zone_type}_{field}"] = adjustment
            
            return {
                "patterns": confidence_adjustments,
                "details": {
                    "confidence_adjustments": len(confidence_adjustments),
                    "avg_confidence_before": sum(extraction_result.confidence_by_zone.values()) / max(len(extraction_result.confidence_by_zone), 1)
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Confidence-driven learning failed: {e}")
            return {"patterns": {}, "details": {"error": str(e)}}
    
    async def _extract_zone_pattern(self, field: str, corrected_value: Any, zone_type: str, 
                                  extraction_result: StructureAwareExtractionResult) -> Optional[Dict[str, Any]]:
        """Extract pattern from zone-specific correction"""
        try:
            pattern_data = {
                "field": field,
                "zone_type": zone_type,
                "corrected_value": str(corrected_value),
                "pattern_type": self._determine_pattern_type(field, corrected_value),
                "confidence": 0.8,  # Initial confidence for learned patterns
                "context": extraction_result.structure_insights.get("zone_analysis", {}).get(zone_type, {})
            }
            
            return pattern_data
            
        except Exception as e:
            self.logger.error(f"❌ Zone pattern extraction failed: {e}")
            return None
    
    def _determine_pattern_type(self, field: str, value: Any) -> str:
        """Determine pattern type based on field and value"""
        if field in ["date", "delivery_date"]:
            return "date_pattern"
        elif field in ["total_amount", "vat_amount"]:
            return "amount_pattern"
        elif field in ["document_number"]:
            return "id_pattern"
        elif field in ["supplier", "recipient"]:
            return "name_pattern"
        else:
            return "text_pattern"
    
    async def _store_zone_pattern(self, zone_type: str, field: str, pattern: Dict[str, Any]):
        """Store learned pattern in pattern database"""
        try:
            # Store in in-memory structure patterns
            if zone_type not in self.structure_patterns:
                self.structure_patterns[zone_type] = []
            
            structure_pattern = StructurePattern(
                zone_type=zone_type,
                field_type=field,
                pattern=json.dumps(pattern),
                confidence=pattern.get("confidence", 0.8),
                usage_count=1,
                success_rate=1.0,
                last_updated=datetime.now()
            )
            
            self.structure_patterns[zone_type].append(structure_pattern)
            
            # Could also store in database for persistence
            # await self._store_pattern_in_db(structure_pattern)
            
        except Exception as e:
            self.logger.error(f"❌ Pattern storage failed: {e}")
    
    async def _generate_improved_pattern(self, field: str, corrected_value: Any, 
                                       extraction_result: StructureAwareExtractionResult) -> Optional[Dict[str, Any]]:
        """Generate improved extraction pattern based on correction"""
        try:
            # Analyze what went wrong and how to improve
            original_value = getattr(extraction_result.extracted_data, field, None)
            
            improvement = {
                "field": field,
                "original_value": str(original_value) if original_value else None,
                "corrected_value": str(corrected_value),
                "improvement_type": self._classify_improvement(original_value, corrected_value),
                "confidence_boost": 0.1  # Boost for patterns that needed correction
            }
            
            return improvement
            
        except Exception as e:
            self.logger.error(f"❌ Improved pattern generation failed: {e}")
            return None
    
    def _classify_improvement(self, original: Any, corrected: Any) -> str:
        """Classify the type of improvement made"""
        if original is None:
            return "missing_value_found"
        elif str(original) != str(corrected):
            return "value_corrected"
        else:
            return "unknown_improvement"
    
    async def _extract_template_features(self, document_structure: DocumentStructure, 
                                       extraction_result: StructureAwareExtractionResult) -> Dict[str, Any]:
        """Extract template-specific features"""
        features = {
            "zone_count": len(document_structure.zones),
            "table_count": len(document_structure.tables),
            "extraction_strategy": extraction_result.extraction_strategy,
            "successful_zones": len(extraction_result.zone_mapping),
            "confidence_pattern": list(extraction_result.confidence_by_zone.values())
        }
        
        return features
    
    async def _generate_template_pattern(self, field: str, corrected_value: Any, 
                                       template_features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate template-specific correction pattern"""
        try:
            pattern = {
                "field": field,
                "corrected_value": str(corrected_value),
                "template_features": template_features,
                "template_confidence": 0.9
            }
            
            return pattern
            
        except Exception as e:
            self.logger.error(f"❌ Template pattern generation failed: {e}")
            return None
    
    async def _calculate_confidence_adjustment(self, field: str, corrected_value: Any, 
                                             current_confidence: float,
                                             extraction_result: StructureAwareExtractionResult) -> Optional[Dict[str, Any]]:
        """Calculate confidence adjustment based on correction"""
        try:
            # If a correction was needed, confidence should be lowered for similar cases
            confidence_penalty = min(0.2, (1.0 - current_confidence) * 0.5)
            
            adjustment = {
                "field": field,
                "original_confidence": current_confidence,
                "confidence_penalty": confidence_penalty,
                "new_threshold": max(0.1, current_confidence - confidence_penalty)
            }
            
            return adjustment
            
        except Exception as e:
            self.logger.error(f"❌ Confidence adjustment calculation failed: {e}")
            return None
    
    async def _update_base_learning(self, extraction_result: StructureAwareExtractionResult,
                                  corrections: Dict[str, Any], invoice_id: Optional[int]):
        """Update base learning service with corrections"""
        try:
            for field, corrected_value in corrections.items():
                original_value = getattr(extraction_result.extracted_data, field, None)
                
                if original_value != corrected_value:
                    await self.base_learning.learn_from_correction(
                        original_value=str(original_value) if original_value else "",
                        corrected_value=str(corrected_value),
                        error_type=field,
                        context=f"structure_aware_{extraction_result.extraction_strategy}",
                        invoice_id=invoice_id
                    )
        except Exception as e:
            self.logger.error(f"❌ Base learning update failed: {e}")
    
    async def _update_structure_patterns(self, extraction_result: StructureAwareExtractionResult,
                                       corrections: Dict[str, Any],
                                       document_structure: Optional[DocumentStructure]):
        """Update structure-specific patterns"""
        try:
            for field, corrected_value in corrections.items():
                zone_type = extraction_result.zone_mapping.get(field)
                if zone_type:
                    # Update success rates for existing patterns
                    await self._update_pattern_success_rate(zone_type, field, False)  # Correction needed = failure
                    
                    # Create new improved pattern
                    improved_pattern = await self._extract_zone_pattern(field, corrected_value, zone_type, extraction_result)
                    if improved_pattern:
                        await self._store_zone_pattern(zone_type, field, improved_pattern)
                        
        except Exception as e:
            self.logger.error(f"❌ Structure patterns update failed: {e}")
    
    async def _update_pattern_success_rate(self, zone_type: str, field: str, success: bool):
        """Update success rate for existing patterns"""
        try:
            if zone_type in self.structure_patterns:
                for pattern in self.structure_patterns[zone_type]:
                    if pattern.field_type == field:
                        pattern.usage_count += 1
                        if success:
                            pattern.success_rate = (pattern.success_rate * (pattern.usage_count - 1) + 1.0) / pattern.usage_count
                        else:
                            pattern.success_rate = (pattern.success_rate * (pattern.usage_count - 1)) / pattern.usage_count
                        pattern.last_updated = datetime.now()
                        
        except Exception as e:
            self.logger.error(f"❌ Pattern success rate update failed: {e}")
    
    async def _calculate_confidence_improvements(self, extraction_result: StructureAwareExtractionResult,
                                               corrections: Dict[str, Any]) -> Dict[str, float]:
        """Calculate expected confidence improvements from learning"""
        improvements = {}
        
        try:
            for field, corrected_value in corrections.items():
                zone_type = extraction_result.zone_mapping.get(field)
                if zone_type:
                    current_confidence = extraction_result.confidence_by_zone.get(zone_type, 0.0)
                    
                    # Calculate expected improvement based on learning
                    learning_weight = self.zone_learning_weights.get(self._get_zone_enum(zone_type), 1.0)
                    expected_improvement = min(0.3, (1.0 - current_confidence) * 0.4 * learning_weight)
                    
                    improvements[field] = expected_improvement
            
        except Exception as e:
            self.logger.error(f"❌ Confidence improvements calculation failed: {e}")
        
        return improvements
    
    def _get_zone_enum(self, zone_type_str: str) -> Optional[ZoneType]:
        """Convert zone type string to ZoneType enum"""
        try:
            if isinstance(zone_type_str, str):
                for zone_enum in ZoneType:
                    if zone_enum.value == zone_type_str or zone_enum.name.lower() == zone_type_str.lower():
                        return zone_enum
            return None
        except:
            return None
    
    async def get_structure_learning_stats(self) -> Dict[str, Any]:
        """Get structure-aware learning statistics"""
        try:
            stats = {
                "total_patterns": sum(len(patterns) for patterns in self.structure_patterns.values()),
                "patterns_by_zone": {zone: len(patterns) for zone, patterns in self.structure_patterns.items()},
                "avg_success_rate": 0.0,
                "most_learned_zones": [],
                "learning_strategies_used": list(self.learning_strategies.keys())
            }
            
            # Calculate average success rate
            if stats["total_patterns"] > 0:
                total_success_rate = sum(
                    pattern.success_rate for patterns in self.structure_patterns.values() 
                    for pattern in patterns
                )
                stats["avg_success_rate"] = total_success_rate / stats["total_patterns"]
            
            # Find most learned zones
            stats["most_learned_zones"] = sorted(
                stats["patterns_by_zone"].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Learning stats calculation failed: {e}")
            return {}
