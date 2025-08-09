#!/usr/bin/env python3
"""
Ātrā migrācijas skripts - dzēš un atveido tabulas ar jaunajiem laukiem
"""

import sys
import os
from pathlib import Path

# Pievienot app ceļu
sys.path.append(str(Path(__file__).parent / "app"))

from app.database import engine, drop_tables, create_tables

def main():
    print("🔄 ĀTRĀ MIGRĀCIJA - dzēšam un izveidojam tabulas ar jaunajiem laukiem")
    
    try:
        # Dzēšam vecās tabulas
        print("🗑️ Dzēšam vecās tabulas...")
        drop_tables()
        
        # Izveidojam jaunās tabulas
        print("🏗️ Izveidojam jaunās tabulas...")
        create_tables()
        
        print("✅ MIGRĀCIJA PABEIGTA!")
        
    except Exception as e:
        print(f"❌ KĻŪDA: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
