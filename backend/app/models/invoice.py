"""
Pavadzīmes (Invoice) datubāzes modelis
Satur galveno informāciju par katru apstrādāto pavadzīmi
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Invoice(Base):
    __tablename__ = "invoices"
    
    # Primārā atslēga
    id = Column(Integer, primary_key=True, index=True)
    
    # Faila informācija
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    
    # OCR rezultāts
    extracted_text = Column(Text)  # OCR ekstraktētais un iztīrītais teksts
    raw_text = Column(Text)  # Neapstrādātais OCR teksts (deprecated)
    ocr_confidence = Column(Float)  # OCR pārliecības līmenis
    ocr_strategy = Column(String(50))  # Izmantotā OCR stratēģija
    confidence_score = Column(Float)  # Kopējais pārliecības līmenis
    
    # Ekstraktētā informācija
    document_number = Column(String(100))  # Pavadzīmes numurs
    
    # Piegādātāja informācija  
    supplier_name = Column(String(255))
    supplier_confidence = Column(Float)
    supplier_reg_number = Column(String(50))  # Piegādātāja reģ.nr.
    supplier_address = Column(Text)  # Piegādātāja adrese
    supplier_bank_account = Column(String(50))  # Piegādātāja bankas konts
    
    # Saņēmēja informācija
    recipient_name = Column(String(255))  # Saņēmēja uzņēmuma nosaukums
    recipient_reg_number = Column(String(50))  # Saņēmēja reģ.nr.
    recipient_address = Column(Text)  # Saņēmēja adrese
    recipient_bank_account = Column(String(50))  # Saņēmēja bankas konts
    recipient_confidence = Column(Float)  # Saņēmēja atpazīšanas kvalitāte
    
    # Datumi
    invoice_date = Column(DateTime)
    delivery_date = Column(DateTime)
    
    # Finanšu informācija
    total_amount = Column(Float)
    vat_amount = Column(Float)  # PVN summa
    currency = Column(String(10), default="EUR")
    subtotal_amount = Column(Float)  # Summa bez PVN
    
    # === JAUNĀS TEMPLATE SISTĒMAS PAPILDU LAUKI ===
    # Papildu dokumenta informācija
    document_type = Column(String(50))  # Dokumenta tips
    document_series = Column(String(50))  # Dokumenta sērija
    service_delivery_date = Column(DateTime)  # Pakalpojuma sniegšanas datums
    contract_number = Column(String(100))  # Līguma numurs
    
    # Papildu piegādātāja informācija
    supplier_vat_payer_number = Column(String(50))  # PVN maksātāja numurs
    supplier_vat_number = Column(String(50))  # PVN numurs
    issue_address = Column(Text)  # Izdošanas adrese
    supplier_bank_name = Column(String(255))  # Piegādātāja bankas nosaukums
    supplier_swift_code = Column(String(20))  # Piegādātāja SWIFT kods
    
    # Papildu saņēmēja informācija  
    recipient_vat_number = Column(String(50))  # Saņēmēja PVN numurs
    recipient_bank_name = Column(String(255))  # Saņēmēja bankas nosaukums
    recipient_account_number = Column(String(50))  # Saņēmēja konta numurs
    recipient_swift_code = Column(String(20))  # SWIFT kods
    receiving_address = Column(Text)  # Saņemšanas adrese
    
    # Transporta informācija
    carrier_name = Column(String(255))  # Pārvadātāja nosaukums
    carrier_vat_number = Column(String(50))  # Pārvadātāja PVN numurs
    vehicle_number = Column(String(50))  # Transportlīdzekļa numurs
    driver_name = Column(String(255))  # Vadītāja vārds
    
    # Papildu finanšu informācija
    discount = Column(Float)  # Atlaide
    total_with_discount = Column(Float)  # Kopsumma ar atlaidi
    amount_with_discount = Column(Float)  # Summa ar atlaidi
    amount_without_discount = Column(Float)  # Summa bez atlaides
    amount_without_vat = Column(Float)  # Summa bez PVN
    
    # Cita informācija
    transaction_type = Column(String(100))  # Darījuma tips
    service_period = Column(String(100))  # Pakalpojuma periods
    payment_method = Column(String(100))  # Apmaksas veids
    notes = Column(Text)  # Piezīmes
    issued_by_name = Column(String(255))  # Izdevēja vārds
    payment_due_date = Column(DateTime)  # Apmaksas termiņš
    justification = Column(Text)  # Pamatojums
    total_issued = Column(Float)  # Kopā izdots
    weight_kg = Column(Float)  # Svars kg
    issued_by = Column(String(255))  # Izdots no
    total_quantity = Column(Float)  # Kopējais daudzums
    page_number = Column(String(20))  # Lapas numurs
    
    # JSON/Complex lauki template sistēmai
    supplier_banks_json = Column(Text)  # JSON - banku informācija
    
    # Produktu sistēma - elastīga JSON struktūra
    product_items = Column(Text)  # JSON - pilna produktu informācija
    product_summary = Column(Text)  # Vienkāršs produktu kopsavilkums
    product_schema_version = Column(String(10), default="1.0")  # Shēmas versija
    
    # Document Structure Analysis - POSM 4.5
    document_structure = Column(Text)  # JSON - dokumenta struktūras analīze
    detected_zones = Column(Text)  # JSON - atrastās zonas (header, body, footer, summary)
    table_regions = Column(Text)  # JSON - tabulu reģioni ar robežām
    structure_confidence = Column(Float)  # Struktūras atpazīšanas precizitāte
    has_structure_analysis = Column(Boolean, default=False)  # Vai ir veikta struktūras analīze
    has_structure_aware_ocr = Column(Boolean, default=False)  # Vai ir veikts Structure-Aware OCR
    structure_analyzed_at = Column(DateTime)  # Kad veikta struktūras analīze
    
    # Apstrādes statuss
    status = Column(String(50), default="uploaded")  # uploaded, processing, completed, error
    error_message = Column(Text)
    
    # Lietotāja labojumi
    is_manually_corrected = Column(Boolean, default=False)
    correction_notes = Column(Text)
    
    # Laika zīmogi
    uploaded_at = Column(DateTime, default=datetime.utcnow)  # Kad fails tika augšupielādēts
    started_at = Column(DateTime)  # Kad sākās apstrāde
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Saites uz citām tabulām
    products = relationship("Product", back_populates="invoice")
    # corrections = relationship("ErrorCorrection", back_populates="invoice")
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, filename='{self.filename}', supplier='{self.supplier_name}')>"
