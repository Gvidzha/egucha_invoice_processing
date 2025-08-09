"""
Template konfigurācijas serviss
Ielādē un pārvalda pavadzīmju lauku definīcijas
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FieldDefinition:
    """Lauka definīcija"""
    type: str
    required: bool = False
    description: str = ""
    default: Optional[Any] = None

class TemplateConfigService:
    """Serviss pavadzīmju template konfigurācijas pārvaldībai"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "config" / "schemas"
        self.template_data: Optional[Dict] = None
        self.field_mappings: Optional[Dict] = None
        self.validation_rules: Optional[Dict] = None
        # English template support
        self.template_en: Optional[Dict] = None
        self.field_mappings_en: Optional[Dict] = None
        self.validation_rules_en: Optional[Dict] = None
        self._load_configurations()
    
    def _load_configurations(self):
        """Ielādē visas konfigurācijas"""
        try:
            # Ielādē template
            template_file = self.config_dir / "invoice_template.json"
            if template_file.exists():
                with open(template_file, 'r', encoding='utf-8') as f:
                    self.template_data = json.load(f)
                logger.info("Template konfigurācija ielādēta")
            
            # Ielādē mappings
            mappings_file = self.config_dir / "field_mappings.json"
            if mappings_file.exists():
                with open(mappings_file, 'r', encoding='utf-8') as f:
                    self.field_mappings = json.load(f)
                logger.info("Field mappings ielādēti")
            
            # Ielādē validation rules
            validation_file = self.config_dir / "validation_rules.json"
            if validation_file.exists():
                with open(validation_file, 'r', encoding='utf-8') as f:
                    self.validation_rules = json.load(f)
                logger.info("Validation rules ielādēti")
            
            # Load English template configurations
            template_en_file = self.config_dir / "invoice_template_en.json"
            if template_en_file.exists():
                with open(template_en_file, 'r', encoding='utf-8') as f:
                    self.template_en = json.load(f)
                logger.info("English template configuration loaded")
            
            mappings_en_file = self.config_dir / "field_mappings_en.json"
            if mappings_en_file.exists():
                with open(mappings_en_file, 'r', encoding='utf-8') as f:
                    self.field_mappings_en = json.load(f)
                logger.info("English field mappings loaded")
            
            validation_en_file = self.config_dir / "validation_rules_en.json"
            if validation_en_file.exists():
                with open(validation_en_file, 'r', encoding='utf-8') as f:
                    self.validation_rules_en = json.load(f)
                logger.info("English validation rules loaded")
            if validation_file.exists():
                with open(validation_file, 'r', encoding='utf-8') as f:
                    self.validation_rules = json.load(f)
                logger.info("Validation rules ielādēti")
                
        except Exception as e:
            logger.error(f"Konfigurācijas ielādes kļūda: {e}")
    
    def get_all_fields(self) -> Dict[str, FieldDefinition]:
        """Atgriež visas lauku definīcijas"""
        if not self.template_data:
            return {}
        
        fields = {}
        
        # Iziet cauri visām kategorijām
        for category, category_fields in self.template_data.get("fields", {}).items():
            if category == "products":
                # Produktu lauki
                if isinstance(category_fields, dict) and "items" in category_fields:
                    for field_name, field_def in category_fields["items"].items():
                        fields[f"product_{field_name}"] = FieldDefinition(
                            type=field_def.get("type", "string"),
                            required=field_def.get("required", False),
                            description=field_def.get("description", "")
                        )
            else:
                # Parastie lauki
                if isinstance(category_fields, dict):
                    for field_name, field_def in category_fields.items():
                        if isinstance(field_def, dict):
                            fields[field_name] = FieldDefinition(
                                type=field_def.get("type", "string"),
                                required=field_def.get("required", False),
                                description=field_def.get("description", ""),
                                default=field_def.get("default")
                            )
        
        return fields
    
    def get_required_fields(self) -> List[str]:
        """Atgriež obligātos laukus"""
        all_fields = self.get_all_fields()
        return [name for name, field_def in all_fields.items() if field_def.required]
    
    def get_db_field_name(self, template_field: str) -> Optional[str]:
        """Konvertē template lauka nosaukumu uz DB lauka nosaukumu"""
        if not self.field_mappings:
            return None
        
        return self.field_mappings.get("field_mappings", {}).get("template_to_db", {}).get(template_field)
    
    def get_template_field_name(self, db_field: str) -> Optional[str]:
        """Konvertē DB lauka nosaukumu uz template lauka nosaukumu"""
        if not self.field_mappings:
            return None
        
        return self.field_mappings.get("field_mappings", {}).get("db_to_template", {}).get(db_field)
    
    def get_regex_patterns(self, field_name: str) -> List[str]:
        """Atgriež regex pattern konkrētam laukam"""
        if not self.field_mappings:
            return []
        
        return self.field_mappings.get("regex_patterns", {}).get(field_name, [])
    
    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validē ekstraktētos datus pret template un validation rules"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "auto_corrections": []
        }
        
        if not self.validation_rules:
            return validation_results
        
        validation_rules_data = self.validation_rules.get("validation_rules", {})
        
        # Validēt individuālos laukus
        for db_field, value in data.items():
            template_field = self.get_template_field_name(db_field)
            if template_field and template_field in validation_rules_data:
                field_validation = self._validate_field(
                    template_field, value, validation_rules_data[template_field]
                )
                
                if not field_validation["valid"]:
                    validation_results["valid"] = False
                
                validation_results["errors"].extend(field_validation["errors"])
                validation_results["warnings"].extend(field_validation["warnings"])
                validation_results["auto_corrections"].extend(field_validation["auto_corrections"])
        
        # Cross-field validation
        cross_field_results = self._validate_cross_fields(data)
        validation_results["errors"].extend(cross_field_results["errors"])
        validation_results["warnings"].extend(cross_field_results["warnings"])
        
        if cross_field_results["errors"]:
            validation_results["valid"] = False
        
        return validation_results
    
    def _validate_field(self, field_name: str, value: Any, rules: Dict) -> Dict[str, Any]:
        """Validē individuālo lauku"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "auto_corrections": []
        }
        
        error_messages = rules.get("error_messages", {})
        
        # Required check
        if rules.get("required", False) and (value is None or value == ""):
            result["valid"] = False
            result["errors"].append(error_messages.get("required", f"Lauks {field_name} ir obligāts"))
            return result
        
        # Skip further validation if value is empty and not required
        if value is None or value == "":
            return result
        
        # String validations
        if isinstance(value, str):
            # Min/max length
            if "min_length" in rules and len(value) < rules["min_length"]:
                result["valid"] = False
                result["errors"].append(error_messages.get("min_length", f"Pārāk īss"))
            
            if "max_length" in rules and len(value) > rules["max_length"]:
                result["valid"] = False
                result["errors"].append(error_messages.get("max_length", f"Pārāk garš"))
            
            # Pattern validation
            if "pattern" in rules:
                import re
                if not re.match(rules["pattern"], value):
                    result["valid"] = False
                    result["errors"].append(error_messages.get("pattern", f"Nepareizs formāts"))
            
            # Forbidden patterns
            if "forbidden_patterns" in rules:
                import re
                for pattern in rules["forbidden_patterns"]:
                    if re.search(pattern, value):
                        result["valid"] = False
                        result["errors"].append(error_messages.get("forbidden_patterns", f"Satur nederīgu saturu"))
            
            # Allowed values
            if "allowed_values" in rules and value not in rules["allowed_values"]:
                result["warnings"].append(
                    error_messages.get("allowed_values", f"Neatbalstīta vērtība: {value}")
                )
        
        # Numeric validations
        if rules.get("type") == "decimal":
            try:
                numeric_value = float(value) if isinstance(value, str) else value
                
                if "min_value" in rules and numeric_value < rules["min_value"]:
                    result["valid"] = False
                    result["errors"].append(error_messages.get("min_value", f"Pārāk maza vērtība"))
                
                if "max_value" in rules and numeric_value > rules["max_value"]:
                    result["valid"] = False
                    result["errors"].append(error_messages.get("max_value", f"Pārāk liela vērtība"))
                
            except (ValueError, TypeError):
                result["valid"] = False
                result["errors"].append(error_messages.get("type", f"Jābūt skaitlim"))
        
        return result
    
    def _validate_cross_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validē starp-lauku atkarības"""
        result = {
            "errors": [],
            "warnings": []
        }
        
        if not self.validation_rules:
            return result
        
        cross_validation = self.validation_rules.get("cross_field_validation", {})
        
        for validation_name, validation_config in cross_validation.items():
            if validation_name == "pvn_calculation":
                # PVN aprēķina pārbaude
                try:
                    summa_bez_pvn = float(data.get("subtotal_amount", 0) or 0)
                    pvn_summa = float(data.get("vat_amount", 0) or 0)
                    kopa_apmaksai = float(data.get("total_amount", 0) or 0)
                    
                    expected_total = summa_bez_pvn + pvn_summa
                    tolerance = validation_config.get("tolerance", 0.01)
                    
                    if abs(kopa_apmaksai - expected_total) > tolerance:
                        result["warnings"].append(validation_config.get("error_message", "PVN aprēķins nav pareizs"))
                
                except (ValueError, TypeError):
                    pass  # Skip if values can't be converted
        
        return result
    
    def get_confidence_threshold(self, field_name: str, level: str = "medium") -> float:
        """Atgriež confidence slieksni konkrētam laukam"""
        if not self.validation_rules:
            return 0.7
        
        thresholds = self.validation_rules.get("confidence_thresholds", {})
        
        # Field-specific threshold
        field_specific = thresholds.get("field_specific", {}).get(field_name, {})
        if level in field_specific:
            return field_specific[level]
        
        # Global threshold
        level_mapping = {
            "high": "high_confidence",
            "medium": "medium_confidence", 
            "low": "low_confidence"
        }
        
        return thresholds.get(level_mapping.get(level, "medium_confidence"), 0.7)
    
    def _validate_field_type(self, value: Any, expected_type: str) -> bool:
        """Validē lauka datu tipu"""
        if value is None:
            return True
        
        type_validators = {
            "string": lambda v: isinstance(v, str),
            "integer": lambda v: isinstance(v, int),
            "decimal": lambda v: isinstance(v, (int, float)),
            "date": lambda v: isinstance(v, str) and len(v) >= 8,  # Vienkārša datuma pārbaude
            "text": lambda v: isinstance(v, str)
        }
        
        validator = type_validators.get(expected_type, lambda v: True)
        return validator(value)
    
    def get_field_suggestions(self, partial_text: str, limit: int = 10) -> List[str]:
        """Atgriež lauku ieteikumus autocomplete funkcionalitātei"""
        all_fields = self.get_all_fields()
        suggestions = []
        
        partial_lower = partial_text.lower()
        
        for field_name, field_def in all_fields.items():
            # Meklē pēc lauka nosaukuma
            if partial_lower in field_name.lower():
                suggestions.append(field_name)
            # Meklē pēc apraksta
            elif partial_lower in field_def.description.lower():
                suggestions.append(field_name)
        
        return suggestions[:limit]
    
    # English Template Methods
    
    def map_db_to_english(self, db_field: str) -> Optional[str]:
        """Map database field to English template field"""
        if not self.field_mappings_en:
            return None
        
        mapping = self.field_mappings_en.get("field_mappings", {}).get("existing_db_to_english_template", {})
        return mapping.get(db_field)
    
    def map_english_to_db(self, english_field: str) -> Optional[str]:
        """Map English template field to database field"""
        if not self.field_mappings_en:
            return None
        
        mapping = self.field_mappings_en.get("field_mappings", {}).get("english_template_to_existing_db", {})
        return mapping.get(english_field)
    
    def map_latvian_to_english(self, latvian_field: str) -> Optional[str]:
        """Map Latvian field name to English template field"""
        if not self.field_mappings_en:
            return None
        
        mapping = self.field_mappings_en.get("field_mappings", {}).get("latvian_to_english", {})
        return mapping.get(latvian_field)
    
    def get_english_field_info(self, english_field: str) -> Optional[Dict[str, Any]]:
        """Get complete field information from English template"""
        if not self.template_en:
            return None
        
        # Search in all categories
        for category_name, category_data in self.template_en.get("invoice_template", {}).items():
            if isinstance(category_data, dict) and "fields" in category_data:
                fields = category_data["fields"]
                if english_field in fields:
                    return fields[english_field]
        
        return None
    
    def get_field_validation_rules_en(self, english_field: str) -> Optional[Dict[str, Any]]:
        """Get validation rules for English field"""
        if not self.validation_rules_en:
            return None
        
        return self.validation_rules_en.get("validation_rules", {}).get(english_field)
    
    def convert_to_english_format(self, db_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database format to English template format"""
        english_data = {}
        
        if not self.field_mappings_en:
            return db_data
        
        mapping = self.field_mappings_en.get("field_mappings", {}).get("existing_db_to_english_template", {})
        
        for db_field, value in db_data.items():
            english_field = mapping.get(db_field, db_field)
            english_data[english_field] = value
        
        return english_data
    
    def convert_to_db_format(self, english_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert English template format to database format"""
        db_data = {}
        
        if not self.field_mappings_en:
            return english_data
        
        mapping = self.field_mappings_en.get("field_mappings", {}).get("english_template_to_existing_db", {})
        
        for english_field, value in english_data.items():
            db_field = mapping.get(english_field, english_field)
            db_data[db_field] = value
        
        return db_data
    
    def validate_with_english_template(self, data: Dict[str, Any], format_type: str = "db") -> Dict[str, Any]:
        """
        Validate data against English template rules
        
        Args:
            data: Data to validate
            format_type: "db" (database format) or "english" (English template format)
        """
        if not self.validation_rules_en:
            return {"valid": True, "errors": [], "warnings": []}
        
        # Convert to English format if needed
        if format_type == "db":
            english_data = self.convert_to_english_format(data)
        else:
            english_data = data
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "field_validations": {}
        }
        
        validation_rules = self.validation_rules_en.get("validation_rules", {})
        
        # Validate each field
        for english_field, value in english_data.items():
            if english_field in validation_rules:
                field_result = self._validate_english_field(english_field, value, validation_rules[english_field])
                validation_result["field_validations"][english_field] = field_result
                
                if not field_result["valid"]:
                    validation_result["valid"] = False
                    validation_result["errors"].extend(field_result["errors"])
                
                validation_result["warnings"].extend(field_result["warnings"])
        
        # Cross-field validation
        cross_validation = self._validate_cross_fields_en(english_data)
        validation_result["errors"].extend(cross_validation["errors"])
        validation_result["warnings"].extend(cross_validation["warnings"])
        
        return validation_result
    
    def apply_auto_corrections_en(self, data: Dict[str, Any], format_type: str = "db") -> Dict[str, Any]:
        """
        Apply auto-corrections using English template rules
        
        Args:
            data: Data to correct
            format_type: "db" (database format) or "english" (English template format)
        """
        if not self.validation_rules_en:
            return data
        
        auto_rules = self.validation_rules_en.get("auto_correction_rules", {})
        if not auto_rules.get("enabled", False):
            return data
        
        # Convert to English format for processing
        if format_type == "db":
            english_data = self.convert_to_english_format(data)
        else:
            english_data = data.copy()
        
        corrected_data = english_data.copy()
        corrections_applied = []
        
        rules = auto_rules.get("rules", {})
        
        # Apply trim whitespace
        trim_fields = rules.get("trim_whitespace", {}).get("fields", [])
        for field in trim_fields:
            if field in corrected_data and isinstance(corrected_data[field], str):
                original = corrected_data[field]
                corrected_data[field] = original.strip()
                if original != corrected_data[field]:
                    corrections_applied.append(f"Trimmed whitespace from {field}")
        
        # Apply currency normalization
        if "currency" in corrected_data:
            currency_mapping = rules.get("normalize_currency", {}).get("mappings", {})
            original = corrected_data["currency"]
            if isinstance(original, str):
                normalized = currency_mapping.get(original.lower(), original)
                if normalized != original:
                    corrected_data["currency"] = normalized
                    corrections_applied.append(f"Normalized currency: {original} → {normalized}")
        
        # Format registration numbers
        reg_fields = ["supplier_registration_number", "recipient_registration_number"]
        for field in reg_fields:
            if field in corrected_data and corrected_data[field]:
                original = str(corrected_data[field])
                # Remove non-numeric characters for Latvian reg numbers
                numeric_only = ''.join(c for c in original if c.isdigit())
                if len(numeric_only) == 11:  # Standard Latvian reg number length
                    corrected_data[field] = numeric_only
                    if numeric_only != original:
                        corrections_applied.append(f"Formatted {field}: {original} → {numeric_only}")
        
        # Convert back to original format
        if format_type == "db":
            final_data = self.convert_to_db_format(corrected_data)
        else:
            final_data = corrected_data
        
        final_data["_corrections_applied"] = corrections_applied
        return final_data
    
    def _validate_english_field(self, field_name: str, value: Any, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate single field using English template rules"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Required check
        if rules.get("required", False) and (value is None or value == ""):
            result["valid"] = False
            result["errors"].append(f"Required field {field_name} is missing")
            return result
        
        if value is None or value == "":
            return result
        
        # String validations
        if isinstance(value, str):
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
    
    def _validate_cross_fields_en(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cross-field validations for English template"""
        result = {"errors": [], "warnings": []}
        
        try:
            # VAT calculation check
            subtotal = float(data.get("subtotal_amount", 0) or 0)
            vat = float(data.get("vat_amount", 0) or 0)
            total = float(data.get("total_amount", 0) or 0)
            
            expected_total = subtotal + vat
            if abs(total - expected_total) > 0.01:
                result["warnings"].append(f"VAT calculation mismatch: {total} ≠ {subtotal} + {vat}")
        
        except (ValueError, TypeError):
            pass
        
        return result
    
    def get_english_field_suggestions(self, field_name: str, partial_value: str = "") -> List[str]:
        """Get field suggestions for autocomplete using English template"""
        suggestions = []
        
        # Get field info
        field_info = self.get_english_field_info(field_name)
        if not field_info:
            return suggestions
        
        # Add example values if available
        if "examples" in field_info:
            for example in field_info["examples"]:
                if partial_value.lower() in example.lower():
                    suggestions.append(example)
        
        # Add common values based on field type
        if field_name == "currency":
            currencies = ["EUR", "USD", "GBP", "CHF"]
            suggestions.extend([c for c in currencies if partial_value.upper() in c])
        elif field_name == "payment_method":
            methods = ["Bank transfer", "Cash", "Card", "Check"]
            suggestions.extend([m for m in methods if partial_value.lower() in m.lower()])
        
        return suggestions[:10]  # Limit to 10 suggestions

# Globālā instance
template_config_service = TemplateConfigService()
