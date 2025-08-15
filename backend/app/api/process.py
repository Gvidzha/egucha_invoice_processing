"""
OCR apstrādes API endpoints
Atbild par pavadzīmju apstrādi ar OCR un datu ekstraktēšanu
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
import asyncio
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

from app.database import get_db
from app.models import Invoice, Product  # Jauns imports no complete_models
from app.services.ocr.ocr_main import OCRService
from app.services.extraction_service import ExtractionService
from app.services.hybrid_service import HybridExtractionService
from app.services.document_structure_service import DocumentStructureAnalyzer
from app.config import UPLOAD_DIR
import json

def convert_int64(obj):
    if isinstance(obj, dict):
        return {k: convert_int64(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_int64(i) for i in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_int64(i) for i in obj)
    elif isinstance(obj, set):
        return [convert_int64(i) for i in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    return obj

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/process/{file_id}/structure-aware-ocr")
async def process_structure_aware_ocr(
    file_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    POSM 4.5 Week 3: Veic Structure-Aware OCR esošam failam
    
    Args:
        file_id: Faila ID
        background_tasks: Background tasks
        db: Datubāzes sesija
    
    Returns:
        dict: Structure-Aware OCR sākšanas statuss
    """
    invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Fails nav atrasts")
    
    file_path = Path(invoice.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fails neeksistē diskā")
    
    # Sāk structure-aware OCR background procesā
    background_tasks.add_task(process_structure_aware_ocr_background, file_id, str(file_path))
    
    return convert_int64({
        "message": "Structure-Aware OCR sākts",
        "file_id": file_id,
        "status": "processing"
    })

async def process_structure_aware_ocr_background(file_id: int, file_path: str):
    """
    POSM 4.5 Week 3: Background process priekš Structure-Aware OCR
    
    Args:
        file_id: Faila ID
        file_path: Ceļš uz failu
    """
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        logger.info(f"Sāk Structure-Aware OCR background process: {file_id}")
        
        # Inicializē OCR servisu
        ocr_service = OCRService()
        await ocr_service.initialize()
        
        # Veic Structure-Aware OCR
        result = await ocr_service.extract_text_with_structure(file_path)
        
        if result['success']:
            structure_result = result['structure_aware_result']
            
            # Atjaunina datubāzes ierakstu
            invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
            if invoice:
                # Saglabā Structure-Aware OCR rezultātus
                invoice.ocr_text = structure_result['enhanced_text']  # Enhanced text
                invoice.raw_ocr_text = structure_result['text']  # Original OCR text
                invoice.structure_confidence = structure_result['confidence']
                
                # Saglabā struktūras informāciju
                invoice.document_structure = json.dumps(structure_result['structure'])
                invoice.detected_zones = json.dumps(structure_result['zone_results'])
                invoice.table_regions = json.dumps(structure_result['table_results'])
                
                # Atzīmē ka ir structure-aware results
                invoice.has_structure_analysis = True
                invoice.has_structure_aware_ocr = True  # Jaunslauka atzīme
                invoice.structure_analyzed_at = datetime.utcnow()
                invoice.processed_at = datetime.utcnow()
                
                # Metadata
                metadata = invoice.metadata or {}
                metadata.update({
                    'structure_aware_ocr': {
                        'zones_detected': result['metadata']['zones_detected'],
                        'tables_detected': result['metadata']['tables_detected'],
                        'overall_confidence': result['metadata']['overall_confidence'],
                        'processing_time': result['processing_time'],
                        'processed_at': datetime.utcnow().isoformat()
                    }
                })
                invoice.metadata = metadata
                
                db.commit()
                
                logger.info(f"Structure-Aware OCR pabeigts: file_id={file_id}, "
                           f"confidence={structure_result['confidence']:.2f}, "
                           f"zones={result['metadata']['zones_detected']}, "
                           f"tables={result['metadata']['tables_detected']}")
        else:
            logger.error(f"Structure-Aware OCR neizdevās failam {file_id}: {result['error']}")
            
            # Atzīmē kļūdu
            invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
            if invoice:
                invoice.error_message = f"Structure-Aware OCR kļūda: {result['error']}"
                db.commit()
                
    except Exception as e:
        logger.error(f"Kļūda Structure-Aware OCR background process failam {file_id}: {e}")
        
        # Atzīmē kļūdu datubāzē
        try:
            invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
            if invoice:
                invoice.error_message = f"Structure-Aware OCR exception: {str(e)}"
                db.commit()
        except Exception as db_error:
            logger.error(f"Nevarēja saglabāt kļūdu datubāzē: {db_error}")
    finally:
        db.close()

@router.post("/process/{file_id}/analyze-structure")
async def analyze_document_structure(
    file_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Veic Document Structure Analysis esošam failam
    
    Args:
        file_id: Faila ID
        background_tasks: Background tasks
        db: Datubāzes sesija
    
    Returns:
        dict: Structure analysis sākšanas statuss
    """
    invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Fails nav atrasts")
    
    file_path = Path(invoice.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fails neeksistē diskā")
    
    # Palaist structure analysis background task
    background_tasks.add_task(process_structure_analysis, file_id)
    
    logger.info(f"Structure analysis sākta failam: {invoice.original_filename} (ID: {file_id})")
    
    return convert_int64({
        "message": f"Structure analysis sākta failam: {invoice.original_filename}",
        "file_id": file_id,
        "filename": invoice.original_filename,
        "status": "structure_analysis_started"
    })

async def process_structure_analysis(file_id: int):
    """
    Background task Document Structure Analysis
    
    Args:
        file_id: Faila ID datubāzē
    """
    from app.database import SessionLocal
    
    db = SessionLocal()
    
    try:
        # Iegūt invoice no datubāzes
        invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
        if not invoice:
            logger.error(f"Invoice ar ID {file_id} nav atrasts")
            return
            
        logger.info(f"Sākam Structure Analysis failam: {invoice.original_filename}")
        
        # Faila ceļš no datubāzes
        file_path = Path(invoice.file_path)
        if not file_path.exists():
            logger.error(f"Fails neeksistē: {file_path}")
            return
        
        # Inicializējam Document Structure Analyzer
        structure_analyzer = DocumentStructureAnalyzer()
        
        # Veicam structure analysis
        structure_result = await structure_analyzer.analyze_document(str(file_path))
        
        if structure_result is None:
            logger.error(f"Structure analysis neizdevās failam {invoice.original_filename}")
            return
        
        # Konvertējam structure objektus uz JSON
        structure_dict = {
            'image_width': structure_result.image_width,
            'image_height': structure_result.image_height,
            'zones': [
                {
                    'type': zone.type,
                    'bounds': {
                        'x1': zone.bounds.x1, 'y1': zone.bounds.y1,
                        'x2': zone.bounds.x2, 'y2': zone.bounds.y2
                    },
                    'confidence': zone.confidence
                } for zone in structure_result.zones
            ],
            'tables': [
                {
                    'bounds': {
                        'x1': table.bounds.x1, 'y1': table.bounds.y1,
                        'x2': table.bounds.x2, 'y2': table.bounds.y2
                    },
                    'confidence': table.confidence,
                    'cell_count': (
                        sum(len(row) if isinstance(row, list) else 1 for row in table.cells)
                        if isinstance(table.cells, list) else 1
                    )
                } for table in structure_result.tables
            ],
            'text_blocks': [
                {
                    'x1': block.x1, 'y1': block.y1,
                    'x2': block.x2, 'y2': block.y2
                } for block in structure_result.text_blocks
            ],
            'confidence': structure_result.confidence,
            'processing_time_ms': structure_result.processing_time_ms
        }
        
        # Saglabājam Structure Analysis rezultātu
        invoice.document_structure = json.dumps(structure_dict)
        invoice.detected_zones = json.dumps(structure_dict['zones'])
        invoice.table_regions = json.dumps(structure_dict['tables'])
        invoice.structure_confidence = structure_result.confidence
        invoice.has_structure_analysis = True
        invoice.structure_analyzed_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Structure Analysis pabeigts: {len(structure_result.zones)} zonas, "
                   f"{len(structure_result.tables)} tabulas, confidence: {structure_result.confidence:.2f}")
        
    except Exception as e:
        logger.error(f"Kļūda structure analysis failam {file_id}: {e}")
    finally:
        db.close()


async def update_invoice_with_corrections(db: Session, invoice: Invoice, corrections: dict):
    """Atjaunina invoice ar lietotāja labojumiem"""
    
    field_mapping = {
        'invoice_number': 'invoice_number',
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
                    from datetime import datetime
                    value = datetime.fromisoformat(value).date()
                except ValueError:
                    continue
            
            setattr(invoice, db_field, value)
    
    # Atjaunina labošanas laiku
    invoice.processed_at = datetime.utcnow()
    db.commit()


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
        
        return convert_int64({
            "status": "success",
            "statistics": stats
        })
        
    except Exception as e:
        logger.error(f"Statistikas iegūšanas kļūda: {e}")
        return convert_int64({
            "status": "error",
            "message": "Nevar iegūt statistiku",
            "error": str(e)
        })


@router.get("/learning/export")
async def export_learning_data():
    """
    Eksportē visus mācīšanās datus
    
    Returns:
        dict: Visi mācīšanās dati
    """
    try:
        from app.services.hybrid_service import hybrid_service
        
        export_data = await hybrid_service.export_learning_data()
        
        return convert_int64({
            "status": "success",
            "export_data": export_data
        })
        
    except Exception as e:
        logger.error(f"Datu eksportēšanas kļūda: {e}")
        return convert_int64({
            "status": "error",
            "message": "Nevar eksportēt datus",
            "error": str(e)
        })


async def process_invoice_ocr(file_id: int):
    """
    Background task OCR apstrādei
    
    Args:
        file_id: Faila ID datubāzē
    """
    from app.database import SessionLocal
    
    db = SessionLocal()
    
    try:
        # Iegūt invoice no datubāzes
        invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
        if not invoice:
            logger.error(f"Invoice ar ID {file_id} nav atrasts")
            return
            
        logger.info(f"Sākam OCR apstrādi failam: {invoice.original_filename}")
        
        # Faila ceļš no datubāzes
        file_path = Path(invoice.file_path)
        if not file_path.exists():
            logger.error(f"Fails neeksistē: {file_path}")
            invoice.status = "error"
            invoice.error_message = f"Fails neeksistē: {invoice.file_path}"
            db.commit()
            return
        
        # Inicializējam servisus
        ocr_service = OCRService()
        await ocr_service.initialize()
        
        # Inicializējam Document Structure Analyzer
        structure_analyzer = DocumentStructureAnalyzer()
        
        # Izvēlēti servisu (default: hybrid, fallback: regex)
        try:
            extraction_service = HybridExtractionService()
            use_hybrid = True
            logger.info("Izmanto hibridāo ekstraktēšanas servisu (regex + NER)")
        except Exception as e:
            logger.warning(f"Hibridais serviss nav pieejams, izmanto regex: {e}")
            extraction_service = ExtractionService()
            use_hybrid = False
        
        # 🆕 PARALLEL EXECUTION: OCR + Structure Analysis vienlaicīgi
        logger.info(f"Sākam parallel OCR + Structure analysis: {file_path}")
        
        # Async parallel execution
        tasks = [
            ocr_service.extract_text_adaptive(str(file_path)),
            structure_analyzer.analyze_document(str(file_path))
        ]
        
        ocr_result, structure_result = await asyncio.gather(*tasks)
        
        # OCR rezultātu validācija
        if not ocr_result.get('success') or not ocr_result.get('cleaned_text'):
            logger.error(f"OCR neizdevās failam {invoice.original_filename}")
            invoice.status = "error"
            invoice.error_message = "OCR apstrāde neizdevās"
            invoice.ocr_confidence = 0.0
            db.commit()
            return
            
        # Structure analysis rezultātu validācija
        if structure_result is None:
            logger.warning(f"Structure analysis neizdevās failam {invoice.original_filename}, turpina bez struktūras datiem")
            structure_result = None
        
        # Saglabājam OCR rezultātu
        invoice.extracted_text = ocr_result['cleaned_text']
        invoice.ocr_confidence = ocr_result.get('confidence_score', 0.0)
        invoice.ocr_strategy = ocr_result.get('strategy_used', 'unknown')
        
        # 🆕 Saglabājam Structure Analysis rezultātu
        if structure_result:
            # Konvertējam structure objektus uz JSON
            structure_dict = {
                'image_width': structure_result.image_width,
                'image_height': structure_result.image_height,
                'zones': [
                    {
                        'type': zone.type,
                        'bounds': {
                            'x1': zone.bounds.x1, 'y1': zone.bounds.y1,
                            'x2': zone.bounds.x2, 'y2': zone.bounds.y2
                        },
                        'confidence': zone.confidence
                    } for zone in structure_result.zones
                ],
                'tables': [
                    {
                        'bounds': {
                            'x1': table.bounds.x1, 'y1': table.bounds.y1,
                            'x2': table.bounds.x2, 'y2': table.bounds.y2
                        },
                        'confidence': table.confidence,
                        'cell_count': (
                            sum(len(row) if isinstance(row, list) else 1 for row in table.cells)
                            if isinstance(table.cells, list) else 1
                        )
                    } for table in structure_result.tables
                ],
                'text_blocks': [
                    {
                        'x1': block.x1, 'y1': block.y1,
                        'x2': block.x2, 'y2': block.y2
                    } for block in structure_result.text_blocks
                ],
                'confidence': structure_result.confidence,
                'processing_time_ms': structure_result.processing_time_ms
            }
            
            invoice.document_structure = json.dumps(structure_dict)
            invoice.detected_zones = json.dumps(structure_dict['zones'])
            invoice.table_regions = json.dumps(structure_dict['tables'])
            invoice.structure_confidence = structure_result.confidence
            invoice.has_structure_analysis = True
            invoice.structure_analyzed_at = datetime.utcnow()
            
            logger.info(f"Structure analysis pabeigts: {len(structure_result.zones)} zonas, "
                       f"{len(structure_result.tables)} tabulas, confidence: {structure_result.confidence:.2f}")
        else:
            invoice.has_structure_analysis = False
            
        logger.info(f"OCR + Structure analysis pabeigts ar OCR confidence: {invoice.ocr_confidence:.2f}")
        logger.info(f"Structure confidence: {invoice.structure_confidence:.2f}" if structure_result else "Nav structure datu")
        
        # Datu ekstraktēšana (hybrid vai regex)
        logger.info(f"Sākam datu ekstraktēšanu ar {'hybrid' if use_hybrid else 'regex'} servisu")
        extracted_data = await extraction_service.extract_invoice_data(ocr_result['cleaned_text'])
        
        # Saglabājam ekstraktētos datus
        invoice.invoice_number = extracted_data.invoice_number
        
        # Piegādātāja informācija
        invoice.supplier_name = extracted_data.supplier_name
        invoice.supplier_confidence = extracted_data.supplier_confidence
        invoice.supplier_reg_number = extracted_data.supplier_reg_number
        invoice.supplier_address = extracted_data.supplier_address  
        invoice.supplier_bank_account = extracted_data.supplier_bank_account
        
        # Saņēmēja informācija
        invoice.recipient_name = extracted_data.recipient_name
        invoice.recipient_reg_number = extracted_data.recipient_reg_number
        invoice.recipient_address = extracted_data.recipient_address
        invoice.recipient_bank_account = extracted_data.recipient_bank_account
        invoice.recipient_confidence = extracted_data.recipient_confidence
        
        # Datumi
        invoice.invoice_date = extracted_data.invoice_date  
        invoice.delivery_date = extracted_data.delivery_date
        
        # Finanšu dati
        invoice.total_amount = extracted_data.total_amount
        invoice.subtotal_amount = extracted_data.subtotal_amount
        invoice.vat_amount = extracted_data.vat_amount
        invoice.currency = extracted_data.currency
        invoice.confidence_score = extracted_data.confidence_score
        
        # Saglabāt produktu rindas datubāzē
        if extracted_data.products:
            await save_product_lines(db, invoice.id, extracted_data.products)
        
        invoice.status = "completed"
        invoice.processed_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Apstrāde pabeigta veiksmīgi: {invoice.original_filename}")
        logger.info(f"Ekstraktētie dati: Nr:{invoice.invoice_number}, "
                   f"Piegādātājs:{invoice.supplier_name}, Summa:{invoice.total_amount}")
        
    except Exception as e:
        logger.error(f"Kļūda apstrādājot failu {file_id}: {e}")
        if invoice:
            invoice.status = "error" 
            invoice.error_message = str(e)
            db.commit()
    finally:
        db.close()

@router.post("/process/{file_id}")
async def process_invoice(
    file_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Sāk pavadzīmes apstrādi ar OCR
    
    Args:
        file_id: Faila ID datubāzē
        background_tasks: FastAPI background tasks
        db: Datubāzes sesija
    
    Returns:
        dict: Apstrādes sākšanas statuss
    """
    # Pārbaudīt, vai fails eksistē
    invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Fails nav atrasts")
    
    # Pārbaudīt faila statusu
    if invoice.status == "processing":
        raise HTTPException(status_code=400, detail="Fails jau tiek apstrādāts")
    
    if invoice.status == "completed":
        return convert_int64({
            "message": "Fails jau ir apstrādāts",
            "file_id": file_id,
            "status": "already_completed",
            "invoice_number": invoice.invoice_number,
            "supplier_name": invoice.supplier_name,
            "total_amount": float(invoice.total_amount) if invoice.total_amount else None,
            "confidence_score": float(invoice.confidence_score) if invoice.confidence_score else None
        })
    
    # Atjaunināt statusu uz "processing"
    invoice.status = "processing"
    invoice.started_at = datetime.utcnow()
    db.commit()
    
    # Palaist background task OCR apstrādei
    background_tasks.add_task(process_invoice_ocr, file_id)
    
    logger.info(f"Apstrāde sākta failam: {invoice.original_filename} (ID: {file_id})")
    
    return convert_int64({
        "message": f"Apstrāde sākta failam: {invoice.original_filename}",
        "file_id": file_id,
        "filename": invoice.original_filename,
        "status": "processing_started"
    })

@router.get("/process/{file_id}/status")
async def get_processing_status(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    Iegūst apstrādes statusu
    
    Args:
        file_id: Faila ID
        db: Datubāzes sesija
    
    Returns:
        dict: Pašreizējais apstrādes statuss
    """
    invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Fails nav atrasts")
    
    response = {
        "file_id": file_id,
        "filename": invoice.original_filename,
        "status": invoice.status,
        "uploaded_at": invoice.uploaded_at.isoformat() if invoice.uploaded_at else None,
        "started_at": invoice.started_at.isoformat() if invoice.started_at else None,
        "processed_at": invoice.processed_at.isoformat() if invoice.processed_at else None,
    }
    
    # Pievienot OCR informāciju, ja pieejama
    if invoice.ocr_confidence is not None:
        response["ocr_confidence"] = float(invoice.ocr_confidence)
        response["ocr_strategy"] = invoice.ocr_strategy
    
    # 🆕 Pievienot Structure Analysis informāciju, ja pieejama
    if invoice.has_structure_analysis:
        response["structure_confidence"] = float(invoice.structure_confidence) if invoice.structure_confidence else None
        response["structure_analyzed_at"] = invoice.structure_analyzed_at.isoformat() if invoice.structure_analyzed_at else None
        response["has_structure_analysis"] = True
        
        # Parse structure data for summary
        if invoice.document_structure:
            try:
                structure_data = json.loads(invoice.document_structure)
                response["structure_summary"] = {
                    "zones_count": len(structure_data.get('zones', [])),
                    "tables_count": len(structure_data.get('tables', [])),
                    "text_blocks_count": len(structure_data.get('text_blocks', [])),
                    "processing_time_ms": structure_data.get('processing_time_ms')
                }
            except json.JSONDecodeError:
                logger.warning(f"Invalid structure JSON for invoice {file_id}")
    else:
        response["has_structure_analysis"] = False
    
    # Pievienot ekstraktētos datus, ja apstrāde pabeigta
    if invoice.status == "completed":
        # Pievienojam datus augšējā līmenī frontend vajadzībām
        response["invoice_number"] = invoice.invoice_number
        
        # Piegādātāja informācija
        response["supplier_name"] = invoice.supplier_name
        response["supplier_reg_number"] = invoice.supplier_reg_number
        response["supplier_address"] = invoice.supplier_address
        response["supplier_bank_account"] = invoice.supplier_bank_account
        
        # Saņēmēja informācija
        response["recipient_name"] = invoice.recipient_name
        response["recipient_reg_number"] = invoice.recipient_reg_number
        response["recipient_address"] = invoice.recipient_address
        response["recipient_bank_account"] = invoice.recipient_bank_account
        
        # Datumi un finanses
        response["invoice_date"] = invoice.invoice_date.isoformat() if invoice.invoice_date else None
        response["delivery_date"] = invoice.delivery_date.isoformat() if invoice.delivery_date else None
        response["total_amount"] = float(invoice.total_amount) if invoice.total_amount else None
        response["subtotal_amount"] = float(invoice.subtotal_amount) if invoice.subtotal_amount else None
        response["vat_amount"] = float(invoice.vat_amount) if invoice.vat_amount else None
        response["currency"] = invoice.currency
        response["confidence_score"] = float(invoice.confidence_score) if invoice.confidence_score else None
        
        # Produktu rindas
        products = db.query(Product).filter(Product.invoice_id == file_id).all()
        response["products"] = [
            {
                "name": p.name,
                "quantity": float(p.quantity) if p.quantity else None,
                "unit": p.unit,
                "unit_price": float(p.unit_price) if p.unit_price else None,
                "total_price": float(p.total_price) if p.total_price else None,
                "product_code": p.product_code,
                "line_number": p.line_number
            } for p in products
        ]
        
        # Saglabājam arī extracted_data objektu saderībai
        response["extracted_data"] = {
            "invoice_number": invoice.invoice_number,
            "supplier_name": invoice.supplier_name,
            "supplier_reg_number": invoice.supplier_reg_number,
            "recipient_name": invoice.recipient_name,
            "recipient_reg_number": invoice.recipient_reg_number,
            "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            "delivery_date": invoice.delivery_date.isoformat() if invoice.delivery_date else None,
            "total_amount": float(invoice.total_amount) if invoice.total_amount else None,
            "subtotal_amount": float(invoice.subtotal_amount) if invoice.subtotal_amount else None,
            "vat_amount": float(invoice.vat_amount) if invoice.vat_amount else None,
            "currency": invoice.currency,
            "confidence_score": float(invoice.confidence_score) if invoice.confidence_score else None,
            "products": response["products"]
        }
    
    # Pievienot kļūdas informāciju, ja ir
    if invoice.status == "error" and invoice.error_message:
        response["error_message"] = invoice.error_message
    logger.info(f"RESPONSE DATA: {response}")
    return convert_int64(response)

@router.post("/process/batch")
async def process_multiple_invoices(
    file_ids: list[int],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Apstrādā vairākas pavadzīmes vienlaicīgi
    
    Args:
        file_ids: Failu ID saraksts
        background_tasks: Background tasks
        db: Datubāzes sesija
    
    Returns:
        dict: Batch apstrādes statuss
    """
    # TODO: Validēt visus file_ids
    # TODO: Sākt batch apstrādi
    # TODO: Atgriezt batch job ID
    
    return convert_int64({
        "message": f"Batch processing started for {len(file_ids)} files - TODO: implement",
        "file_ids": file_ids,
        "batch_id": "placeholder"
    })

@router.get("/process/{file_id}/structure")
async def get_structure_analysis(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    Iegūst pilnu Document Structure Analysis rezultātu
    
    Args:
        file_id: Faila ID
        db: Datubāzes sesija
    
    Returns:
        dict: Structure analysis rezultāti
    """
    invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Fails nav atrasts")
    
    if not invoice.has_structure_analysis:
        raise HTTPException(status_code=404, detail="Structure analysis nav veikta šim failam")
    
    # Parse structure data
    structure_data = None
    zones_data = None
    tables_data = None
    
    try:
        if invoice.document_structure:
            structure_data = json.loads(invoice.document_structure)
        if invoice.detected_zones:
            zones_data = json.loads(invoice.detected_zones)
        if invoice.table_regions:
            tables_data = json.loads(invoice.table_regions)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse structure JSON for invoice {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Structure data ir bojāta")
    
    return convert_int64({
        "file_id": file_id,
        "filename": invoice.original_filename,
        "structure_confidence": float(invoice.structure_confidence) if invoice.structure_confidence else None,
        "structure_analyzed_at": invoice.structure_analyzed_at.isoformat() if invoice.structure_analyzed_at else None,
        "document_structure": structure_data,
        "detected_zones": zones_data,
        "table_regions": tables_data,
        "summary": {
            "zones_count": len(zones_data) if zones_data else 0,
            "tables_count": len(tables_data) if tables_data else 0,
            "text_blocks_count": len(structure_data.get('text_blocks', [])) if structure_data else 0,
            "processing_time_ms": structure_data.get('processing_time_ms') if structure_data else None
        }
    })

@router.post("/process/{file_id}/retry")
async def retry_processing(
    file_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Atkārto neveiksmīgu apstrādi
    
    Args:
        file_id: Faila ID
        background_tasks: Background tasks
        db: Datubāzes sesija
    
    Returns:
        dict: Retry statuss
    """
    invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Fails nav atrasts")
    
    if invoice.status not in ["error", "failed"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Nevar atkārtot apstrādi failam ar statusu: {invoice.status}"
        )
    
    # Atiestatīt statusu un notīrīt iepriekšējos datus
    invoice.status = "processing"
    invoice.error_message = None
    invoice.started_at = datetime.utcnow()
    invoice.processed_at = None
    
    # Notīrīt iepriekšējos rezultātus
    invoice.extracted_text = None
    invoice.ocr_confidence = None
    invoice.ocr_strategy = None
    invoice.confidence_score = None
    
    db.commit()
    
    # Palaist apstrādi no jauna
    background_tasks.add_task(process_invoice_ocr, file_id)
    
    logger.info(f"Atkārtota apstrāde sākta failam: {invoice.original_filename} (ID: {file_id})")
    
    return convert_int64({
        "message": f"Atkārtota apstrāde sākta failam: {invoice.original_filename}",
        "file_id": file_id,
        "filename": invoice.original_filename,
        "status": "retry_started"
    })

@router.get("/process/{file_id}/results")
async def get_processing_results(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    Iegūst detalizētus apstrādes rezultātus
    
    Args:
        file_id: Faila ID
        db: Datubāzes sesija
    
    Returns:
        dict: Detalizēti apstrādes rezultāti
    """
    invoice = db.query(Invoice).filter(Invoice.id == file_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Fails nav atrasts")
    
    if invoice.status != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Apstrāde nav pabeigta. Pašreizējais statuss: {invoice.status}"
        )
    
    return convert_int64({
        "file_id": file_id,
        "filename": invoice.original_filename,
        "processing_info": {
            "uploaded_at": invoice.uploaded_at.isoformat() if invoice.uploaded_at else None,
            "started_at": invoice.started_at.isoformat() if invoice.started_at else None,
            "processed_at": invoice.processed_at.isoformat() if invoice.processed_at else None,
            "ocr_confidence": float(invoice.ocr_confidence) if invoice.ocr_confidence else None,
            "ocr_strategy": invoice.ocr_strategy,
            "overall_confidence": float(invoice.confidence_score) if invoice.confidence_score else None
        },
        "extracted_data": {
            "invoice_number": invoice.invoice_number,
            "supplier_name": invoice.supplier_name,
            "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            "delivery_date": invoice.delivery_date.isoformat() if invoice.delivery_date else None,
            "total_amount": float(invoice.total_amount) if invoice.total_amount else None,
            "vat_amount": float(invoice.vat_amount) if invoice.vat_amount else None,
            "currency": invoice.currency,
            "reg_number": invoice.reg_number,
            "address": invoice.address,
            "bank_account": invoice.bank_account
        },
        "raw_ocr_text": invoice.extracted_text[:1000] + "..." if invoice.extracted_text and len(invoice.extracted_text) > 1000 else invoice.extracted_text
    })

async def save_product_lines(db: Session, invoice_id: int, products: list) -> None:
    """
    Saglabā produktu rindas datubāzē
    
    Args:
        db: Datubāzes sesija
        invoice_id: Pavadzīmes ID
        products: Produktu saraksts
    """
    try:
        # Izdzēst esošos produktus šim invoice (ja ir)
        db.query(Product).filter(Product.invoice_id == invoice_id).delete()
        
        # Pievienot jaunos produktus
        for product_data in products:
            product = Product(
                invoice_id=invoice_id,
                name=product_data.get('name', ''),
                description=product_data.get('description'),
                product_code=product_data.get('product_code'),
                quantity=product_data.get('quantity'),
                unit=product_data.get('unit'),
                unit_price=product_data.get('unit_price'),
                total_price=product_data.get('total_price'),
                vat_rate=product_data.get('vat_rate'),
                vat_amount=product_data.get('vat_amount'),
                extraction_confidence=product_data.get('extraction_confidence', 0.0),
                line_number=product_data.get('line_number'),
                raw_text=product_data.get('raw_text')
            )
            db.add(product)
        
        db.commit()
        logger.info(f"Saglabāti {len(products)} produkti priekš invoice {invoice_id}")
        
    except Exception as e:
        logger.error(f"Produktu saglabāšanas kļūda: {e}")
        db.rollback()
        raise


@router.post("/learn/{file_id}")
async def learn_from_corrections(
    file_id: int,
    corrections: dict,
    db: Session = Depends(get_db)
):
    """
    Mācās no lietotāja labojumiem un uzlabo ekstraktēšanas kvalitāti
    
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
            
            # Izveidot ekstraktētos datus objektu (vienkāršoti)
            from app.services.extraction_service import ExtractedData
            
            extracted_data = ExtractedData()
            extracted_data.invoice_number = invoice.invoice_number
            extracted_data.supplier_name = invoice.supplier_name
            extracted_data.recipient_name = invoice.recipient_name
            extracted_data.total_amount = float(invoice.total_amount) if invoice.total_amount else None
            
            # Mācīšanās process
            learning_results = await hybrid_service.learn_from_corrections(
                invoice.extracted_text,
                extracted_data,
                corrections
            )
            
            # Atjaunināt datus datubāzē ar labojumiem
            await update_invoice_with_corrections(db, invoice, corrections)
            
            logger.info(f"Mācīšanās pabeigta: {learning_results}")
            
            return convert_int64({
                "status": "success",
                "message": "Mācīšanās no labojumiem veiksmīga",
                "learning_results": learning_results,
                "corrected_fields": list(corrections.keys()),
                "improvements": learning_results.get("combined_improvements", 0)
            })
            
        except Exception as e:
            logger.error(f"Hibridās mācīšanās kļūda: {e}")
            # Fallback - vienkārši atjaunina datus
            await update_invoice_with_corrections(db, invoice, corrections)
            
            return convert_int64({
                "status": "partial_success",
                "message": "Dati atjaunināti, bet mācīšanās nav pilnībā veiksmīga",
                "error": str(e)
            })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mācīšanās kļūda: {e}")
        raise HTTPException(status_code=500, detail=f"Mācīšanās kļūda: {str(e)}")


async def update_invoice_with_corrections(db: Session, invoice: Invoice, corrections: dict):
    """Atjaunina invoice ar lietotāja labojumiem"""
    
    field_mapping = {
        'invoice_number': 'invoice_number',
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
                    from datetime import datetime
                    value = datetime.fromisoformat(value).date()
                except ValueError:
                    continue
            
            setattr(invoice, db_field, value)
    
    # Atjaunina labošanas laiku
    invoice.processed_at = datetime.utcnow()
    db.commit()


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
        
        return convert_int64({
            "status": "success",
            "statistics": stats
        })

    except Exception as e:
        logger.error(f"Statistikas iegūšanas kļūda: {e}")
        return convert_int64({
            "status": "error",
            "message": "Nevar iegūt statistiku",
            "error": str(e)
        })


@router.get("/learning/export")
async def export_learning_data():
    """
    Eksportē visus mācīšanās datus
    
    Returns:
        dict: Visi mācīšanās dati
    """
    try:
        from app.services.hybrid_service import hybrid_service
        
        export_data = await hybrid_service.export_learning_data()
        
        return convert_int64({
            "status": "success",
            "export_data": export_data
        })

    except Exception as e:
        logger.error(f"Datu eksportēšanas kļūda: {e}")
        return convert_int64({
            "status": "error", 
            "message": "Nevar eksportēt datus",
            "error": str(e)
        })
