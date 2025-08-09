# OCR Modulis - Dokumentācija

## Pārskats

OCR (Optical Character Recognition) modulis ir strukturēts pavadzīmju teksta atpazīšanai no attēliem un PDF failiem. Modulis ir sadalīts vairākos specializētos apakšmoduļos katrs ar savu atbildības jomu.

## Arhitektūra

```
app/services/ocr/
├── __init__.py              # Modulis exports
├── ocr_main.py             # Galvenais OCR serviss
├── tesseract_config.py     # Tesseract konfigurācija
├── image_preprocessor.py   # Attēlu priekšapstrāde
├── text_cleaner.py         # Teksta tīrīšana un kļūdu labošana
└── pdf_processor.py        # PDF failu apstrāde
```

## Moduļu apraksts

### 1. TesseractManager (`tesseract_config.py`)

**Atbildība**: Tesseract OCR instalācijas pārbaude un konfigurācija

**Galvenās funkcijas**:
- Tesseract instalācijas detekcija
- Latviešu valodas atbalsta pārbaude
- OCR parametru konfigurācija
- Instalācijas instrukciju sniegšana

```python
from app.services.ocr import TesseractManager

manager = TesseractManager()
setup = manager.setup_tesseract()

if setup['installed'] and setup['latvian_support']:
    print("Tesseract gatavs lietošanai!")
```

### 2. ImagePreprocessor (`image_preprocessor.py`)

**Atbildība**: Attēlu kvalitātes uzlabošana OCR procesam

**Galvenās funkcijas**:
- Izmēra normalizācija
- Rotācijas korekcija
- Trokšņa samazināšana
- Kontrasta uzlabošana
- Binarizācija
- Morfologiskās operācijas

```python
from app.services.ocr import ImagePreprocessor

preprocessor = ImagePreprocessor()

# Vispārīga priekšapstrāde
processed_path = preprocessor.preprocess_image("input.jpg")

# Specializēta pavadzīmju priekšapstrāde
invoice_path = preprocessor.preprocess_for_invoice("pavadzime.jpg")
```

### 3. TextCleaner (`text_cleaner.py`)

**Atbildība**: OCR teksta tīrīšana un strukturēto datu ekstraktēšana

**Galvenās funkcijas**:
- Tipisko OCR kļūdu labošana
- Latviešu valodas specifisko kļūdu korekcija
- Pavadzīmju terminoloģijas atpazīšana
- Datumu un summu ekstraktēšana
- Confidence score aprēķināšana

```python
from app.services.ocr import TextCleaner

cleaner = TextCleaner()

# Teksta tīrīšana
cleaned_text = cleaner.clean_text(raw_ocr_text)

# Strukturēto datu ekstraktēšana
data = cleaner.extract_structured_data(cleaned_text)
print(f"Atrasti datumi: {data['dates']}")
print(f"Atrastas summas: {data['amounts']}")
```

### 4. PDFProcessor (`pdf_processor.py`)

**Atbildība**: PDF failu apstrāde OCR vajadzībām

**Galvenās funkcijas**:
- PDF konversija uz attēliem
- Direct text extraction no PDF
- PDF attēlu optimizācija
- Batch PDF apstrāde

```python
from app.services.ocr import PDFProcessor

pdf_processor = PDFProcessor()

# Sagatavo PDF OCR apstrādei
prep_result = pdf_processor.process_pdf_for_ocr("invoice.pdf")

if prep_result['success']:
    print(f"PDF sagatavots: {prep_result['processed_pages']} lapas")
```

### 5. OCRService (`ocr_main.py`)

**Atbildība**: Koordinē visus OCR procesus un sniedz vienotu API

**Galvenās funkcijas**:
- Sistēmas inicializācija
- Pilns OCR workflow
- Batch apstrāde
- Statistika un monitoring

```python
from app.services.ocr import OCRService

# Inicializē servisu
ocr = OCRService()
await ocr.initialize()

# Apstrādā attēlu
result = await ocr.extract_text_from_image("pavadzime.jpg")

# Apstrādā PDF
pdf_result = await ocr.extract_text_from_pdf("documents.pdf")

# Batch apstrāde
batch_results = await ocr.batch_process([
    "img1.jpg", "img2.png", "doc.pdf"
])
```

