"""
Testē API process endpoints ar īsti      # 2. Sākt apstrādi
    print(f"\n⚡ 2. Sākam apstrādi (ID: {file_id})...")
    response = requests.post(f"{API_BASE}/api/v1/process/{file_id}")
    
    if response.status_code != 200:
        print(f"❌ Apstrādes sākšana neizdevās: {response.status_code}")
        print(response.text)
        returnākt apstrādi
    print(f"\n⚙️ 2. Sākam apstrādi (ID: {file_id})...")
    response = requests.post(f"{API_BASE}/api/v1/process/{file_id}")failiem
"""
import sys
import os
import asyncio
import requests
import time
import json
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# API bāzes URL
API_BASE = "http://localhost:8000"

def test_upload_and_process():
    """Testē faila upload un apstrādi"""
    
    print("🚀 Testējam API process endpoints")
    print("=" * 50)
    
    # Test fails
    test_file = Path("c:/Code/regex_invoice_processing/uploads/tim_t.jpg")
    if not test_file.exists():
        print(f"❌ Test fails nav atrasts: {test_file}")
        return
    
    # 1. Upload fails
    print("\n📤 1. Augšupielādējam failu...")
    with open(test_file, 'rb') as f:
        files = {'file': ('tim_t.jpg', f, 'image/jpeg')}
        response = requests.post(f"{API_BASE}/api/v1/upload", files=files)
    
    if response.status_code != 200:
        print(f"❌ Upload neizdevās: {response.status_code}")
        print(response.text)
        return
    
    upload_result = response.json()
    file_id = upload_result['file_id']
    print(f"✅ Fails augšupielādēts: ID={file_id}")
    
    # 2. Sākt apstrādi
    print(f"\n⚡ 2. Sākam apstrādi (ID: {file_id})...")
    response = requests.post(f"{API_BASE}/api/v1/process/{file_id}")
    
    if response.status_code != 200:
        print(f"❌ Apstrādes sākšana neizdevās: {response.status_code}")
        print(response.text)
        return
    
    process_result = response.json()
    print(f"✅ Apstrāde sākta: {process_result['message']}")
    
    # 3. Monitorēt statusu
    print(f"\n👀 3. Monitorējam apstrādes statusu...")
    max_wait = 120  # 2 minūtes
    waited = 0
    
    while waited < max_wait:
        response = requests.get(f"{API_BASE}/api/v1/process/{file_id}/status")
        
        if response.status_code != 200:
            print(f"❌ Status pārbaude neizdevās: {response.status_code}")
            break
        
        status_result = response.json()
        status = status_result['status']
        
        print(f"⏳ Statuss: {status} (gaidīts: {waited}s)")
        
        if status == "completed":
            print("🎉 Apstrāde pabeigta!")
            
            # Parādīt rezultātus
            if 'extracted_data' in status_result:
                data = status_result['extracted_data']
                print(f"\n📋 EKSTRAKTĒTIE DATI:")
                print(f"📄 Pavadzīmes Nr: {data.get('invoice_number')}")
                print(f"🏢 Piegādātājs: {data.get('supplier_name')}")
                print(f"📅 Datums: {data.get('invoice_date')}")
                print(f"💰 Summa: {data.get('total_amount')} {data.get('currency')}")
                print(f"💰 PVN: {data.get('vat_amount')} {data.get('currency')}")
                print(f"🔢 Reģ.nr: {data.get('reg_number')}")
                print(f"📊 Confidence: {data.get('confidence_score')}")
            
            break
            
        elif status == "error":
            print(f"❌ Apstrādes kļūda: {status_result.get('error_message', 'Nav norādīts')}")
            break
            
        elif status == "processing":
            time.sleep(5)
            waited += 5
        else:
            print(f"⚠️ Nezināms statuss: {status}")
            time.sleep(2)
            waited += 2
    
    if waited >= max_wait:
        print("⏰ Timeout - apstrāde aizņēma pārāk daudz laika")
    
    # 4. Iegūt detalizētus rezultātus
    print(f"\n📊 4. Iegūstam detalizētus rezultātus...")
    response = requests.get(f"{API_BASE}/api/v1/process/{file_id}/results")
    
    if response.status_code == 200:
        results = response.json()
        
        print(f"\n🔍 DETALIZĒTI REZULTĀTI:")
        print(f"📁 Fails: {results['filename']}")
        
        proc_info = results['processing_info']
        print(f"⏱️ Apstrādes laiks: {proc_info.get('started_at')} → {proc_info.get('processed_at')}")
        print(f"🔍 OCR confidence: {proc_info.get('ocr_confidence')}")
        print(f"🔧 OCR stratēģija: {proc_info.get('ocr_strategy')}")
        print(f"📊 Kopējais confidence: {proc_info.get('overall_confidence')}")
        
        print(f"\n📄 OCR teksts (fragments):")
        raw_text = results.get('raw_ocr_text', '')
        print(f"'{raw_text[:200]}...'")
        
    else:
        print(f"❌ Rezultātu iegūšana neizdevās: {response.status_code}")

def test_retry_functionality():
    """Testē retry funkcionalitāti"""
    print(f"\n🔄 5. Testējam retry funkcionalitāti...")
    
    # Šeit vajadzētu test ar failu, kas dod error
    # Pagaidām tikai parādām kā izsauktu
    print("ℹ️ Retry tests tiks implementēts ar error scenāriju")

if __name__ == "__main__":
    print("🧪 API Process Endpoints Tests")
    print("=" * 40)
    print("⚠️ Pārliecinieties, ka serveris darbojas: uvicorn app.main:app --reload")
    print("⚠️ Pārliecinieties, ka datubāze ir migrēta: alembic upgrade head")
    
    input("Spiediet Enter, lai turpinātu...")
    
    try:
        test_upload_and_process()
        test_retry_functionality()
        print(f"\n✅ Visi testi pabeigti!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Nevar savienoties ar serveri. Vai serveris darbojas?")
    except Exception as e:
        print(f"❌ Neparedzēta kļūda: {e}")
