#!/usr/bin/env python3
"""
Produktu rindu un saņēmēja ekstraktēšanas tests
Testē jaunās funkcionalitātes ar reālu Lindström pavadzīmi
"""

import asyncio
from app.services.extraction_service import ExtractionService

# Lindström pavadzīmes teksts
LINDSTROM_TEXT = """
ete -. if ik a Rēķins Lapa1(1) gt RēķinaNr. 71068107 ig Izrakstibanasdat. 31. 05. 2025 %, Kllenta/LTgumaNr. 3994410 e o P) x)Lindstrēm ŽiroNr 10867 U Apmaksasterming 14dienas i Meistaruiela4Pipki, Babitespag, Mirupesnovads, LV-2107, g Meldruielala pmaksasvelds ar parskaitfjumu ie Riga, LV-5015 Pretenzijuizskatigana8dienas 1-3 Latvija Sodanaudadiena 0, 1% ē rekiniOriga. sushistation. lv KllentaPVNreg. Nr. LV40203271137 a KlientajuridiskaadreseKapsdtasiela20/22, Liepaja, Latvija 44 144 - Vaisaskanaarligumanosacijumiem. ļ t SIALINDSTROMKONTAKTINFORMACIJA TALRUNIS437167913120 i E-PASTSlatvijaOlindstromgroup. com š Piegadesdatums Cena, EURApmaksai, EUR j Mērvienība gab. 4 3994410 Piegddesadrese i NVERIGASIA Meldruielala, Riga (zs LV-5015, Latvija - 999- - Noma/piegade MSW1 Pelkspaklajs85X150 09. 05. 2025 1 5, 20 5, 20 MSW1 Pelkspaklajs85X150 23. 05. 2025 1 5, 20 5, 20 MSW1 Pelkspaklajs85X150 02. 05. 2025 1 5, 20 5, 20 MSW1 Pelkspaklajs85X150 16. 05. 2025 1 5, 20 5, 20 3 MSW1 Pelkspaklajs85X150 30. 05. 2025 1 5, 20 5, 20 4 Nod. 999kopa 26, 00 Klients3994410kopa 26, 00 a SummabezPVN(EUR). 26, 00945%0) PVN21%(EUR) 5, 46DOT Apmaksai(EUR). 31, 46458i0 Maksajumuslidzamveiktuzzemaknoraditobankaskontu- 1 SEBBankaAS, KodsUNLALV2xKontsLV92UNLA0055001187469 ā ApmaksajotladzunoraditrekinaNr. 71068107 Saimnieciskadarijumaveids-pakalpojumasniegSana PakalpojumasniegSanasperiods01. 05. 2025-31. 05. 2025 Sisrekinsirsagatavotselektroniskiunapliecinatsarelektroniskoparakstu 39944107106810731052025 5 Klientuservisavaditaja. MairitaKazeka Ak N š 53 Š b B o - te LindstromSIA ASSEBbanka Wee Reg. Nr. 40003237187, PVNNr. LV40003237187 Bankaskods UNLALV2X i Sep, Mlle lela4, Pinkl, Babitespag, Marupesnovads, LV-2107 Nordkin. kontsLV92UNLA0055001 187469 hi Q. 00000)00 ļ11 1l % 4 i)
"""

async def test_product_extraction():
    """Testē produktu rindu ekstraktēšanu"""
    
    print("🧪 TESTĒ PRODUKTU UN SAŅĒMĒJA EKSTRAKTĒŠANU")
    print("=" * 50)
    
    # Inicializējam extraction service
    extraction_service = ExtractionService()
    
    # Ekstraktējam visus datus
    print("📊 Ekstraktējam datus...")
    extracted_data = await extraction_service.extract_invoice_data(LINDSTROM_TEXT)
    
    print("\n🏢 PIEGĀDĀTĀJA INFORMĀCIJA:")
    print(f"📋 Nosaukums: {extracted_data.supplier_name}")
    print(f"🆔 Reģ.nr: {extracted_data.supplier_reg_number}")
    print(f"🏠 Adrese: {extracted_data.supplier_address}")
    print(f"💳 Bankas konts: {extracted_data.supplier_bank_account}")
    
    print("\n🏪 SAŅĒMĒJA INFORMĀCIJA:")
    print(f"📋 Nosaukums: {extracted_data.recipient_name}")
    print(f"🆔 Reģ.nr: {extracted_data.recipient_reg_number}")
    print(f"🏠 Adrese: {extracted_data.recipient_address}")
    print(f"💳 Bankas konts: {extracted_data.recipient_bank_account}")
    print(f"📊 Confidence: {extracted_data.recipient_confidence:.2%}")
    
    print("\n📦 PRODUKTU RINDAS:")
    if extracted_data.products:
        for i, product in enumerate(extracted_data.products, 1):
            print(f"  {i}. {product.name}")
            print(f"     📏 Daudzums: {product.quantity} {product.unit}")
            print(f"     💰 Vienības cena: €{product.unit_price}")
            print(f"     💯 Kopā: €{product.total_price}")
            print(f"     📊 PVN: {product.vat_rate}%")
            print()
    else:
        print("  ❌ Nav atrasti produkti")
    
    print("\n💰 FINANŠU KOPSAVILKUMS:")
    print(f"💵 Subtotal (bez PVN): €{extracted_data.subtotal_amount}")
    print(f"🏛️ PVN summa: €{extracted_data.vat_amount}")
    print(f"💸 Kopējā summa: €{extracted_data.total_amount}")
    
    print(f"\n📊 KOPĒJĀ CONFIDENCE: {extracted_data.confidence_score:.2%}")

if __name__ == "__main__":
    asyncio.run(test_product_extraction())
