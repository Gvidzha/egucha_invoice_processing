-- PILNĪGA DATUBĀZES SHĒMA
-- Visas tabulas ar template laukiem

-- 1. INVOICES TABULA (Galvenā pavadzīmju tabula)
CREATE TABLE invoices (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- === FILE METADATA ===
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size INTEGER,
    
    -- === OCR METADATA ===
    extracted_text TEXT,
    raw_text TEXT,
    ocr_confidence FLOAT,
    ocr_strategy VARCHAR(50),
    confidence_score FLOAT,
    
    -- === DOCUMENT INFORMATION ===
    document_type VARCHAR(50),          -- dok_tips
    document_series VARCHAR(50),        -- dok_serija
    document_number VARCHAR(100),       -- dok_nr
    invoice_date DATE,                  -- izrakstisanas_datums
    delivery_date DATE,                 -- dok_piegades_datums
    service_delivery_date DATE,         -- pakalpojuma_piegades_datums
    contract_number VARCHAR(100),       -- liguma_nr
    
    -- === SUPPLIER INFORMATION ===
    supplier_name VARCHAR(255),                    -- piegadatajs
    supplier_registration_number VARCHAR(50),     -- piegadataja_reg_nr
    supplier_vat_payer_number VARCHAR(50),        -- piegadataja_pvd_nr
    supplier_vat_number VARCHAR(50),              -- piegadataja_pvn
    supplier_legal_address TEXT,                  -- piegadataja_jur_adrese
    issue_address TEXT,                           -- izsniegsanas_adrese
    supplier_confidence FLOAT,
    
    -- === SUPPLIER BANKING ===
    supplier_bank_name VARCHAR(255),              -- piegadataja_banka
    supplier_account_number VARCHAR(50),          -- piegadataja_konts
    supplier_swift_code VARCHAR(20),              -- piegadataja_swift
    
    -- Additional banks (1-4)
    supplier_bank_name_1 VARCHAR(255),
    supplier_account_number_1 VARCHAR(50),
    supplier_swift_code_1 VARCHAR(20),
    supplier_bank_name_2 VARCHAR(255),
    supplier_account_number_2 VARCHAR(50),
    supplier_swift_code_2 VARCHAR(20),
    supplier_bank_name_3 VARCHAR(255),
    supplier_account_number_3 VARCHAR(50),
    supplier_swift_code_3 VARCHAR(20),
    supplier_bank_name_4 VARCHAR(255),
    supplier_account_number_4 VARCHAR(50),
    supplier_swift_code_4 VARCHAR(20),
    
    -- === RECIPIENT INFORMATION ===
    recipient_name VARCHAR(255),                  -- sanemejs
    recipient_registration_number VARCHAR(50),    -- sanemeja_reg_nr
    recipient_vat_number VARCHAR(50),             -- sanemeja_pvn
    recipient_legal_address TEXT,                 -- sanemeja_jur_adrese
    receiving_address TEXT,                       -- sanemsanas_adrese
    recipient_confidence FLOAT,
    
    -- === RECIPIENT BANKING ===
    recipient_bank_name VARCHAR(255),             -- sanemeja_banka
    recipient_account_number VARCHAR(50),         -- sanemeja_konts
    recipient_swift_code VARCHAR(20),             -- sanemeja_swift
    
    -- === TRANSPORT INFORMATION ===
    carrier_name VARCHAR(255),                    -- parvadatajs
    carrier_vat_number VARCHAR(50),               -- parvadataja_pvn
    vehicle_number VARCHAR(50),                   -- trans_lidz_nr
    driver_name VARCHAR(255),                     -- auto_vaditajs
    
    -- === TRANSACTION INFORMATION ===
    transaction_type VARCHAR(100),                -- darijums
    service_period VARCHAR(100),                  -- pakalpojuma_periods
    payment_method VARCHAR(100),                  -- apmaksas_veids
    notes TEXT,                                   -- piezimes
    
    -- === FINANCIAL INFORMATION ===
    currency VARCHAR(10) DEFAULT 'EUR',          -- curency
    discount FLOAT,                               -- atlaide
    total_with_discount FLOAT,                    -- kopā_ar_atlaidi
    amount_with_discount FLOAT,                   -- summa_ar_atlaidi
    amount_without_discount FLOAT,                -- summa_bez_atlaides
    amount_without_vat FLOAT,                     -- summa_bez_pvn
    vat_amount FLOAT,                             -- pvn_summa
    total_amount FLOAT,                           -- kopa_apmaksai
    
    -- === ADDITIONAL INFORMATION ===
    issued_by_name VARCHAR(255),                  -- izsniedza_vards_uzvards
    payment_due_date DATE,                        -- apmaksat_lidz
    justification TEXT,                           -- pamatojums
    total_issued FLOAT,                           -- kopa_izsniegts
    weight_kg FLOAT,                              -- svars_kg
    issued_by VARCHAR(255),                       -- izsniedza
    total_quantity FLOAT,                         -- daudzums_kopa
    page_number VARCHAR(20),                      -- lapa
    
    -- === STRUCTURE ANALYSIS (POSM 4.5) ===
    document_structure TEXT,                      -- JSON dokumenta struktūra
    detected_zones TEXT,                          -- JSON atpazītās zonas
    table_regions TEXT,                           -- JSON tabulu reģioni
    structure_confidence FLOAT,
    has_structure_analysis BOOLEAN DEFAULT FALSE,
    has_structure_aware_ocr BOOLEAN DEFAULT FALSE,
    structure_analyzed_at TIMESTAMP,
    
    -- === SYSTEM METADATA ===
    status VARCHAR(20) DEFAULT 'uploaded',
    error_message TEXT,
    is_manually_corrected BOOLEAN DEFAULT FALSE,
    correction_notes TEXT,
    
    -- === TIMESTAMPS ===
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- 2. PRODUCTS TABULA (Produktu rindas)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    
    -- === PRODUCT INFORMATION ===
    product_sequence_number INTEGER,               -- Nr
    product_delivery_date DATE,                    -- piegades_datums
    product_code VARCHAR(100),                     -- kods
    product_name VARCHAR(255),                     -- prece
    product_usage VARCHAR(255),                    -- izlietot
    incoming_batch_number VARCHAR(100),           -- ienak_partijas_nr
    unit_of_measure VARCHAR(20),                   -- merv
    quantity FLOAT,                                -- daudzums
    unit_price FLOAT,                              -- cena
    product_discount FLOAT,                        -- atlaide
    price_with_discount FLOAT,                     -- cena_ar_atlaidi
    vat_rate FLOAT,                                -- pvn_likme
    total_price FLOAT,                             -- summa
    
    -- === METADATA ===
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. SUPPLIERS TABULA (Piegādātāju pamatdati)
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    registration_number VARCHAR(50) UNIQUE,
    vat_number VARCHAR(50),
    vat_payer_number VARCHAR(50),
    legal_address TEXT,
    
    -- Banking information
    primary_bank_name VARCHAR(255),
    primary_account_number VARCHAR(50),
    primary_swift_code VARCHAR(20),
    additional_banks TEXT,                         -- JSON array
    
    -- Learning metadata
    times_encountered INTEGER DEFAULT 1,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_score FLOAT DEFAULT 0.0,
    is_verified BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. ERROR_CORRECTIONS TABULA (AI mācīšanās)
CREATE TABLE error_corrections (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(id),
    
    field_name VARCHAR(100) NOT NULL,
    original_value TEXT,
    corrected_value TEXT,
    confidence_before FLOAT,
    confidence_after FLOAT,
    
    correction_type VARCHAR(50),
    correction_context TEXT,                       -- JSON context
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- 5. ALEMBIC VERSION TABULA (Migrāciju vēsture)
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

-- Indexes priekš labākas veiktspējas
CREATE INDEX idx_invoices_filename ON invoices(filename);
CREATE INDEX idx_invoices_supplier_name ON invoices(supplier_name);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_created_at ON invoices(created_at);
CREATE INDEX idx_products_invoice_id ON products(invoice_id);
CREATE INDEX idx_suppliers_name ON suppliers(name);
CREATE INDEX idx_suppliers_registration_number ON suppliers(registration_number);

-- Ievietojam sākotnējo Alembic versiju
INSERT INTO alembic_version (version_num) VALUES ('complete_initial');

COMMENT ON TABLE invoices IS 'Galvenā pavadzīmju tabula ar visiem template laukiem';
COMMENT ON TABLE products IS 'Produktu rindas no pavadzīmēm';
COMMENT ON TABLE suppliers IS 'Piegādātāju pamatdati autocomplete un mācīšanai';
COMMENT ON TABLE error_corrections IS 'AI mācīšanās no lietotāju labojumiem';
