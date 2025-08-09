"""
Product Template Manager - Manages dynamic product field configurations
"""
import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

class ProductTemplateManager:
    """Pārvalda produktu template konfigurācijas"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Meklējam config failu no dažādām vietām
            possible_paths = [
                Path(__file__).parent.parent.parent / "backend" / "config" / "schemas" / "product_config.json",
                Path(__file__).parent.parent / "config" / "schemas" / "product_config.json", 
                Path(__file__).parent.parent.parent / "config" / "schemas" / "product_config.json",
                Path("backend/config/schemas/product_config.json"),
                Path("config/schemas/product_config.json")
            ]
            
            config_path = None
            for path in possible_paths:
                if path.exists():
                    config_path = path
                    break
            
            if config_path is None:
                raise FileNotFoundError("product_config.json not found in any expected location")
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Ielādē produktu konfigurāciju"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load product config: {e}")
    
    def get_fields_for_document(self, document_type: str) -> List[Dict[str, Any]]:
        """Atgriež visus laukus konkrētam dokumenta tipam"""
        product_fields = self.config['product_fields']
        
        # Sākam ar base laukiem
        all_fields = product_fields['base_fields'].copy()
        
        # Pievienojam optional laukus
        all_fields.extend(product_fields['optional_fields'])
        
        # Pievienojam document-specific laukus
        if document_type in product_fields['document_specific']:
            all_fields.extend(product_fields['document_specific'][document_type])
        
        return all_fields
    
    def get_base_fields(self) -> List[Dict[str, Any]]:
        """Atgriež tikai base laukus"""
        return self.config['product_fields']['base_fields']
    
    def get_optional_fields(self) -> List[Dict[str, Any]]:
        """Atgriež optional laukus"""
        return self.config['product_fields']['optional_fields']
    
    def get_document_specific_fields(self, document_type: str) -> List[Dict[str, Any]]:
        """Atgriež document-specific laukus"""
        return self.config['product_fields']['document_specific'].get(document_type, [])
    
    def get_extraction_patterns(self) -> Dict[str, List[str]]:
        """Atgriež extraction patterns AI sistēmai"""
        return self.config['product_fields']['extraction_patterns']
    
    def validate_product_data(self, product_data: Dict[str, Any], document_type: str) -> Dict[str, List[str]]:
        """Validē produktu datus pret template"""
        errors = {"missing_required": [], "invalid_types": [], "unknown_fields": []}
        
        required_fields = [f for f in self.get_fields_for_document(document_type) if f['required']]
        valid_fields = {f['name']: f for f in self.get_fields_for_document(document_type)}
        
        # Pārbaudam required laukus
        for field in required_fields:
            if field['name'] not in product_data:
                errors['missing_required'].append(field['name'])
        
        # Pārbaudam tipus un nezināmus laukus
        for key, value in product_data.items():
            if key not in valid_fields:
                errors['unknown_fields'].append(key)
            else:
                field_def = valid_fields[key]
                if not self._validate_field_type(value, field_def['type']):
                    errors['invalid_types'].append(f"{key}: expected {field_def['type']}")
        
        return errors
    
    def _validate_field_type(self, value: Any, expected_type: str) -> bool:
        """Validē lauka tipu"""
        if value is None:
            return True  # None ir valid jebkuram tipam
        
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "number":
            return isinstance(value, (int, float))
        elif expected_type == "boolean":
            return isinstance(value, bool)
        else:
            return True  # Nezināmi tipi pagaidām ir valid
    
    def create_product_schema(self, document_type: str) -> Dict[str, Any]:
        """Izveido JSON shēmu produktu validācijai"""
        fields = self.get_fields_for_document(document_type)
        
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for field in fields:
            schema["properties"][field["name"]] = {
                "type": field["type"],
                "description": field["description"]
            }
            
            if field["required"]:
                schema["required"].append(field["name"])
        
        return schema
    
    def get_latvian_mappings(self) -> Dict[str, str]:
        """Atgriež Latvian → English mappings produktu laukiem"""
        all_fields = []
        all_fields.extend(self.config['product_fields']['base_fields'])
        all_fields.extend(self.config['product_fields']['optional_fields'])
        
        # Pievienojam visus document-specific laukus
        for doc_fields in self.config['product_fields']['document_specific'].values():
            all_fields.extend(doc_fields)
        
        return {field['latvian']: field['name'] for field in all_fields}
    
    def get_supported_document_types(self) -> List[str]:
        """Atgriež visus atbalstītos dokumentu tipus"""
        return list(self.config['product_fields']['document_specific'].keys())
