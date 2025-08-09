"""
Pilns API pipeline tests ar īstu failu
"""
import requests
import time
import json
from pathlib import Path

API_BASE = "http://localhost:8000"

def test_full_pipeline():
    """Testē pilnu OCR pipeline ar īstu pavadzīmi"""
    
    print("🚀 Pilns OCR Pipeline Tests")
    print("=" * 50)
    
    # Pārbaudām, vai serveris darbojas
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"✅ Serveris: {response.json()['message']}")
    except Exception as e:
        print(f"❌ Serveris nav pieejams: {e}")
        return
    
    # Test ar TIM-T failu
    test_file = Path("c:/Code/regex_invoice_processing/uploads/tim_t.jpg")
    if not test_file.exists():
        print(f"❌ TIM-T fails nav atrasts: {test_file}")
        return
    
    print(f"\n📤 1. Augšupielādējam: {test_file.name}")
    with open(test_file, 'rb') as f:
        files = {'file': ('tim_t.jpg', f, 'image/jpeg')}
        response = requests.post(f"{API_BASE}/api/v1/upload", files=files)
    
    if response.status_code != 200:
        print(f"❌ Upload: {response.status_code}")
        return
    
    upload_data = response.json()
    file_id = upload_data['file_id']
    print(f"✅ Upload: ID={file_id}")
    
    print(f"\n⚡ 2. Sākam OCR apstrādi...")
    response = requests.post(f"{API_BASE}/api/v1/process/{file_id}")
    if response.status_code != 200:
        print(f"❌ Process: {response.status_code}")
        return
    
    process_data = response.json()
    print(f"✅ Process sākts: {process_data['message']}")
    
    print(f"\n⏳ 3. Gaidām apstrādes pabeigšanu...")
    max_wait = 30  # 30 sekundes
    for i in range(max_wait):
        response = requests.get(f"{API_BASE}/api/v1/process/{file_id}/status")
        if response.status_code == 200:
            status_data = response.json()
            status = status_data['status']
            print(f"   Status: {status} ({i+1}s)")
            
            if status == "completed":
                print("🎉 Apstrāde pabeigta!")
                break
            elif status == "error":
                print(f"❌ Kļūda: {status_data.get('error_message')}")
                return
        
        time.sleep(1)
    else:
        print("⏰ Timeout - apstrāde pārāk ilga")
        return
    
    print(f"\n📊 4. Iegūstam rezultātus...")
    response = requests.get(f"{API_BASE}/api/v1/process/{file_id}/results")
    if response.status_code != 200:
        print(f"❌ Results: {response.status_code}")
        return
    
    results = response.json()
    
    print("\n" + "="*50)
    print("📋 GALĪGIE REZULTĀTI:")
    print("="*50)
    
    # Pamat informācija
    if results.get('invoice_number'):
        print(f"📄 Pavadzīmes Nr: {results['invoice_number']}")
    if results.get('supplier_name'):
        print(f"🏢 Piegādātājs: {results['supplier_name']}")
    if results.get('invoice_date'):
        print(f"📅 Datums: {results['invoice_date']}")
    if results.get('total_amount'):
        print(f"💰 Summa: {results['total_amount']} {results.get('currency', 'EUR')}")
    if results.get('vat_amount'):
        print(f"💰 PVN: {results['vat_amount']} {results.get('currency', 'EUR')}")
    if results.get('reg_number'):
        print(f"🔢 Reģ.nr: {results['reg_number']}")
    if results.get('address'):
        print(f"📍 Adrese: {results['address']}")
    if results.get('bank_account'):
        print(f"🏦 Bankas konts: {results['bank_account']}")
    
    # Kvalitātes metriki
    print(f"\n📊 KVALITĀTE:")
    if results.get('ocr_confidence'):
        print(f"🔍 OCR confidence: {results['ocr_confidence']:.1%}")
    if results.get('confidence_score'):
        print(f"📊 Kopējais confidence: {results['confidence_score']:.1%}")
    if results.get('ocr_strategy'):
        print(f"🔧 OCR stratēģija: {results['ocr_strategy']}")
    
    print(f"\n⏱️ LAIKI:")
    if results.get('uploaded_at'):
        print(f"📤 Augšupielādēts: {results['uploaded_at']}")
    if results.get('started_at'):
        print(f"🏁 Sākts: {results['started_at']}")
    if results.get('processed_at'):
        print(f"✅ Pabeigts: {results['processed_at']}")
    
    print("\n🎯 SECINĀJUMI:")
    confidence = results.get('confidence_score', 0)
    if confidence >= 0.8:
        print("✅ Izcila kvalitāte - dati pilnībā uzticami")
    elif confidence >= 0.6:
        print("✅ Laba kvalitāte - dati lielākoties pareizi")
    elif confidence >= 0.4:
        print("⚠️ Vidēja kvalitāte - ieteicama pārbaude")
    else:
        print("❌ Zema kvalitāte - vajag manuālu korekciju")
    
    print(f"\n✅ Pipeline tests pabeigts veiksmīgi!")

if __name__ == "__main__":
    test_full_pipeline()
