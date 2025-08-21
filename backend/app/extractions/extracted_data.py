from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import date


@dataclass
class ExtractedData:
    """Ekstraktēto datu konteiners"""
    # Pamatinformācija
    document_number: Optional[str] = None
    
    # Piegādātāja informācija
    supplier_name: Optional[str] = None
    supplier_confidence: float = 0.0
    supplier_reg_number: Optional[str] = None
    supplier_address: Optional[str] = None
    supplier_bank_account: Optional[str] = None
    
    # Saņēmēja informācija  
    recipient_name: Optional[str] = None
    recipient_reg_number: Optional[str] = None
    recipient_address: Optional[str] = None
    recipient_bank_account: Optional[str] = None
    recipient_confidence: float = 0.0
    
    # Datumi
    invoice_date: Optional[date] = None
    delivery_date: Optional[date] = None
    
    # Finanšu dati
    total_amount: Optional[float] = None
    subtotal_amount: Optional[float] = None  # Summa bez PVN
    vat_amount: Optional[float] = None
    currency: str = "EUR"
    
    # Produktu rindas
    products: List[Dict] = None
    
    # Kvalitātes metriki
    confidence_scores: Dict[str, float] = None
    
    @property
    def confidence_score(self) -> float:
        """Aprēķina vispārējo confidence score kā vidējo vērtību"""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores.values()) / len(self.confidence_scores)
    
    raw_extracted_text: Optional[str] = None
    
    def __post_init__(self):
        if self.products is None:
            self.products = []
        if self.confidence_scores is None:
            self.confidence_scores = {}
            
    def to_dict(self) -> Dict:
        """Konvertē uz dictionary API atgriešanai"""
        return {
            "document_number": self.document_number,
            "supplier_name": self.supplier_name,
            "supplier_confidence": self.supplier_confidence,
            "reg_number": self.reg_number,
            "address": self.address,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "total_amount": self.total_amount,
            "vat_amount": self.vat_amount,
            "currency": self.currency,
            "products": self.products,
            "confidence_scores": self.confidence_scores
        }
