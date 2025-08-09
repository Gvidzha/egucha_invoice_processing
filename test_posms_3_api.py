#!/usr/bin/env python3
"""
POSMS 3 TESTS: Backend API produktu apstrādei
Pārbauda produktu API endpoints un funkcionalitāti
"""
import json
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Pievienojam backend ceļu
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_products_api_import():
    """Testa produktu API importu"""
    print("🧪 Testing products API import...")
    
    try:
        from app.api.products import router, ProductItem, ProductsUpdateRequest
        print("✅ Products API imported successfully")
        print(f"✅ Router prefix: {router.prefix}")
        print(f"✅ Router tags: {router.tags}")
        return True
    except Exception as e:
        print(f"❌ Products API import failed: {e}")
        return False

def test_pydantic_models():
    """Testa Pydantic modeļu struktūru"""
    print("🧪 Testing Pydantic models...")
    
    try:
        from app.api.products import ProductItem, ProductsUpdateRequest, ProductsResponse
        
        # Testējam ProductItem model
        test_product = ProductItem(
            product_name="Test produkts",
            quantity=5.0,
            unit_price=10.50,
            total_price=52.50,
            unit="gab."
        )
        
        if test_product.product_name != "Test produkts":
            print("❌ ProductItem model validation failed")
            return False
        
        print("✅ ProductItem model works")
        
        # Testējam ProductsUpdateRequest
        test_request = ProductsUpdateRequest(
            invoice_id=1,
            products=[test_product],
            document_type="invoice"
        )
        
        if len(test_request.products) != 1:
            print("❌ ProductsUpdateRequest model validation failed")
            return False
        
        print("✅ ProductsUpdateRequest model works")
        print("✅ ProductsResponse model exists")
        
        return True
    except Exception as e:
        print(f"❌ Pydantic models test failed: {e}")
        return False

def test_api_endpoints_structure():
    """Testa API endpoint struktūru"""
    print("🧪 Testing API endpoints structure...")
    
    try:
        from app.api.products import router
        
        # Pārbaudam vai ir nepieciešamie endpoints
        expected_paths = [
            "/config",
            "/fields/{document_type}",
            "/schema/{document_type}",
            "/{invoice_id}",
            "/update",
            "/validate",
            "/mappings/latvian",
            "/{invoice_id}",  # DELETE
            "/debug/{invoice_id}/raw"
        ]
        
        # Iegūstam router paths
        router_paths = []
        for route in router.routes:
            if hasattr(route, 'path'):
                router_paths.append(route.path)
        
        print(f"✅ Found {len(router_paths)} API routes")
        
        # Pārbaudam vai ir galvenie endpoints
        key_endpoints = ["/config", "/update", "/validate"]
        for endpoint in key_endpoints:
            if not any(endpoint in path for path in router_paths):
                print(f"❌ Missing key endpoint: {endpoint}")
                return False
        
        print("✅ Key endpoints present")
        print("✅ Router structure valid")
        
        return True
    except Exception as e:
        print(f"❌ API endpoints structure test failed: {e}")
        return False

def test_product_services_integration():
    """Testa produktu servisu integrāciju ar API"""
    print("🧪 Testing product services integration...")
    
    try:
        # Importējam nepieciešamos servisus
        from app.services.product_template_service import ProductTemplateManager
        from app.services.product_utils import ProductDataProcessor, validate_products
        
        # Testējam integrāciju
        manager = ProductTemplateManager()
        processor = ProductDataProcessor()
        
        # Test produkti
        test_products = [
            {
                "product_name": "Test produkts",
                "quantity": 2,
                "unit_price": 15.0,
                "total_price": 30.0
            }
        ]
        
        # Testējam validāciju
        errors = validate_products(test_products, "invoice")
        if any(errors.values()):
            print(f"❌ Validation should pass for valid products: {errors}")
            return False
        
        # Testējam normalizāciju
        normalized = processor.normalize_products(test_products, "invoice")
        if len(normalized) != 1:
            print("❌ Normalization failed")
            return False
        
        # Testējam JSON konversiju
        json_string = processor.products_to_json(normalized)
        parsed = processor.products_from_json(json_string)
        if len(parsed['products']) != 1:
            print("❌ JSON conversion failed")
            return False
        
        print("✅ Product services integration works")
        print("✅ Validation, normalization, JSON conversion OK")
        
        return True
    except Exception as e:
        print(f"❌ Product services integration test failed: {e}")
        return False

def test_api_mock_responses():
    """Testa API response struktūru ar mock datiem"""
    print("🧪 Testing API mock responses...")
    
    try:
        from app.api.products import ProductsResponse, ProductConfigResponse
        
        # Mock ProductsResponse
        mock_response = ProductsResponse(
            success=True,
            message="Test message",
            products=[{"product_name": "Test", "quantity": 1}],
            total_products=1,
            summary="Test summary"
        )
        
        if not mock_response.success:
            print("❌ ProductsResponse mock failed")
            return False
        
        # Mock ProductConfigResponse
        mock_config = ProductConfigResponse(
            document_types=["invoice", "receipt"],
            base_fields=[{"name": "product_name", "type": "string"}],
            optional_fields=[],
            document_specific_fields={}
        )
        
        if len(mock_config.document_types) != 2:
            print("❌ ProductConfigResponse mock failed")
            return False
        
        print("✅ ProductsResponse mock works")
        print("✅ ProductConfigResponse mock works")
        print("✅ API response structures valid")
        
        return True
    except Exception as e:
        print(f"❌ API mock responses test failed: {e}")
        return False

def test_error_handling():
    """Testa API error handling loģiku"""
    print("🧪 Testing API error handling...")
    
    try:
        from app.services.product_utils import validate_products
        
        # Testējam ar invalid datiem
        invalid_products = [
            {
                "product_name": "Invalid",
                # trūkst obligātie lauki
            }
        ]
        
        errors = validate_products(invalid_products, "invoice")
        
        # Vajadzētu būt kļūdām
        if not any(errors.values()):
            print("❌ Error handling should detect missing fields")
            return False
        
        # Testējam ar nezināmu document tipu
        try:
            from app.services.product_template_service import ProductTemplateManager
            manager = ProductTemplateManager()
            fields = manager.get_fields_for_document("unknown_type")
            # Šim vajadzētu atgriezt tikai base+optional laukus
            if len(fields) < 5:  # base fields count
                print("❌ Unknown document type handling failed")
                return False
        except:
            pass  # Ir OK ja met exception
        
        print("✅ Error detection works")
        print("✅ Invalid data handling OK")
        
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Galvenā testa funkcija"""
    print("=" * 60)
    print("🧪 POSMS 3 TESTS: Backend API produktu apstrādei")
    print("=" * 60)
    
    tests = [
        test_products_api_import,
        test_pydantic_models,
        test_api_endpoints_structure,
        test_product_services_integration,
        test_api_mock_responses,
        test_error_handling
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
    print(f"📊 POSMS 3 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 POSMS 3 COMPLETED SUCCESSFULLY!")
        print("✅ Gatavs pāriet uz POSMU 4: Frontend dinamiskā komponenta")
    else:
        print("❌ POSMS 3 FAILED - jānovērš kļūdas")
    
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
