# Atjauninātās SQLAlchemy modeli, kas atbilst jaunajai datubāzes shēmai

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Invoice(Base):
    __tablename__ = 'invoices'
    
    # === PAMATINFORMĀCIJA ===
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    
    # === FAILA INFORMĀCIJA (saderīgums ar esošo kodu) ===
    original_filename = Column(String)  # Jaunais lauks
    filename = Column(String)  # Vecais lauks (saderīgumam)
    uploaded_at = Column(DateTime, default=datetime.utcnow)  # Vecais lauks (saderīgumam)
    file_path = Column(String)  # Vecais lauks (saderīgumam)
    file_size = Column(Integer)  # Vecais lauks (saderīgumam)
    processed_at = Column(DateTime)
    
    # === DOKUMENTA INFORMĀCIJA ===
    document_type = Column(String)
    document_series = Column(String)
    document_number = Column(String)
    invoice_number = Column(String)
    invoice_date = Column(Date)
    delivery_date = Column(Date)
    service_delivery_date = Column(Date)
    contract_number = Column(String)
    
    # === PIEGĀDĀTĀJA INFORMĀCIJA ===
    supplier_name = Column(String)
    supplier_reg_number = Column(String) # Piegādātāja reģistrācijas numurs
    supplier_pvd_number = Column(String)
    supplier_vat_number = Column(String)
    supplier_address = Column(Text)
    issue_address = Column(Text)
    
    # === PIEGĀDĀTĀJA BANKAS (GALVENĀ) ===
    supplier_bank_name = Column(String)
    supplier_bank_account = Column(String)
    supplier_swift_code = Column(String)
    
    # === PIEGĀDĀTĀJA PAPILDU BANKAS (1-4) ===
    supplier_bank_name_1 = Column(String)
    supplier_account_number_1 = Column(String)
    supplier_swift_code_1 = Column(String)
    supplier_bank_name_2 = Column(String)
    supplier_account_number_2 = Column(String)
    supplier_swift_code_2 = Column(String)
    supplier_bank_name_3 = Column(String)
    supplier_account_number_3 = Column(String)
    supplier_swift_code_3 = Column(String)
    supplier_bank_name_4 = Column(String)
    supplier_account_number_4 = Column(String)
    supplier_swift_code_4 = Column(String)
    
    # === SAŅĒMĒJA INFORMĀCIJA ===
    recipient_name = Column(String)
    recipient_reg_number = Column(String)
    recipient_vat_number = Column(String)
    recipient_address = Column(Text)
    receiving_address = Column(Text)
    
    # === SAŅĒMĒJA BANKAS ===
    recipient_bank_name = Column(String)
    recipient_bank_account = Column(String)
    recipient_swift_code = Column(String)
    
    # === TRANSPORTA INFORMĀCIJA ===
    carrier_name = Column(String)
    carrier_vat_number = Column(String)
    vehicle_number = Column(String)
    driver_name = Column(String)
    
    # === DARĪJUMA INFORMĀCIJA ===
    transaction_type = Column(String)
    service_period = Column(String)
    payment_method = Column(String)
    notes = Column(Text)
    
    # === FINANŠU INFORMĀCIJA ===
    currency = Column(String)
    discount = Column(Float)
    total_with_discount = Column(Float)
    amount_with_discount = Column(Float)
    amount_without_discount = Column(Float)
    subtotal_amount = Column(Float)
    vat_amount = Column(Float)
    total_amount = Column(Float)
    
    # === PAPILDU INFORMĀCIJA ===
    issued_by_name = Column(String)
    payment_due_date = Column(Date)
    justification = Column(Text)
    total_issued = Column(Float)
    weight_kg = Column(Float)
    issued_by = Column(String)
    total_quantity = Column(Float)
    page_number = Column(String)
    
    # === SISTĒMAS INFORMĀCIJA ===
    extracted_text = Column(Text)  # OCR ekstraktētais teksts
    raw_text = Column(Text)  # Neapstrādātais OCR teksts
    ocr_strategy = Column(String)  # Izmantotā OCR stratēģija
    has_structure_analysis = Column(Boolean, default=False)  # Vai ir veikta struktūras analīze
    structure_confidence = Column(Float)  # Struktūras atpazīšanas precizitāte
    structure_analyzed_at = Column(DateTime)  # Kad veikta struktūras analīze
    document_structure = Column(Text)  # JSON - dokumenta struktūra
    started_at = Column(DateTime)  # Kad sākās apstrāde
    ocr_confidence = Column(Float)
    confidence_score = Column(Float)
    status = Column(String, default='processed')
    error_message = Column(Text)  # Kļūdas ziņojums ja apstrāde neizdevās


    # Saites uz citām tabulām
    products = relationship("Product", back_populates="invoice", cascade="all, delete-orphan")
    error_corrections = relationship("ErrorCorrection", back_populates="invoice", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Pārvērš modeli uz dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, Date):
                value = value.isoformat() if value else None
            result[column.name] = value
        return result

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    
    # === PRECES INFORMĀCIJA ===
    product_code = Column(String)
    product_name = Column(String)
    product_description = Column(Text)
    unit = Column(String)
    quantity = Column(Float)
    unit_price = Column(Float)
    discount_percent = Column(Float)
    discount_amount = Column(Float)
    net_amount = Column(Float)
    vat_rate = Column(Float)
    vat_amount = Column(Float)
    total_amount = Column(Float)
    
    # === PAPILDU LAUKI ===
    product_category = Column(String)
    weight = Column(Float)
    dimensions = Column(String)
    
    # Saite atpakaļ uz pavadzīmi
    invoice = relationship("Invoice", back_populates="products")
    
    def to_dict(self):
        """Pārvērš modeli uz dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            result[column.name] = value
        return result

class Supplier(Base):
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # === PIEGĀDĀTĀJA PAMATINFORMĀCIJA ===
    name = Column(String, nullable=False)
    registration_number = Column(String, unique=True)
    vat_payer_number = Column(String)
    vat_number = Column(String)
    legal_address = Column(Text)
    
    # === BANKAS INFORMĀCIJA ===
    bank_name = Column(String)
    account_number = Column(String)
    swift_code = Column(String)
    
    # === PAPILDU BANKAS (1-4) ===
    bank_name_1 = Column(String)
    account_number_1 = Column(String)
    swift_code_1 = Column(String)
    bank_name_2 = Column(String)
    account_number_2 = Column(String)
    swift_code_2 = Column(String)
    bank_name_3 = Column(String)
    account_number_3 = Column(String)
    swift_code_3 = Column(String)
    bank_name_4 = Column(String)
    account_number_4 = Column(String)
    swift_code_4 = Column(String)
    
    # === KONTAKTINFORMĀCIJA ===
    contact_person = Column(String)
    phone = Column(String)
    email = Column(String)
    website = Column(String)
    
    # === STATISTIKA ===
    invoices_count = Column(Integer, default=0)
    last_invoice_date = Column(Date)
    
    def to_dict(self):
        """Pārvērš modeli uz dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, Date):
                value = value.isoformat() if value else None
            result[column.name] = value
        return result

