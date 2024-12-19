import logging
from typing import Optional, Dict, Any
import io
import requests
from parsestudio.pdf import Pdf  # Corrected import
from ..config import MAX_PDF_SIZE

class DocumentHandler:
    """Enhanced PDF Document Handler for Emissions Data Extraction"""
    def __init__(self):
        # Emissions-specific patterns
        self.emissions_patterns = {
            'scope1': [
                r'(?i)scope\s*1\s*emissions?',
                r'(?i)direct\s*emissions?',
                r'(?i)scope\s*1.*?[\d,.]+\s*(?:tco2e?|tons?)',
            ],
            'scope2': [
                r'(?i)scope\s*2\s*emissions?',
                r'(?i)indirect\s*emissions?',
                r'(?i)(?:location|market).based.*?[\d,.]+\s*(?:tco2e?|tons?)',
            ],
            'year': [
                r'(?i)(?:fy|year|20)\d{2}',
                r'(?i)reporting\s*period',
            ]
        }

    def get_document_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Downloads and processes PDF document with enhanced error handling"""
        try:
            response = requests.get(
                url,
                headers={'User-Agent': 'Mozilla/5.0'},
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            
            if 'application/pdf' not in response.headers.get('content-type', '').lower():
                logging.warning(f"URL {url} does not point to a PDF")
                return None

            if 'content-length' in response.headers:
                content_length = int(response.headers['content-length'])
                if content_length > MAX_PDF_SIZE:
                    logging.warning(f"PDF size ({content_length} bytes) exceeds maximum allowed size")
                    return None

            return self._process_document(io.BytesIO(response.content))

        except requests.RequestException as e:
            logging.error(f"Failed to fetch PDF: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error processing document: {str(e)}")
            return None

    def _process_document(self, pdf_content: io.BytesIO) -> Optional[Dict[str, Any]]:
        """Process document using ParseStudio's PDF parser"""
        try:
            # Initialize PDF parser with content
            pdf = Pdf(pdf_content)
            
            # Extract text and tables
            content = {
                'text': pdf.extract_text(),
                'tables': pdf.extract_tables(),
                'metadata': pdf.get_metadata()
            }
            
            # Process extracted content
            emissions_data = {
                'tables': self._extract_emissions_tables(content['tables']),
                'text_blocks': self._extract_emissions_text(content['text']),
                'metadata': content['metadata']
            }

            return self._structure_emissions_data(emissions_data)

        except Exception as e:
            logging.error(f"Error processing document content: {str(e)}")
            return None

    def _extract_emissions_tables(self, tables: list) -> list:
        """Extract and process tables containing emissions data"""
        emissions_tables = []
        
        for table in tables:
            if self._is_emissions_table(table):
                processed_table = self._process_emissions_table(table)
                if processed_table:
                    emissions_tables.append(processed_table)
        
        return emissions_tables

    def _extract_emissions_text(self, text: str) -> list:
        """Extract text blocks containing emissions data"""
        emissions_blocks = []
        
        # Split text into paragraphs/blocks
        blocks = text.split('\n\n')
        
        for block in blocks:
            if self._contains_emissions_data(block):
                emissions_blocks.append({
                    'content': block,
                    'context': self._get_surrounding_context(block)
                })
        
        return emissions_blocks

    def _is_emissions_table(self, table: list) -> bool:
        """Check if table contains emissions data"""
        if not table or not table[0]:  # Check if table has headers
            return False

        # Convert first row (headers) to string for pattern matching
        header_text = ' '.join(str(cell) for cell in table[0])
        
        # Check if any emissions patterns match the headers
        return any(
            pattern in header_text.lower()
            for patterns in self.emissions_patterns.values()
            for pattern in patterns
        )

    def _process_emissions_table(self, table: list) -> Optional[Dict]:
        """Process emissions table data"""
        try:
            headers = table[0]
            data = table[1:]
            
            processed = {
                'headers': headers,
                'data': [],
                'emissions_data': []
            }

            for row in data:
                if row:  # Skip empty rows
                    emissions_entry = self._extract_row_emissions(row, headers)
                    if emissions_entry:
                        processed['emissions_data'].append(emissions_entry)
                        processed['data'].append(row)

            return processed if processed['emissions_data'] else None

        except Exception as e:
            logging.error(f"Error processing emissions table: {str(e)}")
            return None

    def _extract_row_emissions(self, row: list, headers: list) -> Optional[Dict]:
        """Extract emissions data from a table row"""
        try:
            emissions_data = {}
            
            for header, value in zip(headers, row):
                header_lower = str(header).lower()
                
                # Identify scope
                if 'scope 1' in header_lower:
                    emissions_data['scope'] = 1
                    emissions_data['value'] = self._extract_numeric_value(str(value))
                elif 'scope 2' in header_lower:
                    emissions_data['scope'] = 2
                    if 'location' in header_lower:
                        emissions_data['type'] = 'location-based'
                    elif 'market' in header_lower:
                        emissions_data['type'] = 'market-based'
                    emissions_data['value'] = self._extract_numeric_value(str(value))
                
                # Extract year if present
                if any(pattern in header_lower for pattern in self.emissions_patterns['year']):
                    emissions_data['year'] = self._extract_year(str(value))

            return emissions_data if emissions_data.get('value') is not None else None

        except Exception as e:
            logging.error(f"Error extracting row emissions: {str(e)}")
            return None

    def _extract_numeric_value(self, text: str) -> Optional[float]:
        """Extract numeric value from text, handling different formats"""
        try:
            # Remove common non-numeric characters except decimal points
            clean_text = ''.join(c for c in text if c.isdigit() or c in '.-')
            return float(clean_text) if clean_text else None
        except ValueError:
            return None

    def _contains_emissions_data(self, text: str) -> bool:
        """Check if text block contains emissions-related data"""
        text_lower = text.lower()
        return any(
            pattern in text_lower
            for patterns in self.emissions_patterns.values()
            for pattern in patterns
        )

    def _get_surrounding_context(self, text: str, context_window: int = 100) -> str:
        """Get surrounding context for a piece of text"""
        # This is a simplified version - could be enhanced based on needs
        return text[:context_window] + '...' if len(text) > context_window else text

    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from text"""
        import re
        year_match = re.search(r'20\d{2}', text)
        if year_match:
            return int(year_match.group())
        return None

    def _structure_emissions_data(self, extracted_data: Dict) -> Dict:
        """Structure extracted emissions data into standardized format"""
        structured_data = {
            'scope1_emissions': self._find_scope1_emissions(extracted_data),
            'scope2_emissions': self._find_scope2_emissions(extracted_data),
            'reporting_year': self._find_reporting_year(extracted_data),
            'data_quality': self._assess_data_quality(extracted_data),
            'source_context': self._get_source_context(extracted_data)
        }
        
        # Add raw text representation for Claude analyzer
        structured_data['text_content'] = self._create_text_representation(extracted_data)
        return structured_data

    def _create_text_representation(self, data: Dict) -> str:
        """Creates a text representation of the extracted data for Claude analyzer"""
        text_parts = []
        
        # Add tables content
        if data.get('tables'):
            text_parts.append("EMISSIONS DATA TABLES:")
            for table in data['tables']:
                if isinstance(table, dict) and table.get('data'):
                    headers = table.get('headers', [])
                    text_parts.append(" | ".join(str(h) for h in headers))
                    for row in table['data']:
                        text_parts.append(" | ".join(str(cell) for cell in row))
                text_parts.append("\n")
        
        # Add text blocks
        if data.get('text_blocks'):
            text_parts.append("EMISSIONS TEXT SECTIONS:")
            for block in data['text_blocks']:
                if isinstance(block, dict):
                    text_parts.append(block.get('content', ''))
                    text_parts.append(f"Context: {block.get('context', '')}\n")
                else:
                    text_parts.append(str(block))
        
        return "\n".join(text_parts)
