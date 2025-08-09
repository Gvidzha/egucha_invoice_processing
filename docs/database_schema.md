# Datubāzes shēmas apraksts

## PostgreSQL datubāzes struktūra

Sistēmā izmanto PostgreSQL datubāzi ar 4 galvenajām tabulām mašīnmācīšanās un pavadzīmju apstrādes datu glabāšanai.

## Tabulu struktūra

### 1. invoices (Pavadzīmes)
Galvenā tabula ar pavadzīmju informāciju un OCR rezultātiem.

```sql
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    
    -- Faila informācija
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    
    -- OCR rezultāts
    raw_text TEXT,
    confidence_score REAL,
    
    -- Ekstraktētā informācija
    supplier_name VARCHAR(255),
    supplier_confidence REAL,
    invoice_date TIMESTAMP,
    delivery_date TIMESTAMP,
    total_amount REAL,
    currency VARCHAR(10) DEFAULT 'EUR',
    
    -- Apstrādes statuss
    status VARCHAR(50) DEFAULT 'uploaded',
    error_message TEXT,
    
    -- Lietotāja labojumi
    is_manually_corrected BOOLEAN DEFAULT FALSE,
    correction_notes TEXT,
    
    -- Laika zīmogi
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);
```

**Statusa vērtības:**
- `uploaded` - Fails augšupielādēts, gaida apstrādi
- `processing` - Notiek OCR apstrāde
- `completed` - Apstrāde pabeigta veiksmīgi
- `error` - Apstrādes kļūda
- `manual_review` - Nepieciešama manuāla pārbaude

### 2. suppliers (Piegādātāji)
Piegādātāju datubāze ar mācīšanās patterns un statistiku.

```sql
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    
    -- Piegādātāja pamata informācija
    name VARCHAR(255) NOT NULL UNIQUE,
    name_variations TEXT, -- JSON array ar variantiem
    
    -- Kontaktinformācija
    address TEXT,
    phone VARCHAR(50),
    email VARCHAR(255),
    registration_number VARCHAR(100),
    vat_number VARCHAR(50),
    
    -- Atpazīšanas patterns
    recognition_patterns TEXT, -- JSON ar regex patterns
    confidence_threshold REAL DEFAULT 0.8,
    
    -- Statistika un mācīšanās
    times_processed INTEGER DEFAULT 0,
    last_seen TIMESTAMP,
    accuracy_rate REAL DEFAULT 0.0,
    
    -- Statuss
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    
    -- Laika zīmogi
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**name_variations JSON piemērs:**
```json
["SIA PIEMĒRS", "Piemērs SIA", "PIEMERS", "Piemērs, SIA"]
```

**recognition_patterns JSON piemērs:**
```json
[
    "(?i)SIA\\s+PIEMĒRS",
    "(?i)PIEMĒRS\\s*,?\\s*SIA", 
    "(?i)PIEMERS"
]
```

### 3. products (Produkti)
Produktu informācija no pavadzīmēm.

```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Saite uz pavadzīmi
    invoice_id INTEGER NOT NULL,
    
    -- Produkta informācija
    name VARCHAR(500) NOT NULL,
    description TEXT,
    product_code VARCHAR(100),
    
    -- Daudzumi un cenas
    quantity REAL,
    unit VARCHAR(50), -- gab, kg, l, m, utt.
    unit_price REAL,
    total_price REAL,
    
    -- Nodokļi
    vat_rate REAL, -- PVN likme procentos
    vat_amount REAL, -- PVN summa
    
    -- Ekstraktēšanas kvalitāte
    extraction_confidence REAL,
    is_manually_corrected BOOLEAN DEFAULT FALSE,
    
    -- Rindas pozīcija pavadzīmē
    line_number INTEGER,
    raw_text TEXT, -- Oriģinālā rindan OCR teksts
    
    FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE
);
```

### 4. error_corrections (Kļūdu labojumi)
Kļūdu vārdnīca mašīnmācīšanās uzlabošanai.

```sql
CREATE TABLE error_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Saite uz pavadzīmi (nav obligāta)
    invoice_id INTEGER,
    
    -- Kļūdas informācija
    error_type VARCHAR(100) NOT NULL, -- supplier, product, date, amount
    field_name VARCHAR(100), -- konkrētais lauks
    
    -- Oriģinālā un labotā vērtība
    original_value TEXT NOT NULL,
    corrected_value TEXT NOT NULL,
    
    -- Konteksts
    surrounding_text TEXT, -- Teksts ap kļūdu
    confidence_before REAL, -- Confidence pirms labojuma
    confidence_after REAL,  -- Confidence pēc labojuma
    
    -- Pattern informācija
    matched_pattern TEXT, -- Regex pattern kas sakrita
    suggested_pattern TEXT, -- Ieteiktais jauns pattern
    
    -- Lietotāja informācija
    correction_source VARCHAR(50) DEFAULT 'manual', -- manual, auto, suggested
    user_feedback TEXT,
    
    -- Mācīšanās statuss
    is_applied_to_model BOOLEAN DEFAULT FALSE,
    application_date DATETIME,
    effectiveness_score REAL, -- Cik efektīvs bijis labojums
    
    -- Laika zīmogi
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE SET NULL
);
```

**error_type vērtības:**
- `supplier` - Piegādātāja nosaukuma kļūda
- `product` - Produkta informācijas kļūda
- `date` - Datuma kļūda
- `amount` - Summas kļūda
- `vat` - PVN aprēķina kļūda

## Indeksi optimizācijai

```sql
-- Pavadzīmju meklēšanai
CREATE INDEX idx_invoices_supplier ON invoices(supplier_name);
CREATE INDEX idx_invoices_date ON invoices(invoice_date);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_created_at ON invoices(created_at);

