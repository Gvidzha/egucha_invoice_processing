"""
Kļūdu labojumu (Error Correction) datubāzes modelis
Satur mašīnmācīšanās datus un kļūdu vārdnīcu
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class ErrorCorrection(Base):
    __tablename__ = "error_corrections"
    
    # Primārā atslēga
    id = Column(Integer, primary_key=True, index=True)
    
    # Saite uz pavadzīmi (nav obligāta)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    
    # Kļūdas informācija
    error_type = Column(String(100), nullable=False)  # supplier, product, date, amount
    field_name = Column(String(100))  # konkrētais lauks
    
    # Oriģinālā un labotā vērtība
    original_value = Column(Text, nullable=False)
    corrected_value = Column(Text, nullable=False)
    
    # Konteksts
    surrounding_text = Column(Text)  # Teksts ap kļūdu
    confidence_before = Column(Float)  # Pārliecība pirms labojuma
    confidence_after = Column(Float)   # Pārliecība pēc labojuma
    
    # Pattern informācija
    matched_pattern = Column(Text)  # Regex pattern kas sakrita
    suggested_pattern = Column(Text)  # Ieteiktais jauns pattern
    
    # Lietotāja informācija
    correction_source = Column(String(50), default="manual")  # manual, auto, suggested
    user_feedback = Column(Text)  # Lietotāja komentāri
    
    # Mācīšanās statuss
    is_applied_to_model = Column(Boolean, default=False)
    application_date = Column(DateTime)
    effectiveness_score = Column(Float)  # Cik efektīvs ir bijis šis labojums
    
    # Laika zīmogi
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Saite uz pavadzīmi
    # invoice = relationship("Invoice", back_populates="corrections")
    
    def __repr__(self):
        return f"<ErrorCorrection(id={self.id}, type='{self.error_type}', original='{self.original_value}', corrected='{self.corrected_value}')>"
