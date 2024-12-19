import logging
from typing import Optional, Dict, Any
import io
import requests
from parsestudio import DoclingParser
from ..config import MAX_PDF_SIZE  # Keeping your existing config import

class DocumentHandler:
    """Enhanced PDF Document Handler for Emissions Data Extraction
    Combines ParseStudio's robust parsing with emissions-specific extraction logic
    """
    def __init__(self):
        # Initialize ParseStudio parser
        self.parser = DoclingParser()
        
        # Emissions-specific patterns (keeping your core functionality)
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
        """Enhanced document processing using ParseStudio"""
        try:
            # Use ParseStudio to parse the document
            parsed_content = self.parser.parse(pdf_content)
            
            if not parsed_content:
                logging.warning("No content extracted from PDF")
                return None

            # Extract emissions-relevant sections
            emissions_data = {
                'tables': self._extract_emissions_tables(parsed_content),
                'text_blocks': self._extract_emissions_text(parsed_content),
                'metadata': self._extract_metadata(parsed_content)
            }

            return self._structure_emissions_data(emissions_data)

        except Exception as e:
            logging.error(f"Error processing document content: {str(e)}")
            return None

    def _extract_emissions_tables(self, parsed_content: Dict) -> list:
        """Extracts and processes tables containing emissions data"""
        emissions_tables = []
        
        # ParseStudio provides structured table access
        for table in parsed_content.get('tables', []):
            if self._is_emissions_table(table):
                processed_table = self._process_emissions_table(table)
                if processed_table:
                    emissions_tables.append(processed_table)
        
        return emissions_tables

    def _extract_emissions_text(self, parsed_content: Dict) -> list:
        """Extracts text blocks containing emissions data"""
        emissions_blocks = []
        
        for block in parsed_content.get('text_blocks', []):
            if self._contains_emissions_data(block):
                emissions_blocks.append({
                    'content': block.get('text', ''),
                    'page': block.get('page_number'),
                    'context': self._get_surrounding_context(block)
                })
        
        return emissions_blocks

    def _is_emissions_table(self, table: Dict) -> bool:
        """Improved emissions table detection"""
        if not table:
            return False

        # Check table headers and content for emissions-related terms
        headers = table.get('headers', [])
        first_column = table.get('first_column', [])
        
        # Look for emissions-related patterns in headers and first column
        header_text = ' '.join(str(h) for h in headers if h)
        column_text = ' '.join(str(c) for c in first_column if c)
        
        return any(
            any(pattern.search(text) for pattern in patterns)
            for patterns in self.emissions_patterns.values()
            for text in [header_text, column_text]
        )

    def _process_emissions_table(self, table: Dict) -> Optional[Dict]:
        """Enhanced emissions table processing"""
        try:
            processed = {
                'headers': table.get('headers', []),
                'data': table.get('data', []),
                'page': table.get('page_number'),
                'emissions_data': []
            }

            # Extract specific emissions values and contexts
            for row in processed['data']:
                emissions_entry = self._extract_row_emissions(row)
                if emissions_entry:
                    processed['emissions_data'].append(emissions_entry)

            return processed if processed['emissions_data'] else None

        except Exception as e:
            logging.error(f"Error processing emissions table: {str(e)}")
            return None

    def _structure_emissions_data(self, extracted_data: Dict) -> Dict:
        """Structures extracted emissions data into a standardized format"""
        return {
            'scope1_emissions': self._find_scope1_emissions(extracted_data),
            'scope2_emissions': self._find_scope2_emissions(extracted_data),
            'reporting_year': self._find_reporting_year(extracted_data),
            'data_quality': self._assess_data_quality(extracted_data),
            'source_context': self._get_source_context(extracted_data)
        }

    def _find_scope1_emissions(self, data: Dict) -> Optional[Dict]:
        """Enhanced Scope 1 emissions extraction"""
        for table in data.get('tables', []):
            if table.get('emissions_data'):
                for entry in table['emissions_data']:
                    if entry.get('scope') == 1:
                        return {
                            'value': entry.get('value'),
                            'unit': entry.get('unit'),
                            'context': entry.get('context')
                        }
        return None

    def _find_scope2_emissions(self, data: Dict) -> Optional[Dict]:
        """Enhanced Scope 2 emissions extraction with market/location based distinction"""
        scope2_data = {
            'location_based': None,
            'market_based': None
        }
        
        for table in data.get('tables', []):
            if table.get('emissions_data'):
                for entry in table['emissions_data']:
                    if entry.get('scope') == 2:
                        if 'location' in entry.get('context', '').lower():
                            scope2_data['location_based'] = entry
                        elif 'market' in entry.get('context', '').lower():
                            scope2_data['market_based'] = entry
        
        return scope2_data if any(scope2_data.values()) else None

    def _assess_data_quality(self, data: Dict) -> Dict:
        """Assesses the quality and reliability of extracted data"""
        return {
            'has_tables': bool(data.get('tables')),
            'has_text_blocks': bool(data.get('text_blocks')),
            'completeness': self._calculate_completeness(data),
            'confidence_score': self._calculate_confidence(data)
        }

    def _calculate_completeness(self, data: Dict) -> float:
        """Calculates data completeness score"""
        required_fields = ['scope1_emissions', 'scope2_emissions', 'reporting_year']
        present_fields = sum(1 for field in required_fields if data.get(field))
        return present_fields / len(required_fields)

    def _calculate_confidence(self, data: Dict) -> float:
        """Calculates confidence score for extracted data"""
        confidence_factors = {
            'has_tables': 0.4,
            'has_text_validation': 0.3,
            'has_metadata': 0.3
        }
        
        score = 0.0
        if data.get('tables'):
            score += confidence_factors['has_tables']
        if data.get('text_blocks'):
            score += confidence_factors['has_text_validation']
        if data.get('metadata'):
            score += confidence_factors['has_metadata']
            
        return round(score, 2)