## Instalācija un Setup

### 1. Python bibliotēkas

```bash
cd backend
pip install -r requirements.txt
```

### 2. Tesseract instalācija

**Windows:**
```powershell
winget install UB-Mannheim.TesseractOCR
```
Vai lejupielādējiet no: https://github.com/UB-Mannheim/tesseract/wiki

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-lav
```

**CentOS/RHEL:**
```bash
sudo yum install tesseract tesseract-langpack-lav
```

### 3. Sistēmas pārbaude

```bash
cd backend
python setup_ocr.py
```

## Konfigurācija

OCR moduļa iestatījumi atrodas `app/config.py`:

```python
# OCR iestatījumi
TESSERACT_CONFIG = {
    "lang": "lav+eng",
    "config": "--oem 3 --psm 6 --dpi 300",
    "timeout": 30,
    "char_whitelist": "0123456789...ĀĒĪŌŪāēīōū..."
}

# Priekšapstrādes iestatījumi
IMAGE_PREPROCESSING = {
    "enable": True,
    "invoice_mode": True,
    "target_dpi": 300,
    "enhancement_level": "medium"
}
```

## Izmantošana API

OCR modulis ir integrēts ar FastAPI endpoints:

```python
# app/api/process.py
from app.services.ocr import get_ocr_service

@router.post("/process/{file_id}")
async def process_file(file_id: int):
    ocr_service = await get_ocr_service()
    
    # Apstrādā failu
    result = await ocr_service.extract_text_from_image(file_path)
    
    return {
        "text": result['cleaned_text'],
        "confidence": result['confidence_score'],
        "structured_data": result['structured_data']
    }
```

## Testēšana

### Unit testi

```bash
cd backend
python -m pytest tests/test_ocr/ -v
```

### Manuāla testēšana

```bash
# Setup un tests
python setup_ocr.py

# Ievietot test attēlus direktorijā:
# backend/test_images/
```

## Performance optimizācijas

### 1. Priekšapstrādes optimizācija
- Izmantojiet `invoice_mode=True` pavadzīmēm
- Konfigurējiet `enhancement_level` atkarībā no attēlu kvalitātes

### 2. Parallel processing
```python
# Batch apstrāde lielu failu apjomiem
results = await ocr.batch_process(file_list)
```

### 3. Temporary failu tīrīšana
```python
# Automātiska tīrīšana
preprocessor.cleanup_temp_files(keep_recent=5)
pdf_processor.cleanup_temp_files(keep_recent=3)
```

## Troubleshooting

### Tipiskās problēmas

1. **"Tesseract nav atrasts"**
   - Pārbaudiet vai Tesseract ir instalēts
   - Windows: Pārbaudiet PATH vai iestatiet `TESSERACT_PATH`

2. **"Latviešu valoda nav pieejama"**
   - Instalējiet latviešu language pack
   - Ubuntu: `sudo apt-get install tesseract-ocr-lav`

3. **"PDF apstrāde nedarbojas"**
   - Instalējiet PyMuPDF: `pip install PyMuPDF`
   - Instalējiet poppler (Linux): `sudo apt-get install poppler-utils`

4. **Zema OCR kvalitāte**
   - Ieslēdziet priekšapstrādi: `preprocess=True`
   - Izmantojiet `invoice_mode=True` pavadzīmēm
   - Pārbaudiet attēlu kvalitāti un izmēru

### Debug režīms

```python
# Saglabā katru priekšapstrādes soli
processed_path = preprocessor.preprocess_image(
    image_path, 
    save_steps=True  # Debug režīms
)
```

## Nākamie uzlabojumi

1. **GPU acceleration** - CUDA atbalsts Tesseract
2. **ML classificātion** - Pavadzīmju tipu atpazīšana
3. **Template matching** - Strukturētu pavadzīmju atpazīšana
4. **Confidence optimization** - Uzlabota kvalitātes novērtēšana
5. **Batch optimization** - Optimizēta parallel processing

## Versiju vēsture

- **v1.0** - Pamata OCR funkcionalitāte
- **v1.1** - Modulāra arhitektūra
- **v1.2** - PDF atbalsts
- **v1.3** - Latviešu valodas optimizācijas (current)
