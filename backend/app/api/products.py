"""
Products API - Endpoints for product data management
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import logging

from app.database import get_db
from app.models import Invoice
from app.services.product_template_service import ProductTemplateManager
from app.services.product_utils import ProductDataProcessor, validate_products
from pydantic import BaseModel, Field

# Logger
logger = logging.getLogger(__name__)

# Router
router = APIRouter(tags=["products"])

# Pydantic models
class ProductItem(BaseModel):
    product_name: str = Field(..., description="Product name")
    quantity: float = Field(..., description="Product quantity")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    unit_price: float = Field(..., description="Price per unit")
    total_price: float = Field(..., description="Total price")
    discount: Optional[float] = Field(None, description="Discount amount")
    vat_rate: Optional[float] = Field(None, description="VAT rate percentage")
    vat_amount: Optional[float] = Field(None, description="VAT amount")
    description: Optional[str] = Field(None, description="Additional description")
    product_code: Optional[str] = Field(None, description="Product code/SKU")

class ProductsUpdateRequest(BaseModel):
    invoice_id: int = Field(..., description="Invoice ID")
    products: List[ProductItem] = Field(..., description="List of products")
    document_type: str = Field(default="invoice", description="Document type")

class ProductsResponse(BaseModel):
    success: bool
    message: str
    products: List[Dict[str, Any]]
    total_products: int
    summary: str

class ProductConfigResponse(BaseModel):
    document_types: List[str]
    base_fields: List[Dict[str, Any]]
    optional_fields: List[Dict[str, Any]]
    document_specific_fields: Dict[str, List[Dict[str, Any]]]

# Initialize services
template_manager = ProductTemplateManager()
data_processor = ProductDataProcessor()

@router.get("/config", response_model=ProductConfigResponse)
async def get_product_config():
    """Atgriež produktu konfigurāciju frontend vajadzībām"""
    try:
        config = {
            "document_types": template_manager.get_supported_document_types(),
            "base_fields": template_manager.get_base_fields(),
            "optional_fields": template_manager.get_optional_fields(),
            "document_specific_fields": {}
        }
        
        # Pievienojam document-specific laukus
        for doc_type in config["document_types"]:
            config["document_specific_fields"][doc_type] = template_manager.get_document_specific_fields(doc_type)
        
        return ProductConfigResponse(**config)
    except Exception as e:
        logger.error(f"Failed to get product config: {e}")
        raise HTTPException(status_code=500, detail=f"Config error: {str(e)}")

@router.get("/fields/{document_type}")
async def get_fields_for_document(document_type: str):
    """Atgriež visus laukus konkrētam dokumenta tipam"""
    try:
        if document_type not in template_manager.get_supported_document_types():
            raise HTTPException(status_code=400, detail=f"Unsupported document type: {document_type}")
        
        fields = template_manager.get_fields_for_document(document_type)
        return {
            "document_type": document_type,
            "fields": fields,
            "total_fields": len(fields)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get fields for {document_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Fields error: {str(e)}")

@router.get("/schema/{document_type}")
async def get_product_schema(document_type: str):
    """Atgriež JSON shēmu produktu validācijai"""
    try:
        if document_type not in template_manager.get_supported_document_types():
            raise HTTPException(status_code=400, detail=f"Unsupported document type: {document_type}")
        
        schema = template_manager.create_product_schema(document_type)
        return {
            "document_type": document_type,
            "schema": schema
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get schema for {document_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Schema error: {str(e)}")

@router.get("/{invoice_id}")
async def get_products(invoice_id: int, db: Session = Depends(get_db)):
    """Atgriež produktus konkrētam rēķinam"""
    try:
        # Atrodam rēķinu
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Iegūstam produktu datus
        products_data = []
        summary = "Nav produktu"
        
        if invoice.product_items:
            try:
                parsed_data = data_processor.products_from_json(invoice.product_items)
                products_data = parsed_data["products"]
            except Exception as e:
                logger.warning(f"Failed to parse product JSON for invoice {invoice_id}: {e}")
        
        if invoice.product_summary:
            summary = invoice.product_summary
        elif products_data:
            summary = data_processor.create_product_summary(products_data)
        
        return ProductsResponse(
            success=True,
            message="Products retrieved successfully",
            products=products_data,
            total_products=len(products_data),
            summary=summary
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get products for invoice {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.put("/update")
async def update_products(request: ProductsUpdateRequest, db: Session = Depends(get_db)):
    """Atjaunina produktus rēķinam"""
    try:
        # Atrodam rēķinu
        invoice = db.query(Invoice).filter(Invoice.id == request.invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Konvertējam Pydantic models uz dict
        products_data = [product.dict() for product in request.products]
        
        # Validējam produktus
        validation_errors = validate_products(products_data, request.document_type)
        if any(validation_errors.values()):
            return {
                "success": False,
                "message": "Validation errors found",
                "errors": validation_errors,
                "products": products_data,
                "total_products": len(products_data),
                "summary": "Validation failed"
            }
        
        # Normalizējam produktus
        normalized_products = data_processor.normalize_products(products_data, request.document_type)
        
        # Saglabājam JSON formātā
        schema_version = invoice.product_schema_version or "1.0"
        products_json = data_processor.products_to_json(normalized_products, schema_version)
        summary = data_processor.create_product_summary(normalized_products)
        
        # Atjauninām datubāzi
        invoice.product_items = products_json
        invoice.product_summary = summary
        invoice.is_manually_corrected = True
        
        db.commit()
        
        logger.info(f"Updated products for invoice {request.invoice_id}: {len(normalized_products)} products")
        
        return ProductsResponse(
            success=True,
            message=f"Successfully updated {len(normalized_products)} products",
            products=normalized_products,
            total_products=len(normalized_products),
            summary=summary
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update products for invoice {request.invoice_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update error: {str(e)}")

@router.post("/validate")
async def validate_products_endpoint(products: List[ProductItem], document_type: str = "invoice"):
    """Validē produktu datus bez saglabāšanas"""
    try:
        if document_type not in template_manager.get_supported_document_types():
            raise HTTPException(status_code=400, detail=f"Unsupported document type: {document_type}")
        
        # Konvertējam uz dict
        products_data = [product.dict() for product in products]
        
        # Validējam
        validation_errors = validate_products(products_data, document_type)
        normalized_products = data_processor.normalize_products(products_data, document_type)
        
        is_valid = not any(validation_errors.values())
        
        return {
            "valid": is_valid,
            "errors": validation_errors,
            "normalized_products": normalized_products,
            "total_products": len(products_data),
            "document_type": document_type
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate products: {e}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

@router.get("/mappings/latvian")
async def get_latvian_mappings():
    """Atgriež Latvian → English mappings produktu laukiem"""
    try:
        mappings = template_manager.get_latvian_mappings()
        return {
            "mappings": mappings,
            "total_mappings": len(mappings)
        }
    except Exception as e:
        logger.error(f"Failed to get Latvian mappings: {e}")
        raise HTTPException(status_code=500, detail=f"Mappings error: {str(e)}")

@router.delete("/{invoice_id}")
async def clear_products(invoice_id: int, db: Session = Depends(get_db)):
    """Dzēš visus produktus no rēķina"""
    try:
        # Atrodam rēķinu
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Dzēšam produktu datus
        invoice.product_items = None
        invoice.product_summary = "Nav produktu"
        invoice.is_manually_corrected = True
        
        db.commit()
        
        logger.info(f"Cleared products for invoice {invoice_id}")
        
        return {
            "success": True,
            "message": "Products cleared successfully",
            "invoice_id": invoice_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear products for invoice {invoice_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Clear error: {str(e)}")

# Debug endpoints
@router.get("/debug/{invoice_id}/raw")
async def get_raw_product_data(invoice_id: int, db: Session = Depends(get_db)):
    """Debug endpoint - atgriež raw JSON datus"""
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        return {
            "invoice_id": invoice_id,
            "product_items_raw": invoice.product_items,
            "product_summary": invoice.product_summary,
            "product_schema_version": invoice.product_schema_version
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get raw product data for invoice {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")
