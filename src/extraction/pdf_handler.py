import pdfplumber
import requests
from typing import Optional, List, Dict
import io
from urllib.parse import urljoin
import logging
import re
from bs4 import BeautifulSoup
from ..config import MAX_PDF_SIZE

class DocumentHandler:
    EMISSIONS_KEYWORDS = [
        # Scope patterns with variants
        r'(?i)scope\s*1(?:[,\s]|$)', r'(?i)scope\s*2(?:[,\s]|$)', r'(?i)scope\s*3(?:[,\s]|$)',
        r'(?i)tier\s*1(?:[,\s]|$)', r'(?i)tier\s*2(?:[,\s]|$)', r'(?i)tier\s*3(?:[,\s]|$)',
        # Original keywords with case-insensitive matching
        r'(?i)ghg emissions', r'(?i)co2', r'(?i)greenhouse gas',
        r'(?i)carbon emissions', r'(?i)carbon footprint',
        r'(?i)direct emissions', r'(?i)indirect emissions'
    ]
    UNIT_KEYWORDS = [
        r'(?i)metric tons?', r'(?i)tonnes?', r'(?i)tons?', r'(?i)kg', r'(?i)kilograms?',
        r'(?i)mtco2e?'  # Common CO2 equivalent unit
    ]

    @staticmethod
    def extract_text_from_pdf(url: str, retries: int = 3) -> Optional[str]:
        """Extract text and tables from a PDF URL."""
        headers = {'User-Agent': 'Mozilla/5.0'}
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()

                if int(response.headers.get('content-length', 0)) > MAX_PDF_SIZE:
                    logging.warning(f"PDF too large: {response.headers.get('content-length')} bytes")
                    return None

                pdf_content = io.BytesIO(response.content)
                return DocumentHandler._extract_with_plumber(pdf_content)

            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < retries - 1:
                    continue

        return None

    @staticmethod
    def _extract_with_plumber(pdf_content: io.BytesIO) -> Optional[str]:
        """Extract text and tables from a PDF using pdfplumber."""
        try:
            with pdfplumber.open(pdf_content) as pdf:
                relevant_content = []
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    tables = page.extract_tables()

                    # Check for emissions-related content
                    if DocumentHandler._has_emissions_data(page_text or ""):
                        relevant_content.append(f"=== PAGE {page_num + 1} TEXT ===\n{page_text}")
                    
                    for table in tables:
                        if DocumentHandler._table_has_emissions_data(table):
                            formatted_table = DocumentHandler._format_table(table)
                            relevant_content.append(f"=== PAGE {page_num + 1} TABLE ===\n{formatted_table}")
                
                if not relevant_content:
                    logging.warning("No emissions-related content found.")
                    return None
                
                return "\n".join(relevant_content)

        except Exception as e:
            logging.error(f"Error extracting data with pdfplumber: {str(e)}")
            return None

    @staticmethod
    def _has_emissions_data(text: str) -> bool:
        """Check if text contains emissions-related keywords."""
        if not text:
            return False
        text_lower = text.lower()
        # Add number pattern check alongside keywords
        has_keywords = any(re.search(keyword, text_lower) for keyword in DocumentHandler.EMISSIONS_KEYWORDS)
        has_numbers = bool(re.search(r'\d+(?:,\d{3})*(?:\.\d+)?', text_lower))
        return has_keywords and has_numbers

    @staticmethod
    def _table_has_emissions_data(table: List[List[str]]) -> bool:
        """Check if a table contains emissions-related data."""
        if not table or len(table) < 2:  # Need at least header + data
            return False
            
        # Check header/first row for scope/tier and unit info
        header = " ".join(str(cell).lower() for cell in table[0] if cell)
        has_scope = any(re.search(pattern, header) for pattern in [
            r'(?i)scope\s*[123]', r'(?i)tier\s*[123]'
        ])
        has_units = any(re.search(unit, header) for unit in DocumentHandler.UNIT_KEYWORDS)
        
        if has_scope or has_units:
            # If header has scope or units, check other rows for the missing element
            for row in table[1:]:
                row_text = " ".join(str(cell).lower() for cell in row if cell)
                # If header had scope, look for numbers/units
                if has_scope and re.search(r'\d+(?:,\d{3})*(?:\.\d+)?', row_text):
                    return True
                # If header had units, look for scope references
                if has_units and any(re.search(pattern, row_text) for pattern in [
                    r'(?i)scope\s*[123]', r'(?i)tier\s*[123]'
                ]):
                    return True
        
        # Check each row for emissions keywords
        for i, row in enumerate(table):
            row_text = " ".join(str(cell).lower() for cell in row if cell)
            if any(re.search(keyword, row_text) for keyword in DocumentHandler.EMISSIONS_KEYWORDS):
                # Found keyword, check this and adjacent rows for numbers
                start_idx = max(0, i - 1)
                end_idx = min(len(table), i + 2)
                for check_row in table[start_idx:end_idx]:
                    check_text = " ".join(str(cell).lower() for cell in check_row if cell)
                    if re.search(r'\d+(?:,\d{3})*(?:\.\d+)?', check_text):
                        return True
        return False

    @staticmethod
    def _format_table(table: List[List[str]]) -> str:
        """Format table rows into a readable string with units."""
        formatted_rows = []
        table_text = " ".join(" ".join(str(cell).lower() for cell in row if cell) for row in table)
        
        # Try to find units in entire table first
        table_units = [u for u in DocumentHandler.UNIT_KEYWORDS if re.search(u, table_text)]
        default_unit = table_units[0] if table_units else "unknown unit"
        
        for row in table:
            # Check for unit in this specific row
            row_text = " ".join(cell or "" for cell in row)
            row_units = [u for u in DocumentHandler.UNIT_KEYWORDS if re.search(u, row_text.lower())]
            unit = row_units[0] if row_units else default_unit

            # Append formatted row with detected unit
            formatted_rows.append("\t".join(cell or "" for cell in row) + f" ({unit})")
        return "\n".join(formatted_rows)

    @staticmethod
    def _get_alternative_urls(url: str) -> List[str]:
        """Generate alternative URLs for the PDF."""
        base_url, filename = url.rsplit('/', 1)
        return [
            f"https://web.archive.org/web/2024/{url}",
            urljoin(base_url + '/documents/', filename),
            urljoin(base_url + '/downloads/', filename),
        ]

    @staticmethod
    def extract_text_from_webpage(url: str) -> Optional[str]:
        """Extract text from a webpage."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            main_content = soup.find(["main", "article", "div", "body"])
            if main_content:
                text = main_content.get_text()
            else:
                text = soup.get_text()

            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            return ' '.join(chunk for chunk in chunks if chunk)

        except Exception as e:
            logging.error(f"Error extracting webpage text: {str(e)}")
            return None

    @staticmethod
    def get_document_content(url: str) -> Optional[str]:
        """Get content from either a PDF or a webpage."""
        if url.lower().endswith('.pdf'):
            return DocumentHandler.extract_text_from_pdf(url)
        else:
            return DocumentHandler.extract_text_from_webpage(url)