class ErrorCorrection(Base):
    __tablename__ = 'error_corrections'
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # === LABOJUMA INFORMĀCIJA ===
    field_name = Column(String, nullable=False)  # Kāds lauks tika labots
    original_value = Column(Text)  # Sākotnējā vērtība
    corrected_value = Column(Text)  # Labotā vērtība
    confidence_before = Column(Float)  # Confidence pirms labojuma
    confidence_after = Column(Float)  # Confidence pēc labojuma
    
    # === MĀCĪŠANĀS INFORMĀCIJA ===
    pattern_type = Column(String)  # Kāda veida pattern tika atpazīts
    improvement_applied = Column(Boolean, default=False)  # Vai uzlabojums tika pielietots
    learning_weight = Column(Float, default=1.0)  # Cik svarīgs šis labojums
    
    # === KONTEKSTS ===
    surrounding_text = Column(Text)  # Teksts ap lauku
    document_type = Column(String)  # Dokumenta veids
    supplier_context = Column(String)  # Piegādātāja konteksts
    
    # Saite atpakaļ uz pavadzīmi
    invoice = relationship("Invoice", back_populates="error_corrections")
    
    def to_dict(self):
        """Pārvērš modeli uz dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

# Eksportējam visus modeļus
__all__ = ['Base', 'Invoice', 'Product', 'Supplier', 'ErrorCorrection']
