"""
Korekciju API endpoints
Atbild par lietotāja labojumu saglabāšanu un mācīšanos
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
from datetime import datetime

from app.database import get_db
from app.models import Invoice

logger = logging.getLogger(__name__)
router = APIRouter()


@router.put("/update/{file_id}")
async def update_invoice_with_corrections_endpoint(
    file_id: int,
    corrections: dict,
    db: Session = Depends(get_db)
):
    """
    Atjaunina invoice ar lietotāja labojumiem un veic automātisku mācīšanos
    
    Args:
        file_id: Faila ID datubāzē
        corrections: Lietotāja labojumi
        db: Datubāzes sesija
        
    Returns:
        dict: Atjauninātie dati un mācīšanās rezultāti
    """
    try:
        # Iegūt invoice no datubāzes
        invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice nav atrasts")
        
        logger.info(f"Atjaunina invoice {file_id} ar labojumiem: {list(corrections.keys())}")
        
        # Saglabāt vecākas vērtības salīdzināšanai
        old_values = {
            "document_number": invoice.document_number,
            "supplier_name": invoice.supplier_name,
            "recipient_name": invoice.recipient_name,
            "total_amount": float(invoice.total_amount) if invoice.total_amount else None,
            "vat_amount": float(invoice.vat_amount) if invoice.vat_amount else None,
            "supplier_reg_number": invoice.supplier_reg_number,
            "recipient_reg_number": invoice.recipient_reg_number,
            "supplier_address": invoice.supplier_address,
            "recipient_address": invoice.recipient_address,
        }
        
        # Atjaunināt datus
        await update_invoice_with_corrections(db, invoice, corrections)
        
        # Refresh no datubāzes lai iegūtu jaunās vērtības
        db.refresh(invoice)
        
        # Jaunie dati
        new_values = {
            "document_number": invoice.document_number,
            "supplier_name": invoice.supplier_name,
            "recipient_name": invoice.recipient_name,
            "total_amount": float(invoice.total_amount) if invoice.total_amount else None,
            "vat_amount": float(invoice.vat_amount) if invoice.vat_amount else None,
            "supplier_reg_number": invoice.supplier_reg_number,
            "recipient_reg_number": invoice.recipient_reg_number,
            "supplier_address": invoice.supplier_address,
            "recipient_address": invoice.recipient_address,
        }
        
        # Automātiska mācīšanās fona režīmā (ja ir OCR teksts)
        learning_results = None
        if invoice.extracted_text:
            try:
                from app.services.hybrid_service import hybrid_service
                from app.services.extraction_service import ExtractedData
                
                extracted_data = ExtractedData()
                extracted_data.document_number = old_values["document_number"]
                extracted_data.supplier_name = old_values["supplier_name"]
                extracted_data.recipient_name = old_values["recipient_name"]
                extracted_data.total_amount = old_values["total_amount"]
                
                learning_results = await hybrid_service.learn_from_corrections(
                    invoice.extracted_text,
                    extracted_data,
                    corrections
                )
                logger.info(f"Automātiska mācīšanās pabeigta: {learning_results}")
                
            except Exception as e:
                logger.warning(f"Automātiskā mācīšanās neizdevās: {e}")
        
        return {
            "status": "success",
            "message": "Dati veiksmīgi atjaunināti",
            "file_id": file_id,
            "updated_fields": list(corrections.keys()),
            "old_values": old_values,
            "new_values": new_values,
            "learning_results": learning_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Datu atjaunināšanas kļūda: {e}")
        raise HTTPException(status_code=500, detail=f"Atjaunināšanas kļūda: {str(e)}")


async def update_invoice_with_corrections(db: Session, invoice: Invoice, corrections: dict):
    """Atjaunina invoice ar lietotāja labojumiem"""
    
    field_mapping = {
        'document_number': 'document_number',
        'supplier_name': 'supplier_name', 
        'recipient_name': 'recipient_name',
        'supplier_reg_number': 'supplier_reg_number',
        'recipient_reg_number': 'recipient_reg_number',
        'total_amount': 'total_amount',
        'vat_amount': 'vat_amount',
        'supplier_address': 'supplier_address',
        'recipient_address': 'recipient_address',
        'currency': 'currency'
    }
    
    for field, value in corrections.items():
        if field in field_mapping and value is not None:
            db_field = field_mapping[field]
            
            # Speciāla apstrāde dažādiem laukiem
            if field in ['total_amount', 'vat_amount'] and isinstance(value, str):
                try:
                    value = float(value.replace(',', '.'))
                except ValueError:
                    continue
            
            # Datuma apstrāde
            if field.endswith('_date') and isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value).date()
                except ValueError:
                    continue
            
            setattr(invoice, db_field, value)
    
    # Atjaunina labošanas laiku
    invoice.processed_at = datetime.utcnow()
    db.commit()


@router.post("/learn/{file_id}")
async def learn_from_corrections(
    file_id: int,
    corrections: dict,
    db: Session = Depends(get_db)
):
    """
    Mācās no lietotāja labojumiem bez datu atjaunināšanas
    
    Args:
        file_id: Faila ID datubāzē
        corrections: Lietotāja labojumi
        db: Datubāzes sesija
        
    Returns:
        dict: Mācīšanās rezultāti
    """
    try:
        # Iegūt invoice no datubāzes
        invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice nav atrasts")
        
        if not invoice.extracted_text:
            raise HTTPException(status_code=400, detail="Nav OCR teksta mācīšanās")
        
        logger.info(f"Sākam mācīšanos no labojumiem invoice {file_id}")
        
        # Mācīšanās ar hibridāo servisu
        try:
            from app.services.hybrid_service import hybrid_service
            from app.services.extraction_service import ExtractedData
            
            extracted_data = ExtractedData()
            extracted_data.document_number = invoice.document_number
            extracted_data.supplier_name = invoice.supplier_name
            extracted_data.recipient_name = invoice.recipient_name
            extracted_data.total_amount = float(invoice.total_amount) if invoice.total_amount else None
            
            # Mācīšanās process
            learning_results = await hybrid_service.learn_from_corrections(
                invoice.extracted_text,
                extracted_data,
                corrections
            )
            
            logger.info(f"Mācīšanās pabeigta: {learning_results}")
            
            return {
                "status": "success",
                "message": "Mācīšanās no labojumiem veiksmīga",
                "learning_results": learning_results,
                "corrected_fields": list(corrections.keys()),
                "improvements": learning_results.get("combined_improvements", 0)
            }
            
        except Exception as e:
            logger.error(f"Hibridās mācīšanās kļūda: {e}")
            return {
                "status": "partial_success",
                "message": "Mācīšanās daļēji veiksmīga",
                "error": str(e)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mācīšanās kļūda: {e}")
        raise HTTPException(status_code=500, detail=f"Mācīšanās kļūda: {str(e)}")


@router.get("/learning/statistics")
async def get_learning_statistics():
    """
    Atgriež mācīšanās statistiku
    
    Returns:
        dict: Statistika par mācīšanos
    """
    try:
        from app.services.hybrid_service import hybrid_service
        
        stats = await hybrid_service.get_extraction_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Statistikas iegūšanas kļūda: {e}")
        return {
            "status": "error",
            "message": "Nevar iegūt statistiku",
            "error": str(e)
        }


@router.get("/learning/debug/{file_id}")
async def get_learning_debug_info(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    Iegūst mācīšanās debug informāciju konkrētam failam
    
    Args:
        file_id: Faila ID datubāzē
        db: Datubāzes sesija
        
    Returns:
        dict: Debug informācija par mācīšanos
    """
    try:
        # Iegūt invoice no datubāzes
        invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice nav atrasts")
        
        # Iegūt debug informāciju no NER servisa
        from app.services.ner_service import ner_service
        
        debug_info = await ner_service.get_debug_info(invoice.extracted_text or "")
        
        return {
            "status": "success",
            "file_id": file_id,
            "filename": invoice.original_filename,
            "debug_info": debug_info
        }
        
    except Exception as e:
        logger.error(f"Debug informācijas iegūšanas kļūda: {e}")
        return {
            "status": "error",
            "message": "Nevar iegūt debug informāciju",
            "error": str(e)
        }


