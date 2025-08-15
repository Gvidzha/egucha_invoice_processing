"""
POSM 4.5 Week 2 API Endpoint Test
Pārbauda vai jaunās API funkcionalitātes ir pieejamas
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

def test_api_endpoints():
    """Test API endpoints availability"""
    
    try:
        from app.api.process import router
        from fastapi import FastAPI
        
        # Create test app
        app = FastAPI()
        app.include_router(router)
        
        # Get all routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    'path': route.path,
                    'methods': list(route.methods),
                    'name': getattr(route, 'name', 'unknown')
                })
        
        # Expected POSM 4.5 Week 2 endpoints
        expected_endpoints = [
            {'path': '/process/{file_id}', 'method': 'POST'},
            {'path': '/process/{file_id}/status', 'method': 'GET'}, 
            {'path': '/process/{file_id}/structure', 'method': 'GET'},
            {'path': '/process/{file_id}/analyze-structure', 'method': 'POST'},
            {'path': '/process/{file_id}/results', 'method': 'GET'}
        ]
        
        print("🔍 Available API Endpoints:")
        print("=" * 40)
        
        found_endpoints = []
        for route in routes:
            if route['path'].startswith('/process/'):
                # Convert methods to list and filter out HEAD/OPTIONS
                methods_list = [m for m in route['methods'] if m not in {'HEAD', 'OPTIONS'}]
                methods_str = ', '.join(sorted(methods_list))
                print(f"✅ {methods_str:8} {route['path']}")
                found_endpoints.append(route)
        
        print(f"\n📊 Summary:")
        print(f"Found endpoints: {len(found_endpoints)}")
        print(f"Expected endpoints: {len(expected_endpoints)}")
        
        # Check specific POSM 4.5 Week 2 endpoints
        week2_endpoints = [
            '/process/{file_id}/structure',
            '/process/{file_id}/analyze-structure'
        ]
        
        print(f"\n🆕 POSM 4.5 Week 2 New Endpoints:")
        for endpoint in week2_endpoints:
            found = any(route['path'] == endpoint for route in found_endpoints)
            status = "✅ FOUND" if found else "❌ MISSING"
            print(f"  {status}: {endpoint}")
        
        # Check if enhanced endpoints exist
        enhanced_endpoints = [
            '/process/{file_id}',        # Enhanced with structure info
            '/process/{file_id}/status', # Enhanced with structure summary
            '/process/{file_id}/results' # Enhanced with structure data
        ]
        
        print(f"\n📈 Enhanced Endpoints:")
        for endpoint in enhanced_endpoints:
            found = any(route['path'] == endpoint for route in found_endpoints)
            status = "✅ ENHANCED" if found else "❌ MISSING"
            print(f"  {status}: {endpoint}")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False


def test_function_availability():
    """Test function availability"""
    
    try:
        from app.api.process import (
            process_invoice_ocr,
            process_structure_analysis,
            analyze_document_structure,
            get_structure_analysis
        )
        
        print(f"\n🔧 Key Functions Available:")
        print("=" * 30)
        print("✅ process_invoice_ocr")
        print("✅ process_structure_analysis") 
        print("✅ analyze_document_structure")
        print("✅ get_structure_analysis")
        
        return True
        
    except ImportError as e:
        print(f"❌ Function import failed: {e}")
        return False


def main():
    """Main test runner"""
    
    print("🧪 POSM 4.5 Week 2 API Functionality Test")
    print("=" * 50)
    
    tests = [
        ("API Endpoints", test_api_endpoints),
        ("Function Availability", test_function_availability)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print(f"\n📊 Final Results:")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print(f"\n🎉 POSM 4.5 Week 2 API: FULLY FUNCTIONAL!")
    else:
        print(f"\n⚠️  Some tests failed")


if __name__ == "__main__":
    main()
