"""
Piegādātāja (Supplier) datubāzes modelis
Satur piegādātāju informāciju un mācīšanās datus
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from app.database import Base
from datetime import datetime

class Supplier(Base):
    __tablename__ = "suppliers"
    
    # Primārā atslēga
    id = Column(Integer, primary_key=True, index=True)
    
    # Piegādātāja pamata informācija
    name = Column(String(255), nullable=False, unique=True)
    name_variations = Column(Text)  # JSON ar dažādiem nosaukuma variantiem
    
    # Kontaktinformācija
    address = Column(Text)
    phone = Column(String(50))
    email = Column(String(255))
    registration_number = Column(String(100))
    vat_number = Column(String(50))
    
    # Atpazīšanas patterns
    recognition_patterns = Column(Text)  # JSON ar regex pattern sarakstu
    confidence_threshold = Column(Float, default=0.8)
    
    # Statistika un mācīšanās
    times_processed = Column(Integer, default=0)
    last_seen = Column(DateTime)
    accuracy_rate = Column(Float, default=0.0)
    
    # Statuss
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Vai ir manuāli apstiprināts
    
    # Laika zīmogi
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', times_processed={self.times_processed})>"
