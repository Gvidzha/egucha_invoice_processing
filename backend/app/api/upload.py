"""
Failu augšupielādes API endpoints
Atbild par pavadzīmju failu saņemšanu un sākotnējo validāciju
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from datetime import datetime

from app.database import get_db
from app.models import Invoice  # Jauns imports no complete_models
from app.config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Augšupielādē pavadzīmes failu
    
    Args:
        file: Augšupielādējamais fails
        db: Datubāzes sesija
    
    Returns:
        dict: Faila informācija un upload statuss ar file_id
    """
    # Validēt faila tipu
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nav norādīts faila nosaukums")
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Neatbalstīts faila tips. Atļautie: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validēt faila izmēru
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"Fails pārāk liels. Maksimālais izmērs: {MAX_FILE_SIZE/1024/1024:.1f}MB"
        )
    
    # Izveidot unikālu faila nosaukumu
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename
    
    # Saglabāt failu uz diska
    UPLOAD_DIR.mkdir(exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Izveidot ierakstu datubāzē ar jaunajiem lauku nosaukumiem
    invoice = Invoice(
        original_filename=file.filename,  # Jauns lauks
        filename=file.filename,  # Vecais lauks (saderīgumam)
        file_path=str(file_path),  # Pilnais ceļš uz failu
        file_size=len(content),  # Faila izmērs
        uploaded_at=datetime.utcnow(),  # Ielādes laiks
        # status tiks uzstādīts automātiski uz 'processed' (noklusējuma vērtība)
    )
    
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    
    return {
        "message": "Fails veiksmīgi augšupielādēts",
        "file_id": invoice.id,
        "filename": file.filename,
        "file_size": len(content),
        "status": invoice.status or "uploaded"  # Izmantojam datubāzes vērtību
    }

@router.post("/upload/multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Augšupielādē vairākus pavadzīmju failus vienlaicīgi
    
    Args:
        files: Failu saraksts
        db: Datubāzes sesija
    
    Returns:
        dict: Batch upload rezultāts
    """
    # TODO: Implementēt batch upload loģiku
    # TODO: Validēt katru failu
    # TODO: Saglabāt visus failus
    # TODO: Izveidot datubāzes ierakstus
    
    return {
        "message": "Multiple upload endpoint - TODO: implement",
        "files_count": len(files)
    }

@router.delete("/upload/{file_id}")
async def delete_uploaded_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    Dzēš augšupielādēto failu
    
    Args:
        file_id: Faila ID datubāzē
        db: Datubāzes sesija
    
    Returns:
        dict: Dzēšanas statuss
    """
    # TODO: Implementēt faila dzēšanas loģiku
    # TODO: Dzēst gan no diska, gan no datubāzes
    # TODO: Pārbaudīt, vai fails nav jau apstrādāts
    
    return {"message": f"Delete file {file_id} - TODO: implement"}
