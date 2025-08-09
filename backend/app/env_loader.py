"""
Vides mainīgo ielāde no .env faila
"""

import os
from pathlib import Path
from typing import Optional

def load_env_file(env_file: str = ".env") -> None:
    """
    Ielādē vides mainīgos no .env faila
    
    Args:
        env_file: .env faila nosaukums
    """
    env_path = Path(__file__).parent / env_file
    
    if not env_path.exists():
        print(f"Warning: {env_file} file not found at {env_path}")
        return
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Izlaist komentārus un tukšas rindas
            if not line or line.startswith('#'):
                continue
                
            # Sadalīt pa key=value
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Noņemt pēdiņas ja ir
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Iestatīt vides mainīgo tikai ja nav jau iestatīts
                if key not in os.environ:
                    os.environ[key] = value

def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Iegūst vides mainīgo ar default vērtību
    
    Args:
        key: Mainīgā nosaukums
        default: Default vērtība
        
    Returns:
        str: Mainīgā vērtība vai default
    """
    return os.getenv(key, default)
