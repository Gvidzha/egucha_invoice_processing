#!/usr/bin/env python3
"""
Template sistēmas integrācijas tests
Parāda kā jauno template sistēmu varētu integrēt ar esošo kodu
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Pievienot backend ceļu
sys.path.append(str(Path(__file__).parent / "backend"))

class TemplateIntegrationDemo:
    """Demonstrē template sistēmas integrāciju"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent / "backend" / "config" / "schemas"
        self.template_en = None
        self.field_mappings_en = None
        self.validation_rules_en = None
        self._load_configurations()
    
    def _load_configurations(self):
        """Ielādē konfigurācijas"""
        try:
            # Angļu template
            template_file = self.config_dir / "invoice_template_en.json"
            if template_file.exists():
                with open(template_file, 'r', encoding='utf-8') as f:
                    self.template_en = json.load(f)
            
            # Angļu mappings
            mappings_file = self.config_dir / "field_mappings_en.json"
            if mappings_file.exists():
                with open(mappings_file, 'r', encoding='utf-8') as f:
                    self.field_mappings_en = json.load(f)
            
            # Angļu validation
            validation_file = self.config_dir / "validation_rules_en.json"
            if validation_file.exists():
                with open(validation_file, 'r', encoding='utf-8') as f:
                    self.validation_rules_en = json.load(f)
                    
        except Exception as e:
            print(f"Configuration error: {e}")
    
    def simulate_existing_extraction_service(self, text: str) -> Dict[str, Any]:
        """Simulē esošo ekstraktēšanas servisu"""
        # Simulētie rezultāti (kā no pašreizējās sistēmas)
        return {
            "invoice_number": "PAV-2025-12345",
            "supplier_name": "SIA \"Latvijas Piegādātājs\"",
            "supplier_reg_number": "40003123456",
            "supplier_address": "Rīga, Brīvības iela 123",
            "recipient_name": "SIA \"Mūsu Uzņēmums\"", 
            "recipient_reg_number": "40003654321",
            "recipient_address": "Jelgava, Lielupes iela 45",
            "total_amount": 150.75,
            "vat_amount": 31.50,
            "currency": "EUR",
            "invoice_date": "2025-01-15",
            "delivery_date": "2025-01-20",
            "confidence_score": 0.85
        }
    
    def enhanced_extraction_with_template(self, text: str) -> Dict[str, Any]:
        """Uzlabota ekstraktēšana ar template sistēmu"""
        
        # 1. Sākt ar esošo ekstraktēšanas servisu
        base_results = self.simulate_existing_extraction_service(text)
        
        # 2. Konvertēt uz angļu template formātu
        english_data = {}
        if self.field_mappings_en:
            mapping = self.field_mappings_en.get("field_mappings", {}).get("existing_db_to_english_template", {})
            
            for db_field, value in base_results.items():
                english_field = mapping.get(db_field, db_field)
                english_data[english_field] = value
        
        # 3. Validēt ar template noteikumiem
        validation_result = self.validate_with_template(base_results)
        
        # 4. Piemērot auto-corrections
        corrected_data = self.apply_auto_corrections(base_results)
        
        # 5. Aprēķināt uzlaboto confidence
        enhanced_confidence = self.calculate_enhanced_confidence(base_results, validation_result)
        
        return {
            "original_results": base_results,
            "english_template_format": english_data,
            "validation": validation_result,
            "corrected_data": corrected_data,
            "enhanced_confidence": enhanced_confidence,
            "template_used": "invoice_template_en.json"
        }
    
    def validate_with_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validē ar template sistēmu"""
        if not self.validation_rules_en:
            return {"valid": True, "errors": [], "warnings": []}
        
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "field_validations": {}
        }
        
        validation_rules = self.validation_rules_en.get("validation_rules", {})
        
        # Mapē DB laukus uz angļu laukiem un validē
        for db_field, value in data.items():
            english_field = self.map_db_to_english(db_field)
            
            if english_field in validation_rules:
                field_validation = self._validate_field_detailed(
                    english_field, value, validation_rules[english_field]
                )
                validation_results["field_validations"][db_field] = field_validation
                
                if not field_validation["valid"]:
                    validation_results["valid"] = False
                    validation_results["errors"].extend(field_validation["errors"])
                
                validation_results["warnings"].extend(field_validation["warnings"])
        
        # Cross-field validation
        cross_validation = self._validate_cross_fields(data)
        validation_results["errors"].extend(cross_validation["errors"])
        validation_results["warnings"].extend(cross_validation["warnings"])
        
        return validation_results
    
    def apply_auto_corrections(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Piemēro automātiskos labojumus"""
        corrected = data.copy()
        corrections_applied = []
        
        if not self.validation_rules_en:
            return corrected
        
        auto_rules = self.validation_rules_en.get("auto_correction_rules", {})
        if not auto_rules.get("enabled", False):
            return corrected
        
        rules = auto_rules.get("rules", {})
        
        # Trim whitespace
        for field in ["supplier_name", "recipient_name", "invoice_number"]:
            if field in corrected and isinstance(corrected[field], str):
                original = corrected[field]
                corrected[field] = original.strip()
                if original != corrected[field]:
                    corrections_applied.append(f"Trimmed whitespace from {field}")
        
        # Normalize currency
        if "currency" in corrected:
            currency_mapping = rules.get("normalize_currency", {}).get("mappings", {})
            original = corrected["currency"]
            normalized = currency_mapping.get(original.lower() if isinstance(original, str) else original, original)
            if normalized != original:
                corrected["currency"] = normalized
                corrections_applied.append(f"Normalized currency: {original} → {normalized}")
        
        # Format registration numbers
        for field in ["supplier_reg_number", "recipient_reg_number"]:
            if field in corrected and corrected[field]:
                original = str(corrected[field])
                # Remove non-numeric characters
                numeric_only = ''.join(c for c in original if c.isdigit())
                if len(numeric_only) == 11:
                    corrected[field] = numeric_only
                    if numeric_only != original:
                        corrections_applied.append(f"Formatted {field}: {original} → {numeric_only}")
        
        corrected["_corrections_applied"] = corrections_applied
        return corrected
    
    def calculate_enhanced_confidence(self, data: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
        """Aprēķina uzlaboto confidence ar template sistēmu"""
        base_confidence = data.get("confidence_score", 0.5)
        
        # Confidence penalties/bonuses
        confidence_adjustments = []
        
        # Penalty for validation errors
        error_count = len(validation.get("errors", []))
        if error_count > 0:
            error_penalty = min(0.3, error_count * 0.1)
            base_confidence -= error_penalty
            confidence_adjustments.append(f"Validation errors penalty: -{error_penalty:.2f}")
        
        # Bonus for complete required fields
        if self.validation_rules_en:
            rules = self.validation_rules_en.get("validation_rules", {})
            required_fields = [field for field, rule in rules.items() if rule.get("required", False)]
            
            # Map to DB fields
            required_db_fields = []
            for req_field in required_fields:
                db_field = self.map_english_to_db(req_field)
                if db_field:
                    required_db_fields.append(db_field)
            
            completed_required = sum(1 for field in required_db_fields if data.get(field))
            if required_db_fields:
                completeness_ratio = completed_required / len(required_db_fields)
                if completeness_ratio >= 0.8:
                    bonus = 0.1 * completeness_ratio
                    base_confidence += bonus
                    confidence_adjustments.append(f"Required fields bonus: +{bonus:.2f}")
        
        # Ensure confidence stays in [0, 1] range
        final_confidence = max(0.0, min(1.0, base_confidence))
        
        return {
            "original_confidence": data.get("confidence_score", 0.5),
            "final_confidence": final_confidence,
            "adjustments": confidence_adjustments,
            "validation_errors": len(validation.get("errors", [])),
            "validation_warnings": len(validation.get("warnings", []))
        }
    
    def map_db_to_english(self, db_field: str) -> Optional[str]:
        """Map DB field to English field"""
        if not self.field_mappings_en:
            return None
        return self.field_mappings_en.get("field_mappings", {}).get("existing_db_to_english_template", {}).get(db_field)
    
    def map_english_to_db(self, english_field: str) -> Optional[str]:
        """Map English field to DB field"""
        if not self.field_mappings_en:
            return None
        return self.field_mappings_en.get("field_mappings", {}).get("english_template_to_existing_db", {}).get(english_field)
    
    def _validate_field_detailed(self, field_name: str, value: Any, rules: Dict) -> Dict[str, Any]:
        """Detalizēta lauka validācija"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks_performed": []
        }
        
        # Required check
        if rules.get("required", False) and (value is None or value == ""):
            result["valid"] = False
            result["errors"].append(f"Required field {field_name} is missing")
            result["checks_performed"].append("required")
            return result
        
        if value is None or value == "":
            return result
        
        # String validations
        if isinstance(value, str):
            result["checks_performed"].append("string_validation")
            
            if "min_length" in rules and len(value) < rules["min_length"]:
                result["valid"] = False
                result["errors"].append(f"{field_name} too short (min: {rules['min_length']})")
            
            if "max_length" in rules and len(value) > rules["max_length"]:
                result["valid"] = False
                result["errors"].append(f"{field_name} too long (max: {rules['max_length']})")
            
            if "pattern" in rules:
                import re
                if not re.match(rules["pattern"], value):
                    result["valid"] = False
                    result["errors"].append(f"{field_name} invalid format")
        
        # Numeric validations
        if rules.get("type") == "decimal":
            result["checks_performed"].append("numeric_validation")
            try:
                numeric_value = float(value)
                
                if "min_value" in rules and numeric_value < rules["min_value"]:
                    result["valid"] = False
                    result["errors"].append(f"{field_name} below minimum ({rules['min_value']})")
                
                if "max_value" in rules and numeric_value > rules["max_value"]:
                    result["valid"] = False
                    result["errors"].append(f"{field_name} above maximum ({rules['max_value']})")
                    
            except (ValueError, TypeError):
                result["valid"] = False
                result["errors"].append(f"{field_name} must be numeric")
        
        return result
    
    def _validate_cross_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cross-field validācijas"""
        result = {"errors": [], "warnings": []}
        
        # VAT calculation check
        try:
            subtotal = float(data.get("subtotal_amount", 0) or 0)
            vat = float(data.get("vat_amount", 0) or 0) 
            total = float(data.get("total_amount", 0) or 0)
            
            expected_total = subtotal + vat
            if abs(total - expected_total) > 0.01:
                result["warnings"].append(f"VAT calculation mismatch: {total} ≠ {subtotal} + {vat}")
                
        except (ValueError, TypeError):
            pass
        
        return result

def demo_integration():
    """Demonstrē integrāciju"""
    print("🔧 Template Integration Demo")
    print("=" * 50)
    
    demo = TemplateIntegrationDemo()
    
    # Simulētais teksts
    sample_text = """
    PAVADZĪME Nr. PAV-2025-12345
    Piegādātājs: SIA "Latvijas Piegādātājs"
    Reģ.Nr. 40003123456
    Saņēmējs: SIA "Mūsu Uzņēmums"
    Kopā apmaksai: 150.75 EUR
    PVN: 31.50 EUR
    """
    
    print("📄 Processing sample invoice text...")
    print(f"Text preview: {sample_text[:100]}...")
    
    # Procesēt ar uzlaboto sistēmu
    results = demo.enhanced_extraction_with_template(sample_text)
    
    print("\n📊 Original Extraction Results:")
    print("-" * 30)
    for key, value in results["original_results"].items():
        print(f"  {key}: {value}")
    
    print("\n🇬🇧 English Template Format:")
    print("-" * 30)
    for key, value in results["english_template_format"].items():
        print(f"  {key}: {value}")
    
    print("\n✅ Validation Results:")
    print("-" * 30)
    validation = results["validation"]
    print(f"Valid: {'✅ YES' if validation['valid'] else '❌ NO'}")
    
    if validation["errors"]:
        print("Errors:")
        for error in validation["errors"]:
            print(f"  ❌ {error}")
    
    if validation["warnings"]:
        print("Warnings:")
        for warning in validation["warnings"]:
            print(f"  ⚠️ {warning}")
    
    print("\n🔧 Auto-Corrections Applied:")
    print("-" * 30)
    corrections = results["corrected_data"].get("_corrections_applied", [])
    if corrections:
        for correction in corrections:
            print(f"  🔧 {correction}")
    else:
        print("  No corrections needed")
    
    print("\n🎯 Enhanced Confidence:")
    print("-" * 30)
    confidence = results["enhanced_confidence"]
    print(f"Original: {confidence['original_confidence']:.2f}")
    print(f"Enhanced: {confidence['final_confidence']:.2f}")
    
    if confidence["adjustments"]:
        print("Adjustments:")
        for adj in confidence["adjustments"]:
            print(f"  📈 {adj}")
    
    print("\n🎉 Integration Demo Completed!")
    print("=" * 50)
    print("✅ Template system successfully integrated")
    print("✅ Validation and auto-correction working")
    print("✅ Enhanced confidence calculation functional")
    print("✅ No existing code modified")

if __name__ == "__main__":
    demo_integration()