@router.post("/learning/simulate/{file_id}")
async def simulate_correction_learning(
    file_id: int,
    corrections: dict,
    db: Session = Depends(get_db)
):
    """
    Simulē mācīšanos bez saglabāšanas (preview režīms)
    
    Args:
        file_id: Faila ID datubāzē
        corrections: Lietotāja labojumi
        db: Datubāzes sesija
        
    Returns:
        dict: Simulācijas rezultāti
    """
    try:
        # Iegūt invoice no datubāzes
        invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice nav atrasts")
        
        if not invoice.extracted_text:
            raise HTTPException(status_code=400, detail="Nav OCR teksta simulācijai")
        
        logger.info(f"Simulējam mācīšanos failam {file_id}")
        
        # Simulācija ar NER servisu
        from app.services.ner_service import ner_service
        
        simulation_results = await ner_service.simulate_learning(
            invoice.extracted_text,
            corrections
        )
        
        return {
            "status": "success",
            "message": "Mācīšanās simulācija pabeigta",
            "simulation_results": simulation_results,
            "corrected_fields": list(corrections.keys())
        }
        
    except Exception as e:
        logger.error(f"Simulācijas kļūda: {e}")
        return {
            "status": "error",
            "message": "Simulācija neizdevās",
            "error": str(e)
        }


@router.get("/field-suggestions/{field_name}")
async def get_field_suggestions(
    field_name: str,
    db: Session = Depends(get_db)
):
    """
    Iegūst lauku ieteikumus autocomplete funkcionalitātei
    
    Args:
        field_name: Lauka nosaukums
        db: Datubāzes sesija
        
    Returns:
        dict: Lauka ieteikumu saraksts
    """
    try:
        # Iegūt ieteikumus no NER servisa
        from app.services.ner_service import ner_service
        
        suggestions = await ner_service.get_field_suggestions(field_name)
        
        return {
            "status": "success",
            "field_name": field_name,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Ieteikumu iegūšanas kļūda: {e}")
        return {
            "status": "error",
            "message": "Nevar iegūt ieteikumus",
            "error": str(e),
            "suggestions": []
        }
