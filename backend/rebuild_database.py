#!/usr/bin/env python3
"""
DATUBĀZES PILNĪGA PĀRVEIDE
Izveido jaunu datubāzi ar pilnīgo template atbilstošo shēmu
"""

import os
import sys
from pathlib import Path

# Pievienot backend ceļu
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from complete_schema import Base, Invoice, Product, Supplier, ErrorCorrection

# Iegūstam DATABASE_URL no environment
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://invoice_user:secure_password123@localhost:5432/invoice_processing_fresh")

def create_new_complete_database():
    """Izveido jaunu datubāzi ar pilnīgo shēmu"""
    
    print("🚀 SĀKAM DATUBĀZES PILNĪGO PĀRVEIDI")
    print("=" * 50)
    
    # Izveidojam jaunu datubāzes nosaukumu
    new_db_name = "invoice_processing_complete"
    
    # Savienojamies ar PostgreSQL serveri (bez konkrētas datubāzes)
    server_url = DATABASE_URL.rsplit('/', 1)[0]  # Noņemam datubāzes nosaukumu
    engine_server = create_engine(f"{server_url}/postgres", isolation_level="AUTOCOMMIT")
    
    try:
        with engine_server.connect() as conn:
            # Beigšanas existing connections
            conn.execute(text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = :db_name AND pid != pg_backend_pid()"), 
                        {"db_name": new_db_name})
            
            # Dzēšam datubāzi ja eksistē
            conn.execute(text(f"DROP DATABASE IF EXISTS {new_db_name}"))
            print(f"🗑️  Dzēsta veca datubāze: {new_db_name}")
            
            # Izveidojam jaunu datubāzi
            conn.execute(text(f"CREATE DATABASE {new_db_name}"))
            print(f"🆕 Izveidota jauna datubāze: {new_db_name}")
        
        # Savienojamies ar jauno datubāzi
        new_db_url = f"{server_url}/{new_db_name}"
        engine_new = create_engine(new_db_url)
        
        # Izveidojam visas tabulas
        Base.metadata.create_all(bind=engine_new)
        print(f"✅ Izveidotas visas tabulas jaunajā datubāzē")
        
        # Parādām izveidotās tabulas
        with engine_new.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"📋 Izveidotās tabulas: {', '.join(tables)}")
            
        # Parādām invoice tabulas kolonnas
        with engine_new.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'invoices' 
                ORDER BY ordinal_position
            """))
            columns = list(result)
            print(f"\n📊 Invoice tabulas kolonnas ({len(columns)} kopā):")
            for col_name, data_type, max_length in columns[:10]:  # Parādām pirmas 10
                length_info = f"({max_length})" if max_length else ""
                print(f"   - {col_name}: {data_type}{length_info}")
            if len(columns) > 10:
                print(f"   ... un vēl {len(columns) - 10} kolonnas")
        
        print(f"\n🎉 DATUBĀZES PĀRVEIDE PABEIGTA!")
        print(f"📝 Jaunā datubāzes URL: {new_db_url}")
        print(f"⚠️  SVARĪGI: Atjauniniet .env failu ar jauno DATABASE_URL!")
        
        return new_db_url
        
    except Exception as e:
        print(f"❌ Kļūda: {e}")
        return None
    finally:
        engine_server.dispose()


def update_env_file(new_db_url):
    """Atjaunina .env failu ar jauno datubāzes URL"""
    env_file = Path(".env")
    
    if env_file.exists():
        content = env_file.read_text()
        # Aizstāj DATABASE_URL rindiņu
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('DATABASE_URL='):
                lines[i] = f"DATABASE_URL={new_db_url}"
                break
        
        env_file.write_text('\n'.join(lines))
        print(f"✅ .env fails atjaunināts ar jauno DATABASE_URL")
    else:
        print(f"⚠️  .env fails nav atrasts - atjauniniet manuāli!")


if __name__ == "__main__":
    new_url = create_new_complete_database()
    
    if new_url:
        update_env_file(new_url)
        print(f"\n🚀 NĀKAMIE SOĻI:")
        print(f"1. Restartējiet backend serveri")
        print(f"2. Testējiet jauno sistēmu ar pilnīgo lauku atbalstu") 
        print(f"3. Visiem template laukiem tagad ir atbilstošas datubāzes kolonnas!")
    else:
        print(f"❌ Datubāzes izveidošana neizdevās")
