"""Utilities for detecting and extracting tables from PDF text."""
import re
from typing import List, Dict, Optional, Tuple
import logging

class TableDetector:
    def __init__(self):
        self.emissions_keywords = [
            'scope', 'ghg', 'emissions', 'co2', 'carbon',
            'direct', 'indirect', 'metric tons', 'tonnes'
        ]
        
    def find_tables(self, text: str) -> List[Dict[str, str]]:
        """Find potential tables containing emissions data in text."""
        tables = []
        
        # Split text into chunks that might be tables
        chunks = self._split_into_chunks(text)
        
        for chunk in chunks:
            if self._is_likely_table(chunk):
                table_data = self._extract_table_data(chunk)
                if table_data:
                    tables.append({
                        'content': chunk,
                        'data': table_data,
                        'score': self._calculate_relevance_score(chunk)
                    })
        
        # Sort tables by relevance score
        return sorted(tables, key=lambda x: x['score'], reverse=True)
    
    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into potential table chunks."""
        # Look for common table indicators
        patterns = [
            # Multiple lines with numbers and consistent spacing
            r'(?:\s*[\w\s\(\)]+\s+\d[\d\.,]+\s*\n){3,}',
            # Lines with | or tab separators
            r'(?:[^\n]+[\|\t][^\n]+\n){3,}',
            # Indented blocks with numbers
            r'(?:\s{2,}[\w\s]+\s{2,}\d[\d\.,]+\s*\n){3,}'
        ]
        
        chunks = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            chunks.extend(match.group() for match in matches)
            
        return chunks
    
    def _is_likely_table(self, text: str) -> bool:
        """Check if text chunk is likely to be a table."""
        # Must have multiple lines
        lines = text.strip().split('\n')
        if len(lines) < 3:
            return False
            
        # Must contain at least one emissions keyword
        if not any(keyword in text.lower() for keyword in self.emissions_keywords):
            return False
            
        # Must have consistent structure across lines
        widths = [len(line.strip()) for line in lines]
        if max(widths) - min(widths) > 20:  # Allow some variation
            return False
            
        # Must contain numbers
        if not re.search(r'\d[\d\.,]+', text):
            return False
            
        return True
        
    def _extract_table_data(self, text: str) -> Optional[Dict[str, str]]:
        """Extract structured data from a table chunk."""
        try:
            # Look for scope 1/2 emissions values
            scope_pattern = r'(?i)scope\s*([12]).*?(\d[\d\.,]+)\s*(mt|tons?|tonnes)'
            
            matches = re.finditer(scope_pattern, text)
            data = {}
            
            for match in matches:
                scope_num = match.group(1)
                value = float(match.group(2).replace(',', ''))
                unit = match.group(3)
                
                data[f'scope_{scope_num}'] = {
                    'value': value,
                    'unit': unit
                }
                
            return data if data else None
            
        except Exception as e:
            logging.warning(f"Error extracting table data: {e}")
            return None
            
    def _calculate_relevance_score(self, text: str) -> float:
        """Calculate how relevant a table chunk is for emissions data."""
        score = 0.0
        text_lower = text.lower()
        
        # Keywords present
        score += sum(2.0 for keyword in self.emissions_keywords 
                    if keyword in text_lower)
        
        # Contains years
        score += len(re.findall(r'\b20\d{2}\b', text)) * 0.5
        
        # Contains numbers in typical emissions ranges
        numbers = [float(n.replace(',', '')) 
                  for n in re.findall(r'\d[\d\.,]+', text)]
        score += sum(0.5 for n in numbers 
                    if 100 <= n <= 10_000_000)  # Typical scope 1/2 range
        
        # Has consistent tabular structure
        if re.search(r'(?:\s*\S+\s+\d+\s*\n){3,}', text):
            score += 2.0
            
        return score