"""
Product utilities - Helper functions for product data processing
"""
import json
from typing import Dict, List, Any, Optional
from .product_template_service import ProductTemplateManager

class ProductDataProcessor:
    """Apstrādā produktu datus dažādos formātos"""
    
    def __init__(self):
        self.template_manager = ProductTemplateManager()
    
    def normalize_products(self, products: List[Dict[str, Any]], document_type: str) -> List[Dict[str, Any]]:
        """Normalizē produktu datus pret template"""
        normalized = []
        valid_fields = {f['name']: f for f in self.template_manager.get_fields_for_document(document_type)}
        
        for product in products:
            normalized_product = {}
            
            # Normalizējam katru lauku
            for key, value in product.items():
                if key in valid_fields:
                    field_def = valid_fields[key]
                    normalized_value = self._normalize_field_value(value, field_def['type'])
                    if normalized_value is not None:
                        normalized_product[key] = normalized_value
            
            # Pievienojam default vērtības required laukiem
            for field in self.template_manager.get_base_fields():
                if field['required'] and field['name'] not in normalized_product:
                    normalized_product[field['name']] = self._get_default_value(field['type'])
            
            normalized.append(normalized_product)
        
        return normalized
    
    def _normalize_field_value(self, value: Any, field_type: str) -> Any:
        """Normalizē lauka vērtību"""
        if value is None or value == "":
            return None
        
        try:
            if field_type == "number":
                # Mēģinām konvertēt uz number
                if isinstance(value, str):
                    # Noņemam valūtas simbolus un atstarpes
                    clean_value = value.replace('€', '').replace('$', '').replace(' ', '').replace(',', '.')
                    return float(clean_value)
                return float(value)
            elif field_type == "string":
                return str(value).strip()
            elif field_type == "boolean":
                if isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes', 'jā']
                return bool(value)
        except:
            return None
        
        return value
    
    def _get_default_value(self, field_type: str) -> Any:
        """Atgriež default vērtību tipam"""
        defaults = {
            "string": "",
            "number": 0.0,
            "boolean": False
        }
        return defaults.get(field_type, None)
    
    def products_to_json(self, products: List[Dict[str, Any]], schema_version: str = "1.0") -> str:
        """Konvertē produktus uz JSON string"""
        data = {
            "schema_version": schema_version,
            "products": products,
            "total_products": len(products),
            "generated_at": self._get_timestamp()
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def products_from_json(self, json_string: str) -> Dict[str, Any]:
        """Ielādē produktus no JSON string"""
        try:
            data = json.loads(json_string)
            return {
                "products": data.get("products", []),
                "schema_version": data.get("schema_version", "1.0"),
                "total_products": data.get("total_products", 0),
                "generated_at": data.get("generated_at", None)
            }
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    def create_product_summary(self, products: List[Dict[str, Any]]) -> str:
        """Izveido vienkāršu produktu kopsavilkumu"""
        if not products:
            return "Nav produktu"
        
        total_items = len(products)
        total_amount = 0.0
        
        items_summary = []
        for product in products:
            name = product.get('product_name', 'Nezināms produkts')
            quantity = product.get('quantity', 0)
            unit = product.get('unit', 'gab.')
            total_price = product.get('total_price', 0)
            
            if isinstance(total_price, (int, float)):
                total_amount += total_price
            
            items_summary.append(f"{name} ({quantity} {unit})")
        
        summary_parts = [
            f"Produkti: {total_items}",
            f"Kopsumma: {total_amount:.2f}",
            "Saraksts: " + ", ".join(items_summary[:3])
        ]
        
        if len(items_summary) > 3:
            summary_parts.append(f"un vēl {len(items_summary) - 3}")
        
        return " | ".join(summary_parts)
    
    def _get_timestamp(self) -> str:
        """Atgriež pašreizējo timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

# Utility functions
def get_product_template_manager() -> ProductTemplateManager:
    """Factory function lai iegūtu ProductTemplateManager"""
    return ProductTemplateManager()

def validate_products(products: List[Dict[str, Any]], document_type: str) -> Dict[str, List[str]]:
    """Ātra produktu validācija"""
    manager = ProductTemplateManager()
    
    all_errors = {"missing_required": [], "invalid_types": [], "unknown_fields": []}
    
    for i, product in enumerate(products):
        errors = manager.validate_product_data(product, document_type)
        
        # Pievienojam produkta numuru pie kļūdām
        for error_type, error_list in errors.items():
            for error in error_list:
                all_errors[error_type].append(f"Product {i+1}: {error}")
    
    return all_errors
