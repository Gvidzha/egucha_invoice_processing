# 🔮 NER (Named Entity Recognition) Sistēma

## 📋 Apraksts

NER sistēma ir jauns modulārs komponents, kas papildina esošo regex ekstraktēšanas sistēmu ar mašīnmācīšanās bāzētu pieeju. Sistēma **neizjauc** esošo regex kodu un darbojas paralēli.

## 🎯 Galvenās īpašības

### ✅ **Mācīšanās darba vidē**
- Mācās no lietotāja labojumiem reālajā laikā
- Atceras kļūdas un neatkārto tās
- Uzlabo ekstraktēšanas kvalitāti katru reizi

### 🔄 **Hibridā pieeja**
- **Regex baseline**: Nodrošina stabilu darbu
- **NER enhancement**: Uzlabo precizitāti
- **Automatisks fallback**: Ja NER nedarbojas, izmanto regex

### 📊 **Adaptīva kvalitāte**
- Mācās katras firmas specifiku
- Uzlabo patterns pēc katras kļūdas
- Automātiski ģenerē jaunus ekstraktēšanas likumus

## 🏗️ Arhitektūra

```
📁 app/services/
├── extraction_service.py    # ✅ Oriģinālais regex (netiek aiztikts)
├── ner_service.py          # 🆕 NER komponents  
└── hybrid_service.py       # 🆕 Apvieno regex + NER
```

## 🚀 Lietošana

### 1. **Automātiska hibridā ekstraktēšana**

Sistēma automātiski izmanto hibridāo pieeju:

```python
# Notiek automātiski process.py
# 1. Sākumā: regex ekstraktēšana (stabils baseline)
# 2. Papildus: NER uzlabojumi
# 3. Kombinē abus rezultātus
```

### 2. **Mācīšanās no labojumiem**

```http
POST /api/process/learn/{file_id}
Content-Type: application/json

{
  "supplier_name": "SIA Lindström Latvija",
  "recipient_name": "SIA Uzņēmums ABC", 
  "total_amount": 26.86,
  "recipient_reg_number": "LV50003999410"
}
```

**Rezultāts:**
```json
{
  "status": "success",
  "message": "Mācīšanās no labojumiem veiksmīga",
  "learning_results": {
    "ner_learning": {
      "learned": true,
      "patterns_updated": 4
    },
    "combined_improvements": 4
  },
  "corrected_fields": ["supplier_name", "recipient_name", "total_amount", "recipient_reg_number"]
}
```

### 3. **Statistika un progress**

```http
GET /api/process/learning/statistics
```

```json
{
  "status": "success",
  "statistics": {
    "extraction_service": "hybrid",
    "total_learned_patterns": 15,
    "supported_invoice_types": ["LINDSTROM", "PETERSTIRGUS", "GENERIC"],
    "learning_active": true
  }
}
```

## 📂 Datu struktūra

### Learned Patterns
```json
{
  "SUPPLIER": [
    {
      "pattern": "(?:SIA\\s+)?(Lindström)",
      "confidence": 0.9,
      "example": "SIA Lindström",
      "invoice_type": "LINDSTROM"
    }
  ],
  "RECIPIENT": [...],
  "AMOUNT": [...]
}
```

### Learning History
```json
[
  {
    "original_text": "OCR teksts...",
    "corrected_entities": [...],
    "timestamp": "2024-05-09T10:30:00",
    "supplier_name": "SIA Lindström",
    "invoice_type": "LINDSTROM"
  }
]
```

## 🔧 Konfigurācija

### config.py iestatījumi:

```python
# NER un AI ekstraktēšanas iestatījumi
NER_CONFIG = {
    "enabled": True,
    "confidence_threshold": 0.7,
    "max_learning_examples": 1000,
    "enable_continuous_learning": True
}

# Hibridās ekstraktēšanas iestatījumi
HYBRID_EXTRACTION = {
    "use_ner": True,
    "ner_weight": 0.6,  # 60% NER, 40% regex
    "fallback_to_regex": True
}
```

## 🧪 Testēšana

Palaidiet NER sistēmas testu:

```bash
cd backend
python test_ner.py
```

**Testa rezultāts:**
```
🚀 Sākam NER sistēmas testēšanu...

🔍 Testējam NER servisu...
✅ Atrastas 3 entītijas:
  - SUPPLIER: 'SIA Lindström' (confidence: 0.80)
  - AMOUNT: '26.86' (confidence: 0.75)
  - DATE: '09.05.2024' (confidence: 0.70)

🔬 Testējam hibridāo ekstraktēšanas servisu...
📊 Ekstraktēšana ar NER:
  Piegādātājs: SIA Lindström (confidence: 0.80)
  Overall confidence: 0.73

🎓 Testējam mācīšanos no labojumiem...
✅ Mācīšanās rezultāti: {'learned': True, 'patterns_updated': 4}

🎉 Visi testi veiksmīgi pabeigti!
```

## 📈 Priekšrocības

### 🎯 **Progresīva uzlabošanās**
- Katrs labojums uzlabo sistēmu
- Automātiski adaptējas jauniem formātiem
- Nepazaudē iepriekšējo pieredzi

### 🛡️ **Drošība**
- Regex sistēma paliek kā fallback
- Pakāpeniska migrācija uz AI
- Nav risks sabojāt esošo funkcionalitāti

### 🏢 **Enterprise ready**
- Mācās katras firmas specifiku
- Skalējas līdz ar datu daudzumu
- Gatavs tūkstošiem invoice formātu

## 🔄 Migrācijas plāns

### **FĀZE 1** (Pabeigta ✅)
- [x] NER sistēmas izveide
- [x] Hibridā servisa implementācija
- [x] Mācīšanās API
- [x] Testēšanas sistēma

### **FĀZE 2** (Nākamie soļi)
- [ ] SpaCy NER modeļa integrācija
- [ ] BERT transformers atbalsts
- [ ] Uzlabots pattern ģenerēšanas algoritms

### **FĀZE 3** (Nākotne)
- [ ] Regex koda pakāpeniska atvienošana
- [ ] Pilnīga AI bāzēta ekstraktēšana
- [ ] LayoutLM dokumentu analīze

## 🎊 Secinājums

NER sistēma ir ieviesta **bez riska** esošajam kodaam. Tā:

✅ **Neizjauc** esošo regex kodu  
✅ **Uzlabo** ekstraktēšanas kvalitāti  
✅ **Mācās** no katras kļūdas  
✅ **Skalējas** uz tūkstošiem formātu  
✅ **Gatava** uzreiz sākt mācīties!  

🚀 **Tagad katrs lietotāja labojums padarīs sistēmu gudrāku!**
