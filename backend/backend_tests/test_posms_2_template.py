#!/usr/bin/env python3
"""
POSMS 2 TESTS: Template konfigurācija produktiem
Pārbauda produktu template sistēmas funkcionalitāti
"""
import json
import sys
import os
from pathlib import Path

# Pievienojam backend ceļu
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_product_template_manager_import():
    """Testa ProductTemplateManager importu"""
    print("🧪 Testing ProductTemplateManager import...")
    
    try:
        from app.services.product_template_service import ProductTemplateManager
        manager = ProductTemplateManager()
        print("✅ ProductTemplateManager imported and initialized")
        return True
    except Exception as e:
        print(f"❌ ProductTemplateManager import failed: {e}")
        return False

def test_document_specific_fields():
    """Testa document-specific lauku sistēmu"""
    print("🧪 Testing document-specific fields...")
    
    try:
        from app.services.product_template_service import ProductTemplateManager
        manager = ProductTemplateManager()
        
        # Testējam dažādus dokumentu tipus
        invoice_fields = manager.get_fields_for_document("invoice")
        receipt_fields = manager.get_fields_for_document("receipt")
        delivery_fields = manager.get_fields_for_document("delivery_note")
        
        # Base lauki ir visos dokumentos
        base_count = len(manager.get_base_fields())
        
        if len(invoice_fields) < base_count:
            print(f"❌ Invoice should have at least {base_count} fields")
            return False
        
        print(f"✅ Invoice fields: {len(invoice_fields)}")
        print(f"✅ Receipt fields: {len(receipt_fields)}")
        print(f"✅ Delivery fields: {len(delivery_fields)}")
        
        # Pārbaudam vai document-specific lauki ir atšķirīgi
        invoice_specific = manager.get_document_specific_fields("invoice")
        receipt_specific = manager.get_document_specific_fields("receipt")
        
        if len(invoice_specific) == 0 or len(receipt_specific) == 0:
            print("❌ Document-specific fields should exist")
            return False
        
        print(f"✅ Invoice-specific: {len(invoice_specific)} fields")
        print(f"✅ Receipt-specific: {len(receipt_specific)} fields")
        
        return True
    except Exception as e:
        print(f"❌ Document-specific fields test failed: {e}")
        return False

def test_product_validation():
    """Testa produktu datu validāciju"""
    print("🧪 Testing product data validation...")
    
    try:
        from app.services.product_template_service import ProductTemplateManager
        manager = ProductTemplateManager()
        
        # Valid produkts
        valid_product = {
            "product_name": "Test produkts",
            "quantity": 5,
            "unit_price": 10.50,
            "total_price": 52.50
        }
        
        # Invalid produkts (trūkst required lauku)
        invalid_product = {
            "product_name": "Invalid produkts"
            # trūkst quantity, unit_price, total_price
        }
        
        # Testējam validāciju
        valid_errors = manager.validate_product_data(valid_product, "invoice")
        invalid_errors = manager.validate_product_data(invalid_product, "invoice")
        
        # Valid produktam nevajadzētu būt kļūdām
        total_valid_errors = sum(len(errors) for errors in valid_errors.values())
        if total_valid_errors > 0:
            print(f"❌ Valid product has errors: {valid_errors}")
            return False
        
        # Invalid produktam vajadzētu būt kļūdām
        total_invalid_errors = sum(len(errors) for errors in invalid_errors.values())
        if total_invalid_errors == 0:
            print("❌ Invalid product should have errors")
            return False
        
        print(f"✅ Valid product: 0 errors")
        print(f"✅ Invalid product: {total_invalid_errors} errors")
        print(f"   Missing: {invalid_errors['missing_required']}")
        
        return True
    except Exception as e:
        print(f"❌ Product validation test failed: {e}")
        return False

def test_product_data_processor():
    """Testa ProductDataProcessor funkcionalitāti"""
    print("🧪 Testing ProductDataProcessor...")
    
    try:
        from app.services.product_utils import ProductDataProcessor
        processor = ProductDataProcessor()
        
        # Test produkti
        test_products = [
            {
                "product_name": "Produkts 1",
                "quantity": "5",  # String, vajadzētu konvertēt uz number
                "unit_price": "10.50",
                "total_price": "52.50",
                "unit": "gab."
            },
            {
                "product_name": "Produkts 2", 
                "quantity": 3,
                "unit_price": 15.0,
                "total_price": 45.0
            }
        ]
        
        # Normalizējam produktus
        normalized = processor.normalize_products(test_products, "invoice")
        
        if len(normalized) != 2:
            print(f"❌ Expected 2 products, got {len(normalized)}")
            return False
        
        # Pārbaudam vai string numbers tika konvertēti
        first_product = normalized[0]
        if not isinstance(first_product.get('quantity'), (int, float)):
            print(f"❌ Quantity should be number, got {type(first_product.get('quantity'))}")
            return False
        
        print(f"✅ Normalized {len(normalized)} products")
        print(f"✅ String numbers converted to floats")
        
        # Testējam JSON konversiju
        json_string = processor.products_to_json(normalized)
        parsed_data = processor.products_from_json(json_string)
        
        if len(parsed_data['products']) != 2:
            print("❌ JSON round-trip failed")
            return False
        
        print("✅ JSON serialization/deserialization works")
        
        # Testējam summary
        summary = processor.create_product_summary(normalized)
        if "Produkti: 2" not in summary:
            print(f"❌ Summary should contain 'Produkti: 2', got: {summary}")
            return False
        
        print(f"✅ Product summary: {summary[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ ProductDataProcessor test failed: {e}")
        return False

def test_latvian_mappings():
    """Testa Latvian → English mappings produktu laukiem"""
    print("🧪 Testing Latvian mappings for products...")
    
    try:
        from app.services.product_template_service import ProductTemplateManager
        manager = ProductTemplateManager()
        
        mappings = manager.get_latvian_mappings()
        
        # Pārbaudam vai ir pamatmappings
        expected_mappings = {
            'produkta_nosaukums': 'product_name',
            'daudzums': 'quantity',
            'vienibas_cena': 'unit_price',
            'kopsumma': 'total_price'
        }
        
        for latvian, english in expected_mappings.items():
            if latvian not in mappings:
                print(f"❌ Missing Latvian mapping: {latvian}")
                return False
            if mappings[latvian] != english:
                print(f"❌ Wrong mapping: {latvian} -> {mappings[latvian]}, expected {english}")
                return False
        
        print(f"✅ Latvian mappings: {len(mappings)} total")
        print(f"✅ Core mappings verified")
        
        return True
    except Exception as e:
        print(f"❌ Latvian mappings test failed: {e}")
        return False

def main():
    """Galvenā testa funkcija"""
    print("=" * 60)
    print("🧪 POSMS 2 TESTS: Template konfigurācija produktiem")
    print("=" * 60)
    
    tests = [
        test_product_template_manager_import,
        test_document_specific_fields,
        test_product_validation,
        test_product_data_processor,
        test_latvian_mappings
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            print()
    
    print("=" * 60)
    print(f"📊 POSMS 2 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 POSMS 2 COMPLETED SUCCESSFULLY!")
        print("✅ Gatavs pāriet uz POSMU 3: Backend API")
    else:
        print("❌ POSMS 2 FAILED - jānovērš kļūdas")
    
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
