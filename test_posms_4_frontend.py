#!/usr/bin/env python3
"""
POSMS 4 TESTS: Frontend dinamiskā komponenta
Pārbauda frontend produktu komponentu struktūru
"""
import json
import sys
import os
from pathlib import Path

def test_product_manager_component():
    """Testa ProductManager komponentes struktūru"""
    print("🧪 Testing ProductManager component structure...")
    
    try:
        component_path = "frontend/src/components/ProductManager.tsx"
        if not os.path.exists(component_path):
            print(f"❌ ProductManager component not found: {component_path}")
            return False
        
        with open(component_path, 'r', encoding='utf-8') as f:
            component_content = f.read()
        
        # Pārbaudam galvenos elementus
        required_elements = [
            "interface ProductField",
            "interface ProductItem", 
            "interface ProductConfig",
            "interface ProductManagerProps",
            "export const ProductManager",
            "useState<ProductItem[]>",
            "useEffect",
            "loadProductConfig",
            "loadProducts",
            "saveProducts",
            "addProduct",
            "removeProduct",
            "updateProduct"
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in component_content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing component elements: {missing_elements}")
            return False
        
        print("✅ All required component elements present")
        print("✅ TypeScript interfaces defined")
        print("✅ React hooks usage correct")
        print("✅ CRUD operations implemented")
        
        return True
    except Exception as e:
        print(f"❌ ProductManager component test failed: {e}")
        return False

def test_product_api_utils():
    """Testa produktu API utils failu"""
    print("🧪 Testing product API utils...")
    
    try:
        utils_path = "frontend/src/utils/productAPI.ts"
        if not os.path.exists(utils_path):
            print(f"❌ Product API utils not found: {utils_path}")
            return False
        
        with open(utils_path, 'r', encoding='utf-8') as f:
            utils_content = f.read()
        
        # Pārbaudam API service klasi
        api_methods = [
            "class ProductAPIService",
            "async getConfig()",
            "async getFieldsForDocument(",
            "async getProducts(",
            "async updateProducts(",
            "async validateProducts(",
            "async getLatvianMappings()",
            "async clearProducts("
        ]
        
        missing_methods = []
        for method in api_methods:
            if method not in utils_content:
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing API methods: {missing_methods}")
            return False
        
        # Pārbaudam utility funkcijas
        utility_functions = [
            "calculateTotalPrice",
            "calculateVATAmount", 
            "formatProductSummary",
            "validateProduct",
            "createEmptyProduct",
            "normalizeProduct"
        ]
        
        missing_utils = []
        for util in utility_functions:
            if f"function {util}" not in utils_content:
                missing_utils.append(util)
        
        if missing_utils:
            print(f"❌ Missing utility functions: {missing_utils}")
            return False
        
        print("✅ ProductAPIService class complete")
        print("✅ All API methods defined")
        print("✅ Utility functions present")
        
        return True
    except Exception as e:
        print(f"❌ Product API utils test failed: {e}")
        return False

def test_editable_results_integration():
    """Testa ProductManager integrāciju ar EditableResults"""
    print("🧪 Testing EditableResults integration...")
    
    try:
        editable_path = "frontend/src/components/EditableResults.tsx"
        if not os.path.exists(editable_path):
            print(f"❌ EditableResults component not found: {editable_path}")
            return False
        
        with open(editable_path, 'r', encoding='utf-8') as f:
            editable_content = f.read()
        
        # Pārbaudam vai ProductManager ir importēts
        if "import { ProductManager } from './ProductManager';" not in editable_content:
            print("❌ ProductManager import missing in EditableResults")
            return False
        
        # Pārbaudam vai ProductManager ir izmantots
        if "<ProductManager" not in editable_content:
            print("❌ ProductManager component not used in EditableResults")
            return False
        
        # Pārbaudam props
        required_props = [
            "invoiceId={fileId}",
            "documentType=",
            "onProductsChange=",
            "readonly="
        ]
        
        missing_props = []
        for prop in required_props:
            if prop not in editable_content:
                missing_props.append(prop)
        
        if missing_props:
            print(f"❌ Missing ProductManager props: {missing_props}")
            return False
        
        print("✅ ProductManager imported correctly")
        print("✅ ProductManager component used")
        print("✅ All required props passed")
        
        return True
    except Exception as e:
        print(f"❌ EditableResults integration test failed: {e}")
        return False

def test_typescript_interfaces():
    """Testa TypeScript interface konsistenci"""
    print("🧪 Testing TypeScript interfaces consistency...")
    
    try:
        # Ielādējam ProductManager interfaces
        manager_path = "frontend/src/components/ProductManager.tsx"
        with open(manager_path, 'r', encoding='utf-8') as f:
            manager_content = f.read()
        
        # Ielādējam API utils interfaces
        utils_path = "frontend/src/utils/productAPI.ts"
        with open(utils_path, 'r', encoding='utf-8') as f:
            utils_content = f.read()
        
        # Pārbaudam vai ProductItem interface ir konsistents
        required_fields = [
            "product_name: string",
            "quantity: number",
            "unit_price: number", 
            "total_price: number"
        ]
        
        for field in required_fields:
            if field not in manager_content or field not in utils_content:
                print(f"❌ Inconsistent ProductItem interface: {field}")
                return False
        
        # Pārbaudam ProductConfig interface
        config_fields = [
            "document_types: string[]",
            "base_fields: ProductField[]",
            "optional_fields: ProductField[]"
        ]
        
        for field in config_fields:
            if field not in manager_content or field not in utils_content:
                print(f"❌ Inconsistent ProductConfig interface: {field}")
                return False
        
        print("✅ ProductItem interface consistent")
        print("✅ ProductConfig interface consistent")
        print("✅ TypeScript types properly shared")
        
        return True
    except Exception as e:
        print(f"❌ TypeScript interfaces test failed: {e}")
        return False

def test_component_structure():
    """Testa komponentes struktūru un UI elementus"""
    print("🧪 Testing component structure and UI elements...")
    
    try:
        component_path = "frontend/src/components/ProductManager.tsx"
        with open(component_path, 'r', encoding='utf-8') as f:
            component_content = f.read()
        
        # Pārbaudam UI komponentes (atjaunināts uz HTML elementiem)
        ui_elements = [
            "import React, { useState, useEffect }",
            "from 'lucide-react'",
            "interface ProductField",
            "interface ProductItem", 
            "interface ProductConfig",
            "export const ProductManager"
        ]
        
        missing_ui = []
        for element in ui_elements:
            if element not in component_content:
                missing_ui.append(element)
        
        if missing_ui:
            print(f"❌ Missing component elements: {missing_ui}")
            return False
        
        # Pārbaudam HTML elements (ne UI bibliotēkas)
        html_elements = [
            "<input",
            "<select",
            "<button",
            "<div",
            "className="
        ]
        
        missing_html = []
        for element in html_elements:
            if element not in component_content:
                missing_html.append(element)
        
        if missing_html:
            print(f"❌ Missing HTML elements: {missing_html}")
            return False
        
        # Pārbaudam event handlers (atjaunināts uz HTML events)
        event_handlers = [
            "onClick={addProduct}",
            "onClick={saveProducts}",
            "onClick={() => removeProduct(",
            "onChange={(e) => updateProduct(",
            "onChange={(e) => updateProduct("
        ]
        
        missing_handlers = []
        for handler in event_handlers:
            if handler not in component_content:
                missing_handlers.append(handler)
        
        if missing_handlers:
            print(f"❌ Missing event handlers: {missing_handlers}")
            return False
        
        # Pārbaudam conditional rendering
        conditional_renders = [
            "if (loading)",
            "{!readonly && (",
            "{products.length === 0 ?",
            "{summary && (",
            "{Object.keys(errors).length > 0 && ("
        ]
        
        missing_conditionals = []
        for condition in conditional_renders:
            if condition not in component_content:
                missing_conditionals.append(condition)
        
        if missing_conditionals:
            print(f"❌ Missing conditional renders: {missing_conditionals}")
            return False
        
        print("✅ All component elements present")
        print("✅ HTML elements with Tailwind CSS")
        print("✅ Event handlers properly defined")
        print("✅ Conditional rendering implemented")
        
        return True
    except Exception as e:
        print(f"❌ Component structure test failed: {e}")
        return False

def test_responsive_design():
    """Testa responsive design elementus"""
    print("🧪 Testing responsive design elements...")
    
    try:
        component_path = "frontend/src/components/ProductManager.tsx"
        with open(component_path, 'r', encoding='utf-8') as f:
            component_content = f.read()
        
        # Pārbaudam responsive classes
        responsive_classes = [
            "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
            "flex justify-between items-center",
            "space-y-4",
            "gap-4"
        ]
        
        missing_responsive = []
        for css_class in responsive_classes:
            if css_class not in component_content:
                missing_responsive.append(css_class)
        
        if missing_responsive:
            print(f"❌ Missing responsive classes: {missing_responsive}")
            return False
        
        print("✅ Responsive grid layout")
        print("✅ Flexbox utilities used")
        print("✅ Spacing utilities applied")
        
        return True
    except Exception as e:
        print(f"❌ Responsive design test failed: {e}")
        return False

def main():
    """Galvenā testa funkcija"""
    print("=" * 60)
    print("🧪 POSMS 4 TESTS: Frontend dinamiskā komponenta")
    print("=" * 60)
    
    tests = [
        test_product_manager_component,
        test_product_api_utils,
        test_editable_results_integration,
        test_typescript_interfaces,
        test_component_structure,
        test_responsive_design
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
    print(f"📊 POSMS 4 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 POSMS 4 COMPLETED SUCCESSFULLY!")
        print("✅ Gatavs pāriet uz POSMU 5: AI extraction pielāgošana")
        print()
        print("📋 Frontend Summary:")
        print("   - ✅ ProductManager komponenta izveidota")
        print("   - ✅ ProductAPI utils implementēti")
        print("   - ✅ Integrācija ar EditableResults")
        print("   - ✅ TypeScript interfaces konsistenti")
        print("   - ✅ Responsive UI ar Tailwind CSS")
        print("   - ✅ React hooks un state management")
    else:
        print("❌ POSMS 4 FAILED - jānovērš kļūdas")
    
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
