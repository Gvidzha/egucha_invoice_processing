"""
COMPLETE DATABASE SCHEMA REDESIGN
Based on template.txt requirements with full field mapping
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Invoice(Base):
    """
    Complete invoice model with all template fields
    Pilnīgs pavadzīmes modelis ar visiem template laukiem
    """
    __tablename__ = "invoices"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # === FILE METADATA ===
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_size = Column(Integer)
    
    # === OCR METADATA ===
    extracted_text = Column(Text)  # OCR teksts
    raw_text = Column(Text)  # Sākotnējais teksts
    ocr_confidence = Column(Float)  # OCR kvalitāte
    ocr_strategy = Column(String(50))  # OCR stratēģija
    confidence_score = Column(Float)  # Kopējā kvalitāte
    
    # === DOCUMENT INFORMATION (Dokumenta informācija) ===
    document_type = Column(String(50))  # dok_tips
    document_series = Column(String(50))  # dok_serija  
    document_number = Column(String(100))  # dok_nr
    invoice_date = Column(Date)  # izrakstisanas_datums
    delivery_date = Column(Date)  # dok_piegades_datums
    service_delivery_date = Column(Date)  # pakalpojuma_piegades_datums
    contract_number = Column(String(100))  # liguma_nr
    
    # === SUPPLIER INFORMATION (Piegādātāja informācija) ===
    supplier_name = Column(String(255))  # piegadatajs
    supplier_registration_number = Column(String(50))  # piegadataja_reg_nr
    supplier_vat_payer_number = Column(String(50))  # piegadataja_pvd_nr
    supplier_vat_number = Column(String(50))  # piegadataja_pvn
    supplier_legal_address = Column(Text)  # piegadataja_jur_adrese
    issue_address = Column(Text)  # izsniegsanas_adrese
    supplier_confidence = Column(Float)  # AI confidence
    
    # === SUPPLIER BANKING (Piegādātāja bankas) ===
    # Primary bank
    supplier_bank_name = Column(String(255))  # piegadataja_banka
    supplier_account_number = Column(String(50))  # piegadataja_konts
    supplier_swift_code = Column(String(20))  # piegadataja_swift
    
    # Additional banks (1-4)
    supplier_bank_name_1 = Column(String(255))  # piegadataja_banka_1
    supplier_account_number_1 = Column(String(50))  # piegadataja_konts_1
    supplier_swift_code_1 = Column(String(20))  # piegadataja_swift_1
    
    supplier_bank_name_2 = Column(String(255))  # piegadataja_banka_2
    supplier_account_number_2 = Column(String(50))  # piegadataja_konts_2
    supplier_swift_code_2 = Column(String(20))  # piegadataja_swift_2
    
    supplier_bank_name_3 = Column(String(255))  # piegadataja_banka_3
    supplier_account_number_3 = Column(String(50))  # piegadataja_konts_3
    supplier_swift_code_3 = Column(String(20))  # piegadataja_swift_3
    
    supplier_bank_name_4 = Column(String(255))  # piegadataja_banka_4
    supplier_account_number_4 = Column(String(50))  # piegadataja_konts_4
    supplier_swift_code_4 = Column(String(20))  # piegadataja_swift_4
    
    # === RECIPIENT INFORMATION (Saņēmēja informācija) ===
    recipient_name = Column(String(255))  # sanemejs
    recipient_registration_number = Column(String(50))  # sanemeja_reg_nr
    recipient_vat_number = Column(String(50))  # sanemeja_pvn
    recipient_legal_address = Column(Text)  # sanemeja_jur_adrese
    receiving_address = Column(Text)  # sanemsanas_adrese
    recipient_confidence = Column(Float)  # AI confidence
    
    # === RECIPIENT BANKING (Saņēmēja bankas) ===
    recipient_bank_name = Column(String(255))  # sanemeja_banka
    recipient_account_number = Column(String(50))  # sanemeja_konts
    recipient_swift_code = Column(String(20))  # sanemeja_swift
    
    # === TRANSPORT INFORMATION (Transporta informācija) ===
    carrier_name = Column(String(255))  # parvadatajs
    carrier_vat_number = Column(String(50))  # parvadataja_pvn
    vehicle_number = Column(String(50))  # trans_lidz_nr
    driver_name = Column(String(255))  # auto_vaditajs
    
    # === TRANSACTION INFORMATION (Darījuma informācija) ===
    transaction_type = Column(String(100))  # darijums
    service_period = Column(String(100))  # pakalpojuma_periods
    payment_method = Column(String(100))  # apmaksas_veids
    notes = Column(Text)  # piezimes
    
    # === FINANCIAL INFORMATION (Finanšu informācija) ===
    currency = Column(String(10), default="EUR")  # curency
    discount = Column(Float)  # atlaide
    total_with_discount = Column(Float)  # kopā_ar_atlaidi
    amount_with_discount = Column(Float)  # summa_ar_atlaidi
    amount_without_discount = Column(Float)  # summa_bez_atlaides
    amount_without_vat = Column(Float)  # summa_bez_pvn
    vat_amount = Column(Float)  # pvn_summa
    total_amount = Column(Float)  # kopa_apmaksai
    
    # === ADDITIONAL INFORMATION (Papildu informācija) ===
    issued_by_name = Column(String(255))  # izsniedza_vards_uzvards
    payment_due_date = Column(Date)  # apmaksat_lidz
    justification = Column(Text)  # pamatojums
    total_issued = Column(Float)  # kopa_izsniegts
    weight_kg = Column(Float)  # svars_kg
    issued_by = Column(String(255))  # izsniedza
    total_quantity = Column(Float)  # daudzums_kopa
    page_number = Column(String(20))  # lapa
    
    # === STRUCTURE ANALYSIS (POSM 4.5) ===
    document_structure = Column(Text)  # JSON - dokumenta struktūra
    detected_zones = Column(Text)  # JSON - atpazītās zonas
    table_regions = Column(Text)  # JSON - tabulu reģioni
    structure_confidence = Column(Float)  # Struktūras kvalitāte
    has_structure_analysis = Column(Boolean, default=False)
    has_structure_aware_ocr = Column(Boolean, default=False)
    structure_analyzed_at = Column(DateTime)
    
    # === SYSTEM METADATA ===
    status = Column(String(20), default="uploaded")  # uploaded, processing, completed, error
    error_message = Column(Text)
    is_manually_corrected = Column(Boolean, default=False)
    correction_notes = Column(Text)
    
    # === TIMESTAMPS ===
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # === RELATIONSHIPS ===
    products = relationship("Product", back_populates="invoice", cascade="all, delete-orphan")


class Product(Base):
    """
    Product line items from template produkti section
    Produktu rindas no template produkti sadaļas
    """
    __tablename__ = "products"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key to Invoice
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    # === PRODUCT INFORMATION (Produkta informācija) ===
    product_sequence_number = Column(Integer)  # Nr
    product_delivery_date = Column(Date)  # piegades_datums
    product_code = Column(String(100))  # kods
    product_name = Column(String(255))  # prece
    product_usage = Column(String(255))  # izlietot
    incoming_batch_number = Column(String(100))  # ienak_partijas_nr
    unit_of_measure = Column(String(20))  # merv
    quantity = Column(Float)  # daudzums
    unit_price = Column(Float)  # cena
    product_discount = Column(Float)  # atlaide
    price_with_discount = Column(Float)  # cena_ar_atlaidi
    vat_rate = Column(Float)  # pvn_likme
    total_price = Column(Float)  # summa
    
    # === METADATA ===
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # === RELATIONSHIPS ===
    invoice = relationship("Invoice", back_populates="products")


class Supplier(Base):
    """
    Supplier master data for autocomplete and learning
    Piegādātāju pamatdati automātiskam papildināšanai un mācīšanai
    """
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    registration_number = Column(String(50), unique=True, index=True)
    vat_number = Column(String(50), index=True)
    vat_payer_number = Column(String(50), index=True)
    legal_address = Column(Text)
    
    # Banking information
    primary_bank_name = Column(String(255))
    primary_account_number = Column(String(50))
    primary_swift_code = Column(String(20))
    
    # Additional banks (JSON array)
    additional_banks = Column(Text)  # JSON array of bank objects
    
    # Learning metadata
    times_encountered = Column(Integer, default=1)
    last_seen = Column(DateTime, default=datetime.utcnow)
    confidence_score = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ErrorCorrection(Base):
    """
    AI learning from user corrections
    AI mācīšanās no lietotāju labojumiem
    """
    __tablename__ = "error_corrections"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    
    field_name = Column(String(100), nullable=False)
    original_value = Column(Text)
    corrected_value = Column(Text)
    confidence_before = Column(Float)
    confidence_after = Column(Float)
    
    correction_type = Column(String(50))  # field_correction, structure_correction, etc.
    correction_context = Column(Text)  # JSON - surrounding context
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))  # user identifier
