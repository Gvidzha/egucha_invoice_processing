"""
Datu ekstraktēšanas serviss
Ekstraktē strukturētus datus no OCR teksta izmantojot regex patterns un ML
"""

import re
import asyncio
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import json
import logging
from dataclasses import dataclass

from app.config import REGEX_PATTERNS, CONFIDENCE_THRESHOLD

from app.extractions.extracted_data import ExtractedData
from app.extractions.supplier_extractor import extract_supplier_name
from app.utils.ocr_utils import load_ocr_corrections, correct_ocr_text


logger = logging.getLogger(__name__)


@dataclass
class ExtractionService:
    """Datu ekstraktēšanas serviss"""
    
    def __init__(self):
        """Inicializē ekstraktēšanas servisu"""
        self.patterns = REGEX_PATTERNS
        self.confidence_threshold = CONFIDENCE_THRESHOLD
        self.ocr_corrections = load_ocr_corrections("backend/app/resources/clean_ocr_vardnica.txt")
        
    async def extract_invoice_data(self, ocr_text: str) -> ExtractedData:
        """
        Ekstraktē pavadzīmes datus no OCR teksta
        
        Args:
            ocr_text: OCR rezultāta teksts
            
        Returns:
            ExtractedData: Ekstraktētie dati ar confidence scores
        """
        try:
            logger.info("Sākam datu ekstraktēšanu no OCR teksta")
            cleaned_text = correct_ocr_text(ocr_text, self.ocr_corrections)
            extracted = ExtractedData()
            
            # Ekstraktēt pavadzīmes numuru
            extracted.invoice_number = await self._extract_invoice_number(cleaned_text)

            # Ekstraktēt piegādātāju
            extracted.supplier_name, extracted.supplier_confidence = await self._extract_supplier(cleaned_text)
            extracted.supplier_reg_number = await self._extract_supplier_reg_number(cleaned_text)
            extracted.supplier_address = await self._extract_supplier_address(cleaned_text)
            extracted.supplier_bank_account = await self._extract_supplier_bank_account(cleaned_text)

            # Ekstraktēt saņēmēju
            extracted.recipient_name, extracted.recipient_confidence = await self._extract_recipient(cleaned_text)
            extracted.recipient_reg_number = await self._extract_recipient_reg_number(cleaned_text)
            extracted.recipient_address = await self._extract_recipient_address(cleaned_text)
            extracted.recipient_bank_account = await self._extract_recipient_bank_account(cleaned_text)
            
            # Ekstraktēt datumus
            extracted.invoice_date = await self._extract_invoice_date(cleaned_text)
            extracted.delivery_date = await self._extract_delivery_date(cleaned_text)

            # Ekstraktēt kopējo summu un PVN
            extracted.total_amount = await self._extract_total_amount(cleaned_text)
            extracted.subtotal_amount = await self._extract_subtotal_amount(cleaned_text)
            extracted.vat_amount = await self._extract_vat_amount(cleaned_text)
            extracted.currency = await self._extract_currency(cleaned_text)
            
            # Ekstraktēt produktu rindas
            extracted.products = await self._extract_product_lines(cleaned_text)

            # Aprēķināt confidence scores
            extracted.confidence_scores = await self._calculate_confidence_scores(extracted)

            logger.info(f"EXTRACTED DATA: {extracted.to_dict()}")
            logger.info(f"Ekstraktēšana pabeigta: {len(extracted.products)} produkti, kopā {extracted.total_amount} {extracted.currency}")
            return extracted
            
        except Exception as e:
            logger.error(f"Datu ekstraktēšanas kļūda: {e}")
            return ExtractedData()
            
    async def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Ekstraktē pavadzīmes numuru"""
        for pattern in self.patterns["invoice_number"]:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                number = match.group(1).strip()
                logger.debug(f"Atrasts pavadzīmes numurs: {number}")
                return number
        return None
    
    async def _extract_supplier(self, text: str) -> Tuple[Optional[str], float]:
        """Ekstraktē piegādātāja nosaukumu"""
        for pattern in self.patterns["supplier"]:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                supplier = match.group(1) if match.groups() else match.group(0)
                supplier = supplier.strip()
                
                # Tīrām nevajadzīgos simbolus
                supplier = re.sub(r'\s+', ' ', supplier)
                supplier = supplier.replace('\n', ' ').replace('\r', ' ')
                
                # Specifiskā logika uzņēmumu atpazīšanai
                supplier_clean = self._normalize_supplier_name(supplier, text)
                
                # Aprēķinām confidence
                confidence = 0.7
                if any(word in supplier_clean.upper() for word in ['SIA', 'AS', 'Z/S']):
                    confidence += 0.1
                if len(supplier_clean) > 3 and len(supplier_clean) < 50:
                    confidence += 0.1
                if 'peterstirgus' in text.lower() or 'petertirgus' in text.lower():
                    if 'peter' in supplier_clean.lower():
                        confidence += 0.1
                        
                logger.debug(f"Atrasts piegādātājs: {supplier_clean} (confidence: {confidence})")
                return supplier_clean, min(confidence, 1.0)
        return None, 0.0
        
    def _normalize_supplier_name(self, supplier: str, full_text: str) -> str:
        """Normalizē uzņēmuma nosaukumu"""
        # Lindström specific
        if 'lindstrom' in full_text.lower() or 'lindström' in full_text.lower():
            return "SIA Lindström"
            
        # Specifiskā loģika Liepājas Pētertirgus
        if 'peterstirgus.lv' in full_text.lower():
            return "Liepājas Pētertirgus"
        if any(word in full_text.lower() for word in ['petertirgus', 'peterstirgus', 'ertirg']):
            if any(word in full_text.lower() for word in ['liepaj', 'liepāj']):
                return "Liepājas Pētertirgus"
            return "Pētertirgus"
            
        # TIM-T specifisks
        if 'TIM-T' in supplier or 'tim-t' in supplier.lower():
            return "SIA TIM-T"
            
        # Vispārīga tīrīšana
        supplier = re.sub(r'^(SIA|AS|Z/S)\s*', '', supplier, flags=re.IGNORECASE)
        supplier = supplier.strip('"\'.,;')
        
        return supplier
        
    async def _extract_invoice_date(self, text: str) -> Optional[date]:
        """Ekstraktē pavadzīmes datumu"""
        latvian_months = {
            'janvāris': 1, 'februāris': 2, 'marts': 3, 'aprīlis': 4,
            'maijs': 5, 'jūnijs': 6, 'jūlijs': 7, 'augusts': 8,
            'septembris': 9, 'oktobris': 10, 'novembris': 11, 'decembris': 12
        }
        
        for pattern in self.patterns["date"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        if groups[2] in latvian_months:  # Latviešu mēnesis
                            year, day, month_name = groups
                            month = latvian_months[groups[2]]
                            parsed_date = date(int(year), month, int(day))
                        else:  # Ciparu formāts
                            if len(groups[0]) == 4:  # YYYY-MM-DD formāts
                                year, month, day = groups
                            else:  # DD-MM-YYYY formāts
                                day, month, year = groups
                            parsed_date = date(int(year), int(month), int(day))
                        
                        logger.debug(f"Atrasts datums: {parsed_date}")
                        return parsed_date
                except (ValueError, IndexError) as e:
                    logger.warning(f"Nevarēja parsēt datumu: {match.group(0)} - {e}")
                    continue
        return None
        
    async def _extract_delivery_date(self, text: str) -> Optional[date]:
        """Ekstraktē piegādes datumu (pagaidām tāds pats kā invoice datums)"""
        # TODO: Implementēt specifisko piegādes datuma meklēšanu
        return await self._extract_invoice_date(text)
        
    async def _extract_total_amount(self, text: str) -> Optional[float]:
        """Ekstraktē kopējo summu"""
        for pattern in self.patterns["total"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).strip()
                try:
                    # Tīrām un konvertējam
                    amount_str = amount_str.replace(' ', '').replace(',', '.')
                    amount = float(re.sub(r'[^\d.]', '', amount_str))
                    logger.debug(f"Atrasta kopējā summa: {amount}")
                    return amount
                except (ValueError, IndexError) as e:
                    logger.warning(f"Nevarēja parsēt summu: {amount_str} - {e}")
                    continue
        return None
        
    async def _extract_vat_amount(self, text: str) -> Optional[float]:
        """Ekstraktē PVN summu"""
        for pattern in self.patterns["vat"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).strip()
                try:
                    amount_str = amount_str.replace(' ', '').replace(',', '.')
                    amount = float(re.sub(r'[^\d.]', '', amount_str))
                    logger.debug(f"Atrasts PVN: {amount}")
                    return amount
                except (ValueError, IndexError) as e:
                    logger.warning(f"Nevarēja parsēt PVN: {amount_str} - {e}")
                    continue
        return None
        
    async def _extract_currency(self, text: str) -> str:
        """Ekstraktē valūtu (parasti EUR)"""
        if re.search(r'\bEUR\b', text, re.IGNORECASE):
            return "EUR"
        elif re.search(r'\bUSD\b', text, re.IGNORECASE):
            return "USD"
        return "EUR"  # Default
        
    async def _extract_reg_number(self, text: str) -> Optional[str]:
        """Ekstraktē reģistrācijas numuru"""
        for pattern in self.patterns["reg_number"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                reg_num = match.group(1).strip()
                logger.debug(f"Atrasts reģ. numurs: {reg_num}")
                return reg_num
        return None
        
    async def _extract_address(self, text: str) -> Optional[str]:
        """Ekstraktē juridisko adresi"""
        for pattern in self.patterns["address"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                address = match.group(1).strip()
                # Tīrām adresi
                address = re.sub(r'\s+', ' ', address)
                address = address.replace('\n', ' ').replace('\r', ' ')
                logger.debug(f"Atrasta adrese: {address}")
                return address
        return None
        return None
    
    async def _extract_delivery_date(self, text: str) -> Optional[date]:
        """Ekstraktē piegādes datumu"""
        # Meklē specifiskos piegādes datuma vārdus
        delivery_patterns = [
            r'piegādes?\s+datums?[:\s]*(\d{1,2}[\./\-]\d{1,2}[\./\-]\d{2,4})',
            r'delivery\s+date[:\s]*(\d{1,2}[\./\-]\d{1,2}[\./\-]\d{2,4})',
            r'delivered?[:\s]*(\d{1,2}[\./\-]\d{1,2}[\./\-]\d{2,4})'
        ]
        
        for pattern in delivery_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    # Vienkārša datuma parsēšana
                    parts = re.split(r'[\./\-]', date_str)
                    if len(parts) == 3:
                        day, month, year = parts
                        if len(year) == 2:
                            year = "20" + year
                        parsed_date = date(int(year), int(month), int(day))
                        return parsed_date
                except ValueError:
                    continue
        
        # Ja nav atrasts specifisks piegādes datums, atgriežam invoice datumu
        return await self._extract_invoice_date(text)
    
    async def _extract_total_amount(self, text: str) -> Optional[float]:
        """Ekstraktē kopējo summu"""
        for pattern in self.patterns["total"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).strip()
                try:
                    # Tīrām un konvertējam
                    amount_str = amount_str.replace(' ', '').replace(',', '.')
                    amount = float(re.sub(r'[^\d.]', '', amount_str))
                    logger.debug(f"Atrasta kopējā summa: {amount}")
                    return amount
                except (ValueError, IndexError) as e:
                    logger.warning(f"Nevarēja parsēt summu: {amount_str} - {e}")
                    continue
        return None
    
    async def _extract_currency(self, text: str) -> str:
        """Ekstraktē valūtu (default EUR)"""
        if re.search(r'\bEUR\b', text, re.IGNORECASE):
            return "EUR"
        elif re.search(r'\b€\b', text):
            return "EUR"
        elif re.search(r'\bUSD\b', text, re.IGNORECASE):
            return "USD"
        elif re.search(r'\b\$\b', text):
            return "USD"
        return "EUR"  # Default
    
    async def _extract_products(self, text: str) -> List[dict]:
        """Ekstraktē produktu sarakstu no pavadzīmes"""
        products = []
        
        # Meklējam tabulas struktūru
        for pattern in self.patterns["products"]:
            for match in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
                try:
                    # Sadalām atrastos datus
                    groups = match.groups()
                    if len(groups) >= 3:
                        name = groups[0].strip() if groups[0] else ""
                        quantity_str = groups[1].strip() if groups[1] else "1"
                        price_str = groups[2].strip() if groups[2] else "0"
                        
                        # Tīrām un konvertējam
                        quantity = float(re.sub(r'[^\d.,]', '', quantity_str).replace(',', '.') or '1')
                        price = float(re.sub(r'[^\d.,]', '', price_str).replace(',', '.') or '0')
                        
                        if name and price > 0:
                            product = {
                                "name": name,
                                "quantity": quantity,
                                "unit_price": price,
                                "total_price": quantity * price
                            }
                            products.append(product)
                            logger.debug(f"Atrasts produkts: {product}")
                            
                except (ValueError, IndexError) as e:
                    logger.warning(f"Nevarēja parsēt produktu: {match.group(0)} - {e}")
                    continue
        
        return products
        
    async def _extract_bank_account(self, text: str) -> Optional[str]:
        """Ekstraktē bankas kontu"""
        for pattern in self.patterns["bank_account"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                account = match.group(1).strip()
                # Noņemam atstarpes no IBAN
                account = re.sub(r'\s+', '', account)
                logger.debug(f"Atrasts bankas konts: {account}")
                return account
        return None
    
    async def _calculate_confidence_scores(self, extracted: ExtractedData) -> Dict[str, float]:
        """Aprēķina confidence scores visiem ekstraktētajiem datiem"""
        scores = {}
        
        # Supplier confidence
        scores["supplier"] = 0.8 if extracted.supplier_name else 0.0
        if extracted.supplier_name and 'SIA' in extracted.supplier_name:
            scores["supplier"] += 0.1
            
        # Date confidence
        scores["invoice_date"] = 0.8 if extracted.invoice_date else 0.0
        scores["delivery_date"] = 0.8 if extracted.delivery_date else 0.0
        
        # Amount confidence
        scores["total_amount"] = 0.8 if extracted.total_amount and extracted.total_amount > 0 else 0.0
        scores["vat_amount"] = 0.7 if extracted.vat_amount and extracted.vat_amount >= 0 else 0.0
        
        # Products confidence
        scores["products"] = 0.8 if extracted.products and len(extracted.products) > 0 else 0.0
        
        # Overall confidence (vidējais)
        valid_scores = [score for score in scores.values() if score > 0]
        scores["overall"] = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
        
        return scores
    
    # =================== SAŅĒMĒJA EKSTRAKTĒŠANA ===================
    
    async def _extract_recipient(self, text: str) -> Tuple[Optional[str], float]:
        """Ekstraktē saņēmēja uzņēmuma nosaukumu"""
        recipient_patterns = [
            # Meklē pēc "Piegāde uz:" sekojošo uzņēmuma nosaukumu
            r"(?:piegāde uz|delivery to)[:\s]*\n?\s*([^\n\r]+(?:SIA|AS|IK|UAB)[^\n\r]*)",
            r"(?:piegāde uz|delivery to)[:\s]*\n?\s*([A-ZĀČĒĢĪĶĻŅŠŪŽ][^\n\r]+)",
            # Tradicionālie patterns
            r"(?:saņēmējs|pircējs|klients|buyer|recipient)[:\s]*([^\n\r]+)",
            r"(?:billed to|invoice to|bill to)[:\s]*([^\n\r]+)",
            # Meklē SIA nosaukumus pēc piegādes sadaļas
            r"(?:^|\n)([A-ZĀČĒĢĪĶĻŅŠŪŽ][^\n\r]*(?:SIA|AS|IK|UAB)[^\n\r]*)",
        ]
        
        for pattern in recipient_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                recipient = match.group(1).strip()
                
                # Tīrām un normalizējam
                recipient = re.sub(r'\s+', ' ', recipient)
                recipient = recipient.replace('\n', ' ').replace('\r', ' ')
                recipient = recipient.strip('"\'')
                
                # Pārbaudām vai tas nav adrese
                if any(word in recipient.lower() for word in ['iela', 'street', 'lv-', 'rīga', 'liepāja']):
                    continue  # Izlaižam adreses
                
                if len(recipient) > 3 and len(recipient) < 100:
                    logger.debug(f"Atrasts saņēmējs: {recipient}")
                    confidence = 0.8
                    if any(word in recipient.upper() for word in ['SIA', 'AS', 'IK']):
                        confidence = 0.9
                    return recipient, confidence
        return None, 0.0
    
    async def _extract_recipient_reg_number(self, text: str) -> Optional[str]:
        """Ekstraktē saņēmēja reģistrācijas numuru"""
        # Meklē reg.nr. kontekstā ar saņēmēju
        patterns = [
            r"(?:pircēja|klients|saņēmējs).*?(?:reg|reģ).*?nr[.\s]*[:\-]?\s*([A-Z]{0,2}\d{8,11})",
            r"(?:bill to|billed to).*?(?:reg|vat).*?no[.\s]*[:\-]?\s*([A-Z]{0,2}\d{8,11})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                reg_num = match.group(1).strip()
                logger.debug(f"Atrasts saņēmēja reģ.nr: {reg_num}")
                return reg_num
        return None
    
    async def _extract_recipient_address(self, text: str) -> Optional[str]:
        """Ekstraktē saņēmēja adresi"""
        # Meklē adresi kontekstā ar saņēmēju
        patterns = [
            r"(?:pircēja|klients|saņēmējs).*?(?:adrese|address)[:\s]*([^\n\r]+)",
            r"(?:bill to|billed to).*?address[:\s]*([^\n\r]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                address = match.group(1).strip()
                if len(address) > 5:
                    return address
        return None
    
    async def _extract_recipient_bank_account(self, text: str) -> Optional[str]:
        """Ekstraktē saņēmēja bankas kontu"""
        # Parasti nav pavadzīmēs, bet var būt specifiski gadījumi
        patterns = [
            r"(?:pircēja|klients).*?(?:konts|account)[:\s]*([A-Z]{2}\d{2}[A-Z0-9]{4,24})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                account = match.group(1).strip()
                return account
        return None
    
    # ================= PIEGĀDĀTĀJA DETALIZĒTA EKSTRAKTĒŠANA =================
    
    async def _extract_supplier_reg_number(self, text: str) -> Optional[str]:
        """Ekstraktē piegādātāja reģistrācijas numuru"""
        patterns = [
            r"(?:reg|reģ).*?nr[.\s]*[:\-]?\s*([A-Z]{0,2}\d{8,11})",
            r"(?:registration|VAT).*?no[.\s]*[:\-]?\s*([A-Z]{0,2}\d{8,11})",
            r"PVNnr[.\s]*([A-Z]{2}\d{8,11})",
            r"([A-Z]{2}\d{11})",  # LV format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                reg_num = match.group(1).strip()
                logger.debug(f"Atrasts piegādātāja reģ.nr: {reg_num}")
                return reg_num
        return None
        
    async def _extract_supplier_address(self, text: str) -> Optional[str]:
        """Ekstraktē piegādātāja adresi"""
        patterns = [
            r"(?:adrese|address)[:\s]*([^\n\r]+(?:LV-\d{4})[^\n\r]*)",
            r"([A-ZĀČĒĢĪĶĻŅŠŪŽa-zāčēģīķļņšūž\s\d,.-]+,\s*[A-ZĀČĒĢĪĶĻŅŠŪŽa-zāčēģīķļņšūž\s]+,\s*LV-\d{4})",
            r"([^\n\r]*iela\s*\d+[^\n\r]*(?:LV-\d{4})?)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                address = match.group(1).strip()
                if len(address) > 10:
                    return address
        return None
    
    async def _extract_supplier_bank_account(self, text: str) -> Optional[str]:
        """Ekstraktē piegādātāja bankas kontu"""
        patterns = [
            r"(?:konts|account|IBAN)[:\s]*([A-Z]{2}\d{2}[A-Z0-9]{4,24})",
            r"([A-Z]{2}\d{2}[A-Z]{4}\d{4}[\d]{7,16})",  # IBAN format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                account = match.group(1).strip()
                if len(account) >= 15:  # IBAN minimālais garums
                    return account
        return None
    
    async def _extract_subtotal_amount(self, text: str) -> Optional[float]:
        """Ekstraktē summu bez PVN"""
        patterns = [
            r"(?:summa bez PVN|subtotal|net amount)[:\s]*([0-9,. ]+)",
            r"bez PVN[:\s]*([0-9,. ]+)",
            r"(?:^|\n)[^\n]*bez\s*PVN[^\n]*?([0-9,. ]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                amount_str = match.group(1).strip()
                try:
                    amount = float(re.sub(r'[,\s]', '.', amount_str.replace(' ', '')))
                    if amount > 0:
                        return amount
                except ValueError:
                    continue
        return None
    
    # =================== PRODUKTU RINDU EKSTRAKTĒŠANA ===================
    
    async def _extract_product_lines(self, text: str) -> List[Dict]:
        """Ekstraktē produktu rindas no pavadzīmes"""
        try:
            products = []
            
            # Meklē produktu tabulas daļu
            table_patterns = [
                r"(?:nosaukums|apraksts|description|item).*?\n(.*?)(?:\n.*?(?:kopā|total|summa))",
                r"(?:^|\n)((?:.*?\d+[.,]\d{2}.*?\n)+)",  # Rindas ar cenām
            ]
            
            for pattern in table_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
                if match:
                    table_text = match.group(1)
                    products.extend(await self._parse_product_lines(table_text))
                    break
            
            logger.info(f"Ekstraktēti {len(products)} produkti")
            return products
            
        except Exception as e:
            logger.error(f"Produktu ekstraktēšanas kļūda: {e}")
            return []
    
    async def _parse_product_lines(self, table_text: str) -> List[Dict]:
        """Parsē produktu rindas no tabulas teksta"""
        products = []
        lines = table_text.strip().split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 10:
                continue
                
            # Produktu rindas pattern (pielāgots Latvijas pavadzīmēm)
            product_patterns = [
                # Pattern 1: Nosaukums Daudzums Cena Summa
                r"^(.+?)\s+(\d+(?:[.,]\d+)?)\s+([^\s]+)\s+(\d+[.,]\d{2})\s+(\d+[.,]\d{2})$",
                # Pattern 2: Kods Nosaukums Daudzums Mērvienība Cena Summa  
                r"^(\w+)\s+(.+?)\s+(\d+(?:[.,]\d+)?)\s+([^\s]+)\s+(\d+[.,]\d{2})\s+(\d+[.,]\d{2})$",
                # Pattern 3: Vienkāršs - tikai nosaukums un summa
                r"^(.+?)\s+(\d+[.,]\d{2})$",
            ]
            
            for pattern in product_patterns:
                match = re.match(pattern, line)
                if match:
                    try:
                        product = await self._create_product_dict(match, pattern)
                        if product:
                            product['line_number'] = i + 1
                            product['raw_text'] = line
                            products.append(product)
                        break
                    except Exception as e:
                        logger.warning(f"Produktu parsēšanas kļūda rindā '{line}': {e}")
                        continue
        
        return products
    
    async def _create_product_dict(self, match, pattern: str) -> Optional[Dict]:
        """Izveido produkta dictionary no regex match"""
        try:
            groups = match.groups()
            
            if len(groups) == 6:  # Pilns pattern ar kodu
                return {
                    'product_code': groups[0],
                    'name': groups[1].strip(),
                    'quantity': float(groups[2].replace(',', '.')),
                    'unit': groups[3],
                    'unit_price': float(groups[4].replace(',', '.')),
                    'total_price': float(groups[5].replace(',', '.')),
                    'extraction_confidence': 0.9
                }
            elif len(groups) == 5:  # Pattern bez koda
                return {
                    'name': groups[0].strip(),
                    'quantity': float(groups[1].replace(',', '.')),
                    'unit': groups[2],
                    'unit_price': float(groups[3].replace(',', '.')),
                    'total_price': float(groups[4].replace(',', '.')),
                    'extraction_confidence': 0.8
                }
            elif len(groups) == 2:  # Vienkāršs pattern
                return {
                    'name': groups[0].strip(),
                    'total_price': float(groups[1].replace(',', '.')),
                    'extraction_confidence': 0.6
                }
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Produkta izveidošanas kļūda: {e}")
            return None
    
    async def improve_extraction_with_corrections(self, 
                                                original_text: str, 
                                                corrections: Dict) -> Dict:
        """
        Uzlabo ekstraktēšanas kvalitāti izmantojot lietotāja labojumus
        
        Args:
            original_text: Oriģinālais OCR teksts
            corrections: Lietotāja labojumi
            
        Returns:
            dict: Uzlabotie regex patterns
        """
        # TODO: Implementēt mašīnmācīšanos:
        # - Analizēt labojumu patterns
        # - Ģenerēt jaunus regex patterns
        # - Atjaunināt pattern datubāzi
        # - Testēt jauno pattern efektivitāti
        
        return {"message": "TODO: implement learning from corrections"}
