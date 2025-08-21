"""
OCR teksta tīrīšanas un uzlabošanas modulis
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
import unicodedata

logger = logging.getLogger(__name__)

class TextCleaner:
    """OCR teksta tīrīšanas un kļūdu labošanas klase"""
    
    def __init__(self):
        # Tipiskās OCR kļūdas un to labojumi
        self.common_ocr_errors = {
            # Cipari vs burti
            '0': ['O', 'o', 'Q'],
            '1': ['I', 'l', '|', ']'],
            '2': ['Z', 'z'],
            '5': ['S', 's'],
            '6': ['G', 'b'],
            '8': ['B'],
            # Burti vs cipari
            'O': ['0'],
            'I': ['1', '|'],
            'l': ['1', '|'],
            'S': ['5'],
            'G': ['6'],
            'B': ['8'],
            # Latviešu valodas specifiskās kļūdas
            'ā': ['a', 'ã', 'à', 'á'],
            'ē': ['e', 'è', 'é', 'ê'],
            'ī': ['i', 'ì', 'í', 'î'],
            'ō': ['o', 'ò', 'ó', 'ô'],
            'ū': ['u', 'ù', 'ú', 'û'],
            'č': ['c', 'ç'],
            'ģ': ['g'],
            'ķ': ['k'],
            'ļ': ['l'],
            'ņ': ['n', 'ñ'],
            'š': ['s'],
            'ž': ['z'],
        }
        
        # Tipiska pavadzīmju terminoloģija latviešu valodā
        self.invoice_terms = {
            'pavadzīme': ['pavadzime', 'pavadz īme', 'pavad zīme'],
            'piegādātājs': ['piegadatajs', 'piegādatajs', 'piegadat ājs'],
            'saņēmējs': ['saņemejs', 'sanemejs', 'saņēm ējs'],
            'datums': ['dat ums', 'da tums'],
            'summa': ['sum ma', 'su mma'],
            'cena': ['ce na'],
            'daudzums': ['daudz ums', 'daudzams'],
            'pvn': ['p vn', 'p.v.n.'],
            'kopā': ['kop ā', 'ko pā'],
            'bez pvn': ['bez p vn', 'bez p.v.n.'],
            'ar pvn': ['ar p vn', 'ar p.v.n.'],
        }
        
        # Datumu formātu regex patterini
        self.date_patterns = [
            r'\d{1,2}\.\d{1,2}\.\d{4}',  # dd.mm.yyyy
            r'\d{1,2}/\d{1,2}/\d{4}',   # dd/mm/yyyy
            r'\d{4}-\d{1,2}-\d{1,2}',   # yyyy-mm-dd
            r'\d{1,2}-\d{1,2}-\d{4}',   # dd-mm-yyyy
        ]
        
        # Naudas summu formāti
        self.money_patterns = [
            r'\d+[,\.]\d{2}\s*€',        # 123.45 €
            r'€\s*\d+[,\.]\d{2}',        # € 123.45
            r'\d+[,\.]\d{2}\s*EUR',      # 123.45 EUR
            r'EUR\s*\d+[,\.]\d{2}',      # EUR 123.45
        ]
    
    def clean_text(self, raw_text: str) -> str:
        """
        Galvenā teksta tīrīšanas funkcija
        
        Args:
            raw_text: Neapstrādātais OCR teksts
            
        Returns:
            str: Iztīrītais teksts
        """
        if not raw_text:
            return ""
        
        text = raw_text
        
        # 1. Pamata tīrīšana
        text = self._basic_cleanup(text)
        
        # 2. OCR kļūdu labošana
        text = self._fix_ocr_errors(text)
        
        # 3. Latviešu valodas speciālā apstrāde
        text = self._fix_latvian_text(text)
        
        # 4. Pavadzīmju terminoloģijas labošana
        text = self._fix_invoice_terms(text)
        
        # 5. Strukturāla tīrīšana
        text = self._structural_cleanup(text)
        
        return text.strip()
    
    def _basic_cleanup(self, text: str) -> str:
        """Pamata teksta tīrīšana"""
        # Noņem nederīgās kontroles rakstzīmes
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\n\t')
        
        # Aizstāj vairākas atstarpes ar vienu
        text = re.sub(r'\s+', ' ', text)
        
        # Noņem atstarpes pirms un pēc interpunkcijas
        text = re.sub(r'\s*([,.;:!?])\s*', r'\1 ', text)
        
        # Noņem dubultās interpunkcijas
        text = re.sub(r'([,.;:!?]){2,}', r'\1', text)
        
        return text
    
    def _fix_ocr_errors(self, text: str) -> str:
        """Labo tipiskās OCR kļūdas"""
        # Kontekstbāzēta kļūdu labošana
        
        # Ciparu kontekstā labo burtus
        text = re.sub(r'(\d+)O(\d+)', r'\g<1>0\g<2>', text)  # Cipari-O-cipari -> 0
        text = re.sub(r'(\d+)I(\d+)', r'\g<1>1\g<2>', text)  # Cipari-I-cipari -> 1
        text = re.sub(r'(\d+)S(\d+)', r'\g<1>5\g<2>', text)  # Cipari-S-cipari -> 5
        
        # Burtu kontekstā labo ciparus
        text = re.sub(r'([a-zA-ZāēīōūčģķļņšžĀĒĪŌŪČĢĶĻŅŠŽ]+)0([a-zA-ZāēīōūčģķļņšžĀĒĪŌŪČĢĶĻŅŠŽ]+)', r'\g<1>o\g<2>', text)
        text = re.sub(r'([a-zA-ZāēīōūčģķļņšžĀĒĪŌŪČĢĶĻŅŠŽ]+)1([a-zA-ZāēīōūčģķļņšžĀĒĪŌŪČĢĶĻŅŠŽ]+)', r'\g<1>l\g<2>', text)
        
        # Tipiskās rakstzīmju kļūdas
        replacements = {
            'rn': 'm',  # rn -> m
            'vv': 'w',  # vv -> w
            '|': 'l',   # | -> l (ja nav ciparu kontekstā)
            '¢': 'c',   # ¢ -> c
            '§': 's',   # § -> s
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _fix_latvian_text(self, text: str) -> str:
        """Labo latviešu valodas specifiskās OCR kļūdas"""
        
        # Diakritisko zīmju labošana kontekstā
        latvian_words = {
            'nevareju': 'nevarēju',
            'daudz': 'daudzums',
            'piegadatājs': 'piegādātājs', 
            'sanemejs': 'saņēmējs',
            'kopa': 'kopā',
            'ara': 'ārā',
        }
        
        for wrong, correct in latvian_words.items():
            text = re.sub(r'\b' + re.escape(wrong) + r'\b', correct, text, flags=re.IGNORECASE)
        
        # Diakritisko zīmju atjaunošana bieži lietotiem vārdiem
        # Izmanto word boundaries, lai neaiztiktu citus vārdus
        diacritic_fixes = [
            (r'\bpavadzime\b', 'pavadzīme'),
            (r'\bpiegadatajs\b', 'piegādātājs'),
            (r'\bsanemejs\b', 'saņēmējs'),
            (r'\bdaudzums\b', 'daudzums'),
            (r'\bkopa\b', 'kopā'),
        ]
        
        for pattern, replacement in diacritic_fixes:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _fix_invoice_terms(self, text: str) -> str:
        """Labo pavadzīmju specifisko terminoloģiju"""
        
        for correct_term, variations in self.invoice_terms.items():
            for variation in variations:
                # Case-insensitive replacement
                pattern = re.escape(variation).replace(r'\ ', r'\s+')
                text = re.sub(pattern, correct_term, text, flags=re.IGNORECASE)
        
        # Speciāli PVN gadījumi
        text = re.sub(r'\bp\s*v\s*n\b', 'PVN', text, flags=re.IGNORECASE)
        text = re.sub(r'\bp\s*\.\s*v\s*\.\s*n\s*\.?', 'PVN', text, flags=re.IGNORECASE)
        
        return text
    
    def _structural_cleanup(self, text: str) -> str:
        """Strukturāla teksta tīrīšana"""
        # Noņem liekās rindas
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Izlaiž pārāk īsas rindiņas (iespējams, troksnis)
            if len(line) < 2:
                continue
            # Izlaiž rindiņas ar tikai speciālām rakstzīmēm
            if re.match(r'^[^\w\s]*$', line):
                continue
            cleaned_lines.append(line)
        
        # Apvieno atpakaļ
        text = '\n'.join(cleaned_lines)
        
        # Noņem liekās tukšās rindiņas
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        return text
    
    def extract_structured_data(self, cleaned_text: str) -> Dict[str, any]:
        """
        Ekstraktē strukturētus datus no iztīrītā teksta
        
        Args:
            cleaned_text: Iztīrītais teksts
            
        Returns:
            Dict: Strukturēti dati
        """
        result = {
            'dates': self.extract_dates(cleaned_text),
            'amounts': self.extract_amounts(cleaned_text),
            'supplier_candidates': self.extract_supplier_candidates(cleaned_text),
            'document_number': self.extract_document_number(cleaned_text),
            'items': self.extract_items(cleaned_text)
        }
        
        return result
    
    def extract_dates(self, text: str) -> List[str]:
        """Ekstraktē datumus no teksta"""
        dates = []
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        # Noņem dublikātus, saglabājot secību
        seen = set()
        unique_dates = []
        for date in dates:
            if date not in seen:
                seen.add(date)
                unique_dates.append(date)
        
        return unique_dates
    
    def extract_amounts(self, text: str) -> List[str]:
        """Ekstraktē naudas summas no teksta"""
        amounts = []
        for pattern in self.money_patterns:
            matches = re.findall(pattern, text)
            amounts.extend(matches)
        
        # Normalizē formātu
        normalized_amounts = []
        for amount in amounts:
            # Noņem liekās atstarpes un standartizē formātu
            normalized = re.sub(r'\s+', '', amount)
            normalized = normalized.replace(',', '.')
            normalized_amounts.append(normalized)
        
        return normalized_amounts
    
    def extract_supplier_candidates(self, text: str) -> List[str]:
        """Ekstraktē iespējamos piegādātāju nosaukumus"""
        lines = text.split('\n')
        candidates = []
        
        # Meklē rindiņas ar "SIA", "AS", "UAB" utml.
        company_patterns = [
            r'SIA\s+[A-ZĀĒĪŌŪČĢĶĻŅŠŽ][^,\n]*',
            r'AS\s+[A-ZĀĒĪŌŪČĢĶĻŅŠŽ][^,\n]*',
            r'UAB\s+[A-ZĀĒĪŌŪČĢĶĻŅŠŽ][^,\n]*',
            r'[A-ZĀĒĪŌŪČĢĶĻŅŠŽ][A-ZĀĒĪŌŪČĢĶĻŅŠŽa-zāēīōūčģķļņšž\s&]+(?:SIA|AS|UAB)',
        ]
        
        for line in lines[:10]:  # Skatās tikai pirmās 10 rindiņas
            for pattern in company_patterns:
                matches = re.findall(pattern, line)
                candidates.extend(matches)
        
        return candidates
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """Ekstraktē pavadzīmes numuru"""
        # Meklē pēc "Nr.", "No.", "Numurs" utml.
        patterns = [
            r'(?:Nr\.?|No\.?|Numurs)\s*:?\s*([A-Z0-9\-/]+)',
            r'Pavadzīme\s*(?:Nr\.?|No\.?)\s*:?\s*([A-Z0-9\-/]+)',
            r'Invoice\s*(?:Nr\.?|No\.?)\s*:?\s*([A-Z0-9\-/]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_items(self, text: str) -> List[Dict[str, str]]:
        """Ekstraktē preču rindiņas no teksta"""
        lines = text.split('\n')
        items = []
        
        # Vienkāršots preču rindiņu atpazīšanas algoritms
        # Meklē rindiņas ar ciparu (daudzums) un naudas summu
        for line in lines:
            line = line.strip()
            if len(line) < 5:  # Pārāk īsa rindiņa
                continue
            
            # Pārbauda vai satur ciparus un iespējami naudas summu
            has_numbers = bool(re.search(r'\d+', line))
            has_money = bool(re.search(r'\d+[,\.]\d{2}', line))
            
            if has_numbers and has_money:
                # Mēģina sadalīt rindiņu komponentēs
                parts = re.split(r'\s{2,}', line)  # Sadala pa vairākām atstarpēm
                
                if len(parts) >= 2:
                    item = {
                        'full_line': line,
                        'description': parts[0] if parts else '',
                        'potential_amount': self._extract_number_from_text(line),
                        'potential_price': self._extract_money_from_text(line)
                    }
                    items.append(item)
        
        return items
    
    def _extract_number_from_text(self, text: str) -> Optional[str]:
        """Ekstraktē ciparu no teksta (daudzumam)"""
        # Meklē atsevišķu ciparu (daudzums)
        numbers = re.findall(r'\b\d+(?:[,\.]\d+)?\b', text)
        return numbers[0] if numbers else None
    
    def _extract_money_from_text(self, text: str) -> Optional[str]:
        """Ekstraktē naudas summu no teksta"""
        for pattern in self.money_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        # Ja nav atrasts ar € vai EUR, meklē decimāldaļu
        money_match = re.search(r'\d+[,\.]\d{2}', text)
        return money_match.group(0) if money_match else None
    
    def get_confidence_score(self, original_text: str, cleaned_text: str) -> float:
        """
        Aprēķina tīrīšanas kvalitātes novērtējumu
        
        Args:
            original_text: Oriģinālais teksts
            cleaned_text: Iztīrītais teksts
            
        Returns:
            float: Confidence score 0.0-1.0
        """
        if not original_text or not cleaned_text:
            return 0.0
        
        # Faktori confidence score aprēķināšanai
        factors = []
        
        # 1. Teksta garuma saglabāšana (nedrīkst zust pārāk daudz)
        length_ratio = len(cleaned_text) / len(original_text)
        if 0.7 <= length_ratio <= 1.3:  # Pieņemams garuma diapazons
            factors.append(0.8)
        else:
            factors.append(max(0.2, 1.0 - abs(1.0 - length_ratio)))
        
        # 2. Strukturēto datu atpazīšana
        structured_data = self.extract_structured_data(cleaned_text)
        structure_score = 0.0
        
        if structured_data['dates']:
            structure_score += 0.3
        if structured_data['amounts']:
            structure_score += 0.3
        if structured_data['supplier_candidates']:
            structure_score += 0.2
        if structured_data['document_number']:
            structure_score += 0.2
        
        factors.append(structure_score)
        
        # 3. Valodas kvalitāte (latviaši vārdi)
        cleaned_lower = cleaned_text.lower()
        latvian_terms_found = sum(term in cleaned_lower for term in self.invoice_terms)
        language_score = min(1.0, latvian_terms_found / 3)  # Maksimums 3 termini
        factors.append(language_score)
        
        # Aprēķina vidējo confidence score
        return sum(factors) / len(factors) if factors else 0.0
