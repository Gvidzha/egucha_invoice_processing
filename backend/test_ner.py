"""
NER sistēmas tests
Pārbauda hibridā ekstraktēšanas servisa funkcionalitāti
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.hybrid_service import HybridExtractionService
from app.services.ner_service import NERService

# Testa OCR teksts (SIA Lindström piemērs)
TEST_OCR_TEXT = """
PAVADZĪME Nr. P240509001

SIA Lindström
Reg.Nr.: LV40003410015
Adrese: Daugavgrīvas iela 26, Rīga, LV-1050
Konts: LV10UNLA0050012345678

Piegāde uz: 
SIA "Uzņēmums ABC"
Reg.Nr.: LV50003999410
Adrese: Brīvības iela 123, Rīga, LV-1010

Datums: 09.05.2024
Derīgs līdz: 09.05.2025

MSW1 Pelkspaklajs85X150 09.05.2025      1      5,20      5,20
MSW2 Darba halāts XL                     2      8,50     17,00

Summa bez PVN:                                           22,20
PVN 21%:                                                  4,66
KOPĀ:                                                    26,86 EUR
"""

async def test_ner_service():
    """Testē NER servisu"""
    print("🔍 Testējam NER servisu...")
    
    ner_service = NERService()
    
    # Ekstraktē entītijas
    entities = await ner_service.extract_entities(TEST_OCR_TEXT)
    
    print(f"✅ Atrastas {len(entities)} entītijas:")
    for entity in entities:
        print(f"  - {entity.label}: '{entity.text}' (confidence: {entity.confidence:.2f})")
    
    return entities

async def test_hybrid_service():
    """Testē hibridāo servisu"""
    print("\n🔬 Testējam hibridāo ekstraktēšanas servisu...")
    
    hybrid_service = HybridExtractionService()
    
    # Ekstraktē ar NER ieslēgtu
    print("📊 Ekstraktēšana ar NER:")
    data_with_ner = await hybrid_service.extract_invoice_data(TEST_OCR_TEXT, use_ner=True)
    
    print(f"  Piegādātājs: {data_with_ner.supplier_name} (confidence: {data_with_ner.supplier_confidence:.2f})")
    print(f"  Saņēmējs: {data_with_ner.recipient_name} (confidence: {data_with_ner.recipient_confidence:.2f})")
    print(f"  Kopējā summa: {data_with_ner.total_amount} {data_with_ner.currency}")
    print(f"  Produkti: {len(data_with_ner.products)}")
    print(f"  Overall confidence: {data_with_ner.confidence_score:.2f}")
    
    # Ekstraktē tikai ar regex
    print("\n📊 Ekstraktēšana tikai ar regex:")
    data_regex_only = await hybrid_service.extract_invoice_data(TEST_OCR_TEXT, use_ner=False)
    
    print(f"  Piegādātājs: {data_regex_only.supplier_name} (confidence: {data_regex_only.supplier_confidence:.2f})")
    print(f"  Saņēmējs: {data_regex_only.recipient_name} (confidence: {data_regex_only.recipient_confidence:.2f})")
    print(f"  Kopējā summa: {data_regex_only.total_amount} {data_regex_only.currency}")
    print(f"  Produkti: {len(data_regex_only.products)}")
    print(f"  Overall confidence: {data_regex_only.confidence_score:.2f}")
    
    return data_with_ner, data_regex_only

async def test_learning():
    """Testē mācīšanās funkcionalitāti"""
    print("\n🎓 Testējam mācīšanos no labojumiem...")
    
    hybrid_service = HybridExtractionService()
    
    # Vispirms ekstraktē
    extracted_data = await hybrid_service.extract_invoice_data(TEST_OCR_TEXT)
    
    # Simulējam lietotāja labojumus (precīzākus)
    corrections = {
        "supplier_name": "SIA Lindström",  # Atstājam pareizo
        "recipient_name": "SIA Uzņēmums ABC", 
        "total_amount": 26.86,
        "recipient_reg_number": "LV50003999410"
    }
    
    print(f"📝 Labojumi: {corrections}")
    
    # Mācās no labojumiem
    learning_results = await hybrid_service.learn_from_corrections(
        TEST_OCR_TEXT,
        extracted_data,
        corrections
    )
    
    print(f"✅ Mācīšanās rezultāti: {learning_results}")
    
    return learning_results

async def test_statistics():
    """Testē statistikas iegūšanu"""
    print("\n📊 Testējam statistiku...")
    
    hybrid_service = HybridExtractionService()
    
    stats = await hybrid_service.get_extraction_statistics()
    print(f"📈 Statistika: {stats}")
    
    return stats

async def main():
    """Galvenā testa funkcija"""
    print("🚀 Sākam NER sistēmas testēšanu...\n")
    
    try:
        # 1. Testē NER servisu
        entities = await test_ner_service()
        
        # 2. Testē hibridāo servisu
        hybrid_data, regex_data = await test_hybrid_service()
        
        # 3. Testē mācīšanos
        learning_results = await test_learning()
        
        # 4. Testē statistiku
        stats = await test_statistics()
        
        print("\n🎉 Visi testi veiksmīgi pabeigti!")
        print("\n📋 KOPSAVILKUMS:")
        print(f"  - NER entītijas: {len(entities)}")
        print(f"  - Hibridā confidence: {hybrid_data.confidence_score:.2f}")
        print(f"  - Regex confidence: {regex_data.confidence_score:.2f}")
        print(f"  - Mācīšanās uzlabojumi: {learning_results.get('combined_improvements', 0)}")
        print(f"  - Iemācītie patterns: {stats.get('total_learned_patterns', 0)}")
        
    except Exception as e:
        print(f"❌ Kļūda testā: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
