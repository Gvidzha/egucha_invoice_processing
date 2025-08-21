"""
NER (Named Entity Recognition) serviss
Mašīnmācīšanās bāzēta ekstraktēšana ar adaptīvu mācīšanos darba vidē
"""

import asyncio
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import re
import pickle
import os
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class NEREntity:
    """NER atklātā entītija"""
    text: str
    label: str
    start: int
    end: int
    confidence: float
    context: str = ""

@dataclass
class LearningExample:
    """Mācīšanās piemērs no lietotāja labojumiem"""
    original_text: str
    predicted_entities: List[NEREntity]
    corrected_entities: List[Dict]
    timestamp: datetime
    invoice_type: Optional[str] = None
    supplier_name: Optional[str] = None

class NERService:
    """NER serviss ar adaptīvu mācīšanos"""
    
    def __init__(self):
        self.model_path = Path("./models/ner")
        self.learning_data_path = Path("./data/learning")
        self.patterns_cache = {}
        self.learning_examples = []
        
        # Inicializē direktorijas
        self.model_path.mkdir(parents=True, exist_ok=True)
        self.learning_data_path.mkdir(parents=True, exist_ok=True)
        
        # Ielādē esošos mācīšanās datus
        self._load_learning_history()
        
        # SVARĪGI: Ielādē saglabātos patterns inicializācijas laikā!
        self._load_patterns_from_disk_sync()
        
    async def extract_entities(self, text: str) -> List[NEREntity]:
        """
        Ekstraktē entītijas no teksta izmantojot NER
        
        Args:
            text: OCR teksts
            
        Returns:
            List[NEREntity]: Atklātās entītijas
        """
        try:
            entities = []
            
            # Sākumā izmanto rule-based patterns (uzlabotus ar mācīšanos)
            entities.extend(await self._extract_with_learned_patterns(text))
            
            # TODO: Pievienot spaCy/transformers NER kad būs gatavs
            # entities.extend(await self._extract_with_ml_model(text))
            
            logger.info(f"NER ekstraktētas {len(entities)} entītijas")
            return entities
            
        except Exception as e:
            logger.error(f"NER ekstraktēšanas kļūda: {e}")
            return []
    
    async def _extract_with_learned_patterns(self, text: str) -> List[NEREntity]:
        """Ekstraktē izmantojot no labojumiem mācītus patterns"""
        entities = []
        
        # Izmanto uzlabotus patterns no mācīšanās
        learned_patterns = await self._get_learned_patterns()
        
        # DEBUG: Pārbaudi vai ir mācību patterns
        if learned_patterns:
            logger.info(f"IZMANTO MĀCĪTUS PATTERNS: {len(learned_patterns)} tipi")
            for label, patterns in learned_patterns.items():
                logger.info(f"  {label}: {len(patterns)} patterns")
        else:
            logger.info("NAV MĀCĪTU PATTERNS - izmanto bāzes")
        
        # Ja nav vēl mācību patterns, izmanto bāzes patterns
        if not learned_patterns:
            learned_patterns = await self._get_base_patterns()
            logger.info(f"Izmanto bāzes patterns: {len(learned_patterns)} tipi")
        
        for label, patterns in learned_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                confidence = pattern_info['confidence']
                
                for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                    entity_text = match.group(1) if match.groups() else match.group(0)
                    entity_text = entity_text.strip()
                    
                    # Filtrējam par īsiem/gariem tekstiem
                    if len(entity_text) < 2 or len(entity_text) > 200:
                        continue
                    
                    entity = NEREntity(
                        text=entity_text,
                        label=label,
                        start=match.start(),
                        end=match.end(),
                        confidence=confidence,
                        context=self._get_context(text, match.start(), match.end())
                    )
                    entities.append(entity)
                    logger.info(f"NER atrada {label}: '{entity_text}' (conf: {confidence:.2f})")
        
        return entities
    
    async def _get_base_patterns(self) -> Dict:
        """Atgriež bāzes NER patterns pirms mācīšanās"""
        return {
            "SUPPLIER": [
                {
                    "pattern": r"(?:^|\n)\s*([A-ZĀČĒĢĪĶĻŅŠŪŽ][^\n\r]*(?:SIA|AS|Z/S)[^\n\r]*)",
                    "confidence": 0.8
                },
                {
                    "pattern": r"(?:SIA|AS)\s+([A-ZĀČĒĢĪĶĻŅŠŪŽ][A-Za-zāčēģīķļņšūž\s]+)",
                    "confidence": 0.9
                }
            ],
            "RECIPIENT": [
                {
                    "pattern": r"(?:piegāde uz|delivery to)[:\s]*\n?\s*([^\n\r]+(?:SIA|AS|IK)[^\n\r]*)",
                    "confidence": 0.8
                },
                {
                    "pattern": r"(?:piegāde uz)[:\s]*\n?\s*([A-ZĀČĒĢĪĶĻŅŠŪŽ][^\n\r]+)",
                    "confidence": 0.7
                }
            ],
            "AMOUNT": [
                {
                    "pattern": r"(?:kopā|total|summa)[:\s]*([0-9,. ]+)\s*EUR",
                    "confidence": 0.9
                },
                {
                    "pattern": r"([0-9]+[.,]\d{2})\s*EUR",
                    "confidence": 0.7
                }
            ],
            "REG_NUMBER": [
                {
                    "pattern": r"(?:reg|reģ)\.?\s*nr\.?[:\s]*([A-Z]{2}\d{8,11})",
                    "confidence": 0.9
                }
            ],
            "DATE": [
                {
                    "pattern": r"(?:datums|date)[:\s]*(\d{1,2}[\./\-]\d{1,2}[\./\-]\d{2,4})",
                    "confidence": 0.8
                }
            ],
            "DOCUMENT_NUMBER": [
                {
                    "pattern": r"(?:pavadzīme|invoice|nr)\.?\s*([A-Z0-9]+)",
                    "confidence": 0.8
                }
            ]
        }
    
    def _get_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Iegūst kontekstu ap atrasto entītiju"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].replace('\n', ' ').strip()
    
    async def learn_from_corrections(self, 
                                   original_text: str,
                                   predicted_entities: List[NEREntity],
                                   corrected_data: Dict) -> Dict:
        """
        Mācās no lietotāja labojumiem
        
        Args:
            original_text: Oriģinālais OCR teksts
            predicted_entities: NER prognozes
            corrected_data: Lietotāja labojumi
            
        Returns:
            Dict: Mācīšanās rezultāti
        """
        try:
            # Izveidoa mācīšanās piemēru
            learning_example = LearningExample(
                original_text=original_text,
                predicted_entities=predicted_entities,
                corrected_entities=self._convert_corrections_to_entities(corrected_data),
                timestamp=datetime.now(),
                supplier_name=corrected_data.get('supplier_name'),
                invoice_type=self._detect_invoice_type(original_text)
            )
            
            # Pievieno mācīšanās piemēru
            self.learning_examples.append(learning_example)
            
            # Analizē un uzlabo patterns
            improvements = await self._analyze_and_improve_patterns(learning_example)
            
            # Saglabā mācīšanās datus
            await self._save_learning_example(learning_example)
            
            logger.info(f"NER iemācījās no labojuma: {len(improvements)} uzlabojumi")
            return {
                "learned": True,
                "improvements": improvements,
                "patterns_updated": len(improvements)
            }
            
        except Exception as e:
            logger.error(f"NER mācīšanās kļūda: {e}")
            return {"learned": False, "error": str(e)}
    
    def _convert_corrections_to_entities(self, corrected_data: Dict) -> List[Dict]:
        """Konvertē lietotāja labojumus uz entītiju formātu"""
        entities = []
        
        # Kartēšana starp datiem un entītiju tipiem
        field_mapping = {
            'supplier_name': 'SUPPLIER',
            'recipient_name': 'RECIPIENT', 
            'supplier_reg_number': 'REG_NUMBER',
            'recipient_reg_number': 'RECIPIENT_REG_NUMBER',
            'document_number': 'DOCUMENT_NUMBER',
            'total_amount': 'AMOUNT',
            'vat_amount': 'VAT_AMOUNT',
            'invoice_date': 'DATE',
            'supplier_address': 'ADDRESS',
            'recipient_address': 'RECIPIENT_ADDRESS'
        }
        
        for field, label in field_mapping.items():
            if field in corrected_data and corrected_data[field]:
                entities.append({
                    'text': str(corrected_data[field]),
                    'label': label,
                    'field': field
                })
        
        return entities
    
    def _detect_invoice_type(self, text: str) -> str:
        """Nosaka pavadzīmes tipu pēc satura"""
        text_lower = text.lower()
        
        if 'lindström' in text_lower or 'lindstrom' in text_lower:
            return 'LINDSTROM'
        elif 'peterstirgus' in text_lower or 'petertirgus' in text_lower:
            return 'PETERSTIRGUS'
        elif 'tim-t' in text_lower:
            return 'TIM_T'
        else:
            return 'GENERIC'
    
    async def _analyze_and_improve_patterns(self, example: LearningExample) -> List[Dict]:
        """Analizē mācīšanās piemēru un uzlabo patterns"""
        improvements = []
        
        for corrected_entity in example.corrected_entities:
            text = corrected_entity['text']
            label = corrected_entity['label']
            
            # Meklē šo tekstu oriģinālajā tekstā
            matches = list(re.finditer(re.escape(text), example.original_text, re.IGNORECASE))
            
            for match in matches:
                # Iegūst kontekstu
                context = self._get_context(example.original_text, match.start(), match.end(), 100)
                
                # Ģenerē jaunu pattern
                new_pattern = await self._generate_pattern_from_context(text, context, label)
                
                if new_pattern:
                    # Pārbauda pattern kvalitāti
                    pattern_quality = await self._evaluate_pattern_quality(
                        new_pattern, example.original_text, text
                    )
                    
                    if pattern_quality > 0.7:  # Tikai kvalitatīvi patterns
                        improvements.append({
                            'label': label,
                            'pattern': new_pattern,
                            'confidence': pattern_quality,
                            'example_text': text,
                            'context': context[:100],
                            'invoice_type': example.invoice_type
                        })
        
        # Atjaunina pattern cache
        await self._update_pattern_cache(improvements)
        
        return improvements
    
    async def _generate_pattern_from_context(self, text: str, context: str, label: str) -> Optional[str]:
        """Ģenerē regex pattern no konteksta"""
        try:
            # Vienkārša pattern ģenerēšana (TODO: uzlabot ar ML)
            escaped_text = re.escape(text)
            
            # Meklē specifiskus konteksta atslēgvārdus
            if label == 'SUPPLIER':
                if 'sia' in context.lower():
                    return rf"(?:SIA\s+)?({escaped_text})"
                else:
                    return rf"({escaped_text})"
            
            elif label == 'REG_NUMBER':
                # Pattern reģistrācijas numuriem
                if re.search(r'LV\d{11}', text):
                    return r"(LV\d{11})"
                else:
                    return rf"({escaped_text})"
            
            elif label == 'AMOUNT':
                # Pattern summām
                amount_pattern = re.sub(r'\d+', r'\\d+', escaped_text)
                return rf"(?:kopā|total|summa)[:\s]*({amount_pattern})"
            
            elif label == 'DATE':
                # Pattern datumiem
                date_pattern = re.sub(r'\d+', r'\\d+', escaped_text)
                return rf"(?:datums|date)[:\s]*({date_pattern})"
            
            else:
                return rf"({escaped_text})"
                
        except Exception as e:
            logger.warning(f"Pattern ģenerēšanas kļūda: {e}")
            return None
    
    async def _evaluate_pattern_quality(self, pattern: str, text: str, expected_match: str) -> float:
        """Novērtē pattern kvalitāti"""
        try:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            
            if not matches:
                return 0.0
            
            # Pārbauda vai pattern atrod pareizo tekstu
            for match in matches:
                found_text = match.group(1) if match.groups() else match.group(0)
                if found_text.strip().lower() == expected_match.strip().lower():
                    return 0.9  # Augsta kvalitāte
            
            # Pārbauda false positives
            if len(matches) > 3:  # Pārāk daudz atbilstību
                return 0.4
            
            return 0.6  # Vidēja kvalitāte
            
        except Exception as e:
            logger.warning(f"Pattern novērtēšanas kļūda: {e}")
            return 0.0
    
    async def _get_learned_patterns(self) -> Dict:
        """Iegūst no mācīšanās iegūtos patterns"""
        if not self.patterns_cache:
            await self._load_patterns_from_disk()
        
        return self.patterns_cache
    
    async def _update_pattern_cache(self, improvements: List[Dict]):
        """Atjaunina pattern cache ar jauniem uzlabojumiem"""
        for improvement in improvements:
            label = improvement['label']
            
            if label not in self.patterns_cache:
                self.patterns_cache[label] = []
            
            # Pievieno jauno pattern
            self.patterns_cache[label].append({
                'pattern': improvement['pattern'],
                'confidence': improvement['confidence'],
                'example': improvement['example_text'],
                'invoice_type': improvement['invoice_type']
            })
        
        # Saglabā uz diska
        await self._save_patterns_to_disk()
    
    def _load_patterns_from_disk_sync(self):
        """Ielādē saglabātos patterns no diska (sync versija)"""
        patterns_file = self.model_path / "learned_patterns.json"
        
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self.patterns_cache = json.load(f)
                logger.info(f"Ielādēti {len(self.patterns_cache)} pattern tipi")
            except Exception as e:
                logger.warning(f"Pattern ielādes kļūda: {e}")
                self.patterns_cache = {}
        else:
            self.patterns_cache = {}
    
    async def _load_patterns_from_disk(self):
        """Ielādē saglabātos patterns no diska"""
        patterns_file = self.model_path / "learned_patterns.json"
        
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self.patterns_cache = json.load(f)
                logger.info(f"Ielādēti {len(self.patterns_cache)} pattern tipi")
            except Exception as e:
                logger.warning(f"Pattern ielādes kļūda: {e}")
                self.patterns_cache = {}
        else:
            self.patterns_cache = {}
    
    async def _save_patterns_to_disk(self):
        """Saglabā patterns uz diska"""
        patterns_file = self.model_path / "learned_patterns.json"
        
        try:
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns_cache, f, ensure_ascii=False, indent=2)
            logger.info("Patterns saglabāti uz diska")
        except Exception as e:
            logger.error(f"Pattern saglabāšanas kļūda: {e}")
    
    def _load_learning_history(self):
        """Ielādē mācīšanās vēsturi"""
        history_file = self.learning_data_path / "learning_history.json"
        
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                # Konvertē atpakaļ uz LearningExample objektiem
                for item in history_data:
                    example = LearningExample(
                        original_text=item['original_text'],
                        predicted_entities=[],  # Nevajag ielādēt
                        corrected_entities=item['corrected_entities'],
                        timestamp=datetime.fromisoformat(item['timestamp']),
                        supplier_name=item.get('supplier_name'),
                        invoice_type=item.get('invoice_type')
                    )
                    self.learning_examples.append(example)
                
                logger.info(f"Ielādēti {len(self.learning_examples)} mācīšanās piemēri")
            except Exception as e:
                logger.warning(f"Mācīšanās vēstures ielādes kļūda: {e}")
    
    async def _save_learning_example(self, example: LearningExample):
        """Saglabā mācīšanās piemēru"""
        history_file = self.learning_data_path / "learning_history.json"
        
        try:
            # Ielādē esošo vēsturi
            history_data = []
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
            
            # Pievieno jauno piemēru
            history_data.append({
                'original_text': example.original_text,
                'corrected_entities': example.corrected_entities,
                'timestamp': example.timestamp.isoformat(),
                'supplier_name': example.supplier_name,
                'invoice_type': example.invoice_type
            })
            
            # Saglabā atjaunināto vēsturi
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Mācīšanās piemēra saglabāšanas kļūda: {e}")
    
    async def get_learning_statistics(self) -> Dict:
        """Atgriež mācīšanās statistiku"""
        return {
            "total_examples": len(self.learning_examples),
            "learned_patterns": sum(len(patterns) for patterns in self.patterns_cache.values()),
            "invoice_types": list(set(ex.invoice_type for ex in self.learning_examples if ex.invoice_type)),
            "last_learning": self.learning_examples[-1].timestamp.isoformat() if self.learning_examples else None
        }
    
    
    async def export_learned_patterns(self) -> Dict:
        """Eksportē iemācītos patterns diagnostikai"""
        return {
            "patterns": self.patterns_cache,
            "statistics": await self.get_learning_statistics(),
            "export_time": datetime.now().isoformat()
        }
    
    async def get_field_suggestions(self, field_name: str, limit: int = 10) -> List[str]:
        """
        Iegūst ieteikumus konkrētam laukam no mācīšanās vēstures
        
        Args:
            field_name: Lauka nosaukums (piem., 'supplier_name', 'total_amount')
            limit: Maksimālais ieteikumu skaits
            
        Returns:
            List[str]: Ieteikumu saraksts
        """
        try:
            suggestions = []
            
            # Iegūst vērtības no mācīšanās piemēriem
            for example in self.learning_examples:
                for entity_data in example.corrected_entities:
                    if entity_data.get('field') == field_name:
                        value = entity_data.get('value', '').strip()
                        if value and value not in suggestions:
                            suggestions.append(value)
            
            # Kārtot pēc popularitātes (vienkāršojums - alfabētiski)
            suggestions.sort()
            
            # Ierobežot skaitu
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Kļūda iegūstot ieteikumus laukam {field_name}: {e}")
            return []

# Globālā NER servisa instance
ner_service = NERService()
