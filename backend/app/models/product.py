"""
Produkta (Product) datubāzes modelis
Satur produktu informāciju no pavadzīmēm
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Product(Base):
    __tablename__ = "products"
    
    # Primārā atslēga
    id = Column(Integer, primary_key=True, index=True)
    
    # Saite uz pavadzīmi
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    # Produkta informācija
    name = Column(String(500), nullable=False)
    description = Column(Text)
    product_code = Column(String(100))
    
    # Daudzumi un cenas
    quantity = Column(Float)
    unit = Column(String(50))  # gab, kg, l, utt.
    unit_price = Column(Float)
    total_price = Column(Float)
    
    # Nodokļi
    vat_rate = Column(Float)  # PVN likme
    vat_amount = Column(Float)  # PVN summa
    
    # Extraktēšanas kvalitāte
    extraction_confidence = Column(Float)
    is_manually_corrected = Column(Boolean, default=False)
    
    # Rindas pozīcija pavadzīmē
    line_number = Column(Integer)
    raw_text = Column(Text)  # Oriģinālais teksts no OCR
    
    # Saite uz pavadzīmi
    invoice = relationship("Invoice", back_populates="products")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', quantity={self.quantity}, price={self.total_price})>"