-- Produktu meklēšanai
CREATE INDEX idx_products_invoice_id ON products(invoice_id);
CREATE INDEX idx_products_name ON products(name);

-- Piegādātāju meklēšanai
CREATE INDEX idx_suppliers_name ON suppliers(name);
CREATE INDEX idx_suppliers_active ON suppliers(is_active);

-- Kļūdu analīzei
CREATE INDEX idx_errors_type ON error_corrections(error_type);
CREATE INDEX idx_errors_invoice ON error_corrections(invoice_id);
CREATE INDEX idx_errors_created ON error_corrections(created_at);
```

## Datu migrācijas

### Izveidošanas skripts
```sql
-- suppliers.sql
-- Sākotnējie piegādātāji demo vajadzībām
INSERT INTO suppliers (name, name_variations, is_verified) VALUES 
('SIA PIEMĒRS', '["SIA PIEMĒRS", "PIEMĒRS SIA", "Piemērs"]', TRUE),
('AS TESTS', '["AS TESTS", "TESTS AS", "A/S TESTS"]', TRUE);
```

## Backup stratēģija

1. **Dienas backup** - Katru dienu 02:00
2. **Nedēļas backup** - Katru svētdienu pilns backup
3. **Mēneša arhīvs** - Mēneša beigas

**Backup komanda:**
```bash
pg_dump -U invoice_user -h localhost invoice_processing_db | gzip > backup_$(date +%Y%m%d).sql.gz
```

## Performance apsvērumi

- **Pagination** - Izmantot LIMIT/OFFSET lieliem resultātiem
- **Lazy loading** - Produktus ielādēt tikai pēc pieprasījuma  
- **Connection pooling** - PostgreSQL connection pool optimizācija
- **Query optimization** - Izmantot EXPLAIN ANALYZE

## Datubāzes pieauguma prognozes

Ar 10,000 pavadzīmēm mēnesī:
- **invoices**: ~120K ieraksti/gadā (~50MB)
- **products**: ~1.2M ieraksti/gadā (~200MB) 
- **error_corrections**: ~50K ieraksti/gadā (~20MB)
- **suppliers**: ~5K ieraksti/gadā (~2MB)

**Kopējais izmērs**: ~300MB/gadā
