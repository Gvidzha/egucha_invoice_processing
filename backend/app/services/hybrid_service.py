"""
Hibridais ekstraktēšanas serviss
Apvieno regex un NER pieejas ar mācīšanās iespējām
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import date

from app.services.extraction_service import ExtractionService, ExtractedData
from app.services.ner_service import NERService, NEREntity

from app.utils.ocr_utils import load_ocr_corrections, correct_ocr_text


logger = logging.getLogger(__name__)

class HybridExtractionService:
    """Hibridais serviss - regex + NER ar mācīšanos"""
    
    def __init__(self):
        self.regex_service = ExtractionService()
        self.ner_service = NERService()
        self.ocr_corrections = load_ocr_corrections("backend/app/ocr_corrections/clean_ocr_vardnica.txt")
        
    async def extract_invoice_data(self, ocr_text: str, use_ner: bool = True) -> ExtractedData:
        # Izlabo OCR tekstu pirms ekstrakcijas
        cleaned_text = correct_ocr_text(ocr_text, self.ocr_corrections)
        """
        Ekstraktē datus izmantojot hybrid pieeju
        
        Args:
            ocr_text: OCR teksts
            use_ner: Vai izmantot NER (default: True)
            
        Returns:
            ExtractedData: Ekstraktētie dati
        """
        try:
            logger.info(f"Hibridā ekstraktēšana: NER={'ieslēgts' if use_ner else 'izslēgts'}")
            
            # 1. SĀKUMĀ izmanto NER (lai izmantotu mācīšanos!)
            ner_entities = []
            if use_ner:
                ner_entities = await self.ner_service.extract_entities(cleaned_text)
                logger.info(f"NER atrada {len(ner_entities)} entities ar mācīšanos")
            
            # 2. Pēc tam izmanto regex (stabilo baseline)
            regex_data = await self.regex_service.extract_invoice_data(cleaned_text)
            
            if not use_ner:
                # Ja NER ir izslēgts, atgriež tikai regex rezultātus
                return regex_data
            
            # 3. Kombinē abus rezultātus (NER prioritāte augstāka!)
            combined_data = await self._combine_results(regex_data, ner_entities, ocr_text)
            
            # 4. Aprēķina kombinēto confidence
            combined_data.confidence_scores = await self._calculate_hybrid_confidence(
                regex_data, ner_entities, combined_data
            )
            
            logger.info(f"Hibridā ekstraktēšana pabeigta: {len(combined_data.products)} produkti")
            return combined_data
            
        except Exception as e:
            logger.error(f"Hibridās ekstraktēšanas kļūda: {e}")
            # Fallback uz regex
            return await self.regex_service.extract_invoice_data(ocr_text)
    
    async def _combine_results(self, 
                             regex_data: ExtractedData, 
                             ner_entities: List[NEREntity],
                             original_text: str) -> ExtractedData:
        """Kombinē regex un NER rezultātus - NER ir prioritārāks!"""
        
        # Sākam ar regex datiem kā baseline
        combined = regex_data
        
        # NER rezultāti PĀRRAKSTA regex rezultātus, ja confidence ir pietiekams
        for entity in ner_entities:
            confidence_bonus = 0.2  # NER iegūst confidence bonus
            
            if entity.label == 'SUPPLIER_NAME' and entity.confidence > 0.6:
                # NER SUPPLIER vienmēr pārraksta regex, ja confidence > 0.6
                if entity.text and entity.text.lower() not in ["periods", "reģ", "adrese", ""]:
                    combined.supplier_name = entity.text
                    combined.supplier_confidence = min(entity.confidence + confidence_bonus, 1.0)
                    logger.info(f"NER pārrakstīja supplier: {entity.text} (conf: {entity.confidence:.2f})")
            
            elif entity.label == 'RECIPIENT' and entity.confidence > 0.5:
                # Pārbaudām vai tas nav adrese  
                if not any(word in entity.text.lower() for word in ['iela', 'street', 'lv-', 'rīga']):
                    combined.recipient_name = entity.text
                    combined.recipient_confidence = min(entity.confidence + confidence_bonus, 1.0)
                    logger.info(f"NER pārrakstīja recipient: {entity.text} (conf: {entity.confidence:.2f})")
            
            elif entity.label == 'SUPPLIER_REGISTRATION_NUMBER' and entity.confidence > 0.7:
                combined.supplier_reg_number = entity.text
                logger.info(f"NER pārrakstīja reg_number: {entity.text}")
            
            elif entity.label == 'RECIPIENT_REG_NUMBER' and entity.confidence > 0.7:
                combined.recipient_reg_number = entity.text
                logger.info(f"NER pārrakstīja recipient_reg_number: {entity.text}")
            
            elif entity.label == 'INVOICE_NUMBER' and entity.confidence > 0.7:
                combined.document_number = entity.text
                logger.info(f"NER pārrakstīja document_number: {entity.text}")
            
            elif entity.label == 'AMOUNT' and entity.confidence > 0.7:
                if not combined.total_amount:
                    try:
                        amount = float(entity.text.replace(',', '.').replace(' ', ''))
                        combined.total_amount = amount
                    except ValueError:
                        pass
            
            elif entity.label == 'DATE' and entity.confidence > 0.8:
                if not combined.invoice_date:
                    parsed_date = await self._parse_date_from_entity(entity.text)
                    if parsed_date:
                        combined.invoice_date = parsed_date
        
        return combined
    
    async def _parse_date_from_entity(self, date_str: str) -> Optional[date]:
        """Parsē datumu no NER entītijas"""
        try:
            # Vienkārša datuma parsēšana
            import re
            
            # DD.MM.YYYY vai DD/MM/YYYY
            match = re.search(r'(\d{1,2})[\./](\d{1,2})[\./](\d{2,4})', date_str)
            if match:
                day, month, year = match.groups()
                if len(year) == 2:
                    year = "20" + year
                return date(int(year), int(month), int(day))
        except Exception as e:
            logger.warning(f"Datuma parsēšanas kļūda: {e}")
        
        return None
    
    async def _calculate_hybrid_confidence(self, 
                                         regex_data: ExtractedData,
                                         ner_entities: List[NEREntity],
                                         combined_data: ExtractedData) -> Dict[str, float]:
        """Aprēķina kombinēto confidence score"""
        
        scores = regex_data.confidence_scores.copy() if regex_data.confidence_scores else {}
        
        # NER bonuss
        ner_confidence_bonus = 0.1
        entity_counts = {}
        
        for entity in ner_entities:
            if entity.confidence > 0.7:
                label_lower = entity.label.lower()
                entity_counts[label_lower] = entity_counts.get(label_lower, 0) + 1
        
        # Pievieno NER bonusu atbilstošajiem laukiem
        if 'supplier' in entity_counts and 'supplier' in scores:
            scores['supplier'] = min(scores['supplier'] + ner_confidence_bonus, 1.0)
        
        if 'recipient' in entity_counts:
            scores['recipient'] = min(scores.get('recipient', 0.5) + ner_confidence_bonus, 1.0)
        
        # Pārskaitām overall confidence
        valid_scores = [score for score in scores.values() if score > 0]
        scores['overall'] = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
        scores['hybrid_bonus'] = min(len(entity_counts) * 0.05, 0.2)  # Bonuss par NER daudzveidību
        
        return scores
    
    async def learn_from_corrections(self, 
                                   original_text: str,
                                   extracted_data: ExtractedData,
                                   corrected_data: Dict) -> Dict:
        """
        Mācās no lietotāja labojumiem abos servisos
        
        Args:
            original_text: Oriģinālais OCR teksts
            extracted_data: Mūsu prognozes
            corrected_data: Lietotāja labojumi
            
        Returns:
            Dict: Mācīšanās rezultāti
        """
        try:
            learning_results = {
                "regex_learning": {"learned": False},
                "ner_learning": {"learned": False},
                "combined_improvements": 0
            }
            
            # 1. NER mācīšanās (galvenais fokuss)
            ner_entities = await self.ner_service.extract_entities(original_text)
            ner_results = await self.ner_service.learn_from_corrections(
                original_text, ner_entities, corrected_data
            )
            learning_results["ner_learning"] = ner_results
            
            # 2. Regex uzlabojumi (TODO: būs jāatvienot)
            # Pagaidām saglabājam regex uzlabojumus atsevišķi
            regex_improvements = await self._analyze_regex_improvements(
                original_text, extracted_data, corrected_data
            )
            learning_results["regex_learning"] = regex_improvements
            
            learning_results["combined_improvements"] = (
                ner_results.get("patterns_updated", 0) + 
                regex_improvements.get("patterns_updated", 0)
            )
            
            logger.info(f"Hibridā mācīšanās: {learning_results['combined_improvements']} uzlabojumi")
            return learning_results
            
        except Exception as e:
            logger.error(f"Hibridās mācīšanās kļūda: {e}")
            return {"learned": False, "error": str(e)}
    
    async def _analyze_regex_improvements(self, 
                                        original_text: str,
                                        extracted_data: ExtractedData,
                                        corrected_data: Dict) -> Dict:
        """Analizē iespējamos regex uzlabojumus (pagaidu risinājums)"""
        
        improvements = []
        
        # Vienkārša analīze - salīdzina prognozēto ar laboto
        comparisons = [
            ('supplier_name', extracted_data.supplier_name, corrected_data.get('supplier_name')),
            ('recipient_name', extracted_data.recipient_name, corrected_data.get('recipient_name')),
            ('total_amount', extracted_data.total_amount, corrected_data.get('total_amount')),
            ('document_number', extracted_data.document_number, corrected_data.get('document_number'))
        ]
        
        for field, predicted, correct in comparisons:
            if predicted != correct and correct:
                # Reģistrē nepareizu prognozi
                improvements.append({
                    'field': field,
                    'predicted': predicted,
                    'correct': correct,
                    'needs_pattern_update': True
                })
        
        return {
            "learned": len(improvements) > 0,
            "patterns_updated": len(improvements),
            "improvements": improvements
        }
    
    async def get_extraction_statistics(self) -> Dict:
        """Atgriež ekstraktēšanas statistiku"""
        
        ner_stats = await self.ner_service.get_learning_statistics()
        
        return {
            "extraction_service": "hybrid",
            "regex_available": True,
            "ner_available": True,
            "ner_statistics": ner_stats,
            "total_learned_patterns": ner_stats.get("learned_patterns", 0),
            "supported_invoice_types": ner_stats.get("invoice_types", []),
            "learning_active": True
        }
    
    async def export_learning_data(self) -> Dict:
        """Eksportē visus mācīšanās datus"""
        
        ner_export = await self.ner_service.export_learned_patterns()
        
        return {
            "export_type": "hybrid_learning_data",
            "ner_data": ner_export,
            "statistics": await self.get_extraction_statistics()
        }

# Globālā hibridā servisa instance
hybrid_service = HybridExtractionService()
