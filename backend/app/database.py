"""
SQLAlchemy datubāzes konfigurācija un sesiju pārvaldība (PostgreSQL)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL
from app.models import Base  # Importējam Base no models
import os

# PostgreSQL engine izveide ar standarta draiveri
# Use standard PostgreSQL connection without specifying driver
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Connection pool izmērs
    max_overflow=0,  # Maksimālais connection overflow
    pool_pre_ping=True,  # Pārbauda connection pirms lietošanas
    echo=False  # SQL query logging (development: True)
)

# Sesiju factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency injection function priekš FastAPI
    Atgriež datubāzes sesiju
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Izveido visas datubāzes tabulas
    Jāizsauc aplikācijas startēšanas laikā
    """
    print("🔧 Pārbaudam datubāzes tabulu statusu...")
    
    # Importējam jaunos modeļus no complete_models
    from app.models import Invoice, Product, Supplier, ErrorCorrection, Base
    print(f"📋 Jaunie modeļi importēti. Reģistrētās tabulas: {list(Base.metadata.tables.keys())}")
    
    # Pārbaudām un izveidojam tabulas (tikai ja nepastāv)
    print("🏗️ Pārbaudam un izveidojam trūkstošās tabulas...")
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("✅ Datubāzes tabulu pārbaude pabeigta! (Esošās tabulas netika skartas)")

def drop_tables():
    """
    Dzēš visas datubāzes tabulas (izmanto tikai development!)
    """
    from app.models import Invoice, Product, Supplier, ErrorCorrection, Base
    Base.metadata.drop_all(bind=engine)
