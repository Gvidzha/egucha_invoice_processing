#!/usr/bin/env python3
"""
POSMS 1 TESTS: Datubāzes JSON struktūra
Pārbauda produktu sistēmas datubāzes konfigurāciju
"""
import json
import sys
import os
from pathlib import Path

# Pievienojam backend ceļu
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_product_config_structure():
    """Testa produktu konfigurācijas faila struktūru"""
    print("🧪 Testing product configuration structure...")
    
    config_path = "backend/config/schemas/product_config.json"
    
    # Pārbaudam vai fails eksistē
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        return False
    
    # Ielādējam konfigurāciju
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False
    
    # Pārbaudam galveno struktūru
    required_keys = ['product_fields']
    for key in required_keys:
        if key not in config:
            print(f"❌ Missing key: {key}")
            return False
    
    product_fields = config['product_fields']
    required_sections = ['version', 'base_fields', 'optional_fields', 'document_specific', 'extraction_patterns']
    
    for section in required_sections:
        if section not in product_fields:
            print(f"❌ Missing section: {section}")
            return False
    
    print(f"✅ Config structure valid")
    print(f"   - Version: {product_fields['version']}")
    print(f"   - Base fields: {len(product_fields['base_fields'])}")
    print(f"   - Optional fields: {len(product_fields['optional_fields'])}")
    print(f"   - Document types: {list(product_fields['document_specific'].keys())}")
    
    return True

def test_database_model_import():
    """Testa datubāzes modeļa struktūru bez konekcijas"""
    print("🧪 Testing database model structure...")
    
    try:
        # Lasām model failu tieši
        model_path = "backend/app/models/invoice.py"
        with open(model_path, 'r', encoding='utf-8') as f:
            model_content = f.read()
        
        # Pārbaudam vai produktu lauki eksistē
        required_product_fields = [
            'product_items = Column(Text)',
            'product_summary = Column(Text)', 
            'product_schema_version = Column(String(10), default="1.0")'
        ]
        
        all_found = True
        for field in required_product_fields:
            if field not in model_content:
                print(f"❌ Missing product field: {field}")
                all_found = False
            else:
                field_name = field.split(' = ')[0]
                print(f"✅ {field_name} field exists")
        
        # Pārbaudam vai vecie produktu lauki ir izņemti  
        old_product_fields = ['product_type = Column(String(100))']
        for field in old_product_fields:
            if field in model_content:
                print(f"❌ Old product field still exists: {field}")
                all_found = False
            else:
                print("✅ Old product_type field removed")
        
        return all_found
    except Exception as e:
        print(f"❌ Database model structure test failed: {e}")
        return False

def test_field_mappings_consistency():
    """Testa lauku mapping konsistenci bez produktu laukiem"""
    print("🧪 Testing field mappings without product fields...")
    
    try:
        with open("backend/config/schemas/field_mappings_en.json", 'r', encoding='utf-8') as f:
            mappings = json.load(f)
        
        en_to_db = mappings['field_mappings']['english_template_to_existing_db']
        db_to_en = mappings['field_mappings']['existing_db_to_english_template']
        latvian_to_en = mappings['field_mappings']['latvian_to_english']
        
        # Pārbaudam vai produktu lauki ir izņemti
        product_fields = ['product_type', 'product_items']
        
        for field in product_fields:
            if field in en_to_db.values():
                print(f"❌ Product field {field} still in en_to_db mapping")
                return False
            if field in db_to_en:
                print(f"❌ Product field {field} still in db_to_en mapping")
                return False
        
        print(f"✅ Product fields removed from mappings")
        print(f"   - EN→DB mappings: {len(en_to_db)}")
        print(f"   - DB→EN mappings: {len(db_to_en)}")
        print(f"   - Latvian→EN mappings: {len(latvian_to_en)}")
        
        return True
    except Exception as e:
        print(f"❌ Field mappings test failed: {e}")
        return False

def test_json_schema_validation():
    """Testa JSON shēmas validāciju produktu konfigurācijai"""
    print("🧪 Testing JSON schema validation...")
    
    try:
        with open("backend/config/schemas/product_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validējam base_fields struktūru
        base_fields = config['product_fields']['base_fields']
        required_field_keys = ['name', 'type', 'required', 'description', 'latvian']
        
        for field in base_fields:
            for key in required_field_keys:
                if key not in field:
                    print(f"❌ Base field missing key {key}: {field}")
                    return False
        
        # Validējam document_specific struktūru
        doc_specific = config['product_fields']['document_specific']
        for doc_type, fields in doc_specific.items():
            if not isinstance(fields, list):
                print(f"❌ Document specific fields must be list for {doc_type}")
                return False
            
            for field in fields:
                for key in required_field_keys:
                    if key not in field:
                        print(f"❌ Document field missing key {key}: {field}")
                        return False
        
        print("✅ JSON schema validation passed")
        return True
    except Exception as e:
        print(f"❌ JSON schema validation failed: {e}")
        return False

def main():
    """Galvenā testa funkcija"""
    print("=" * 60)
    print("🧪 POSMS 1 TESTS: Datubāzes JSON struktūra")
    print("=" * 60)
    
    tests = [
        test_product_config_structure,
        test_database_model_import,
        test_field_mappings_consistency,
        test_json_schema_validation
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
    print(f"📊 POSMS 1 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 POSMS 1 COMPLETED SUCCESSFULLY!")
        print("✅ Gatavs pāriet uz POSMU 2: Template konfigurācija")
    else:
        print("❌ POSMS 1 FAILED - jānovērš kļūdas")
    
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
