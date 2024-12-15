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
        r'(?i)scope\s*1\s*and\s*2', r'(?i)location-based', r'(?i)market-based',
        r'(?i)tier\s*1(?:[,\s]|$)', r'(?i)tier\s*2(?:[,\s]|$)', r'(?i)tier\s*3(?:[,\s]|$)',
        # General emissions terms
        r'(?i)ghg emissions', r'(?i)co2', r'(?i)greenhouse gas',
        r'(?i)carbon emissions', r'(?i)carbon footprint', r'(?i)gross emissions',
        r'(?i)net carbon footprint', r'(?i)total emissions', r'(?i)subtotal emissions',
        r'(?i)carbon offsets'
    ]
    UNIT_KEYWORDS = [
        r'(?i)metric tons?', r'(?i)tonnes?', r'(?i)tons?', r'(?i)kg', r'(?i)kilograms?',
        r'(?i)mtco2e?', r'(?i)000\s*tonnes?', r'(?i)mt\s*co2'
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
        has_keywords = any(re.search(keyword, text_lower) for keyword in DocumentHandler.EMISSIONS_KEYWORDS)
        has_numbers = bool(re.search(r'\b\d+(?:,\d{3})*(?:\.\d+)?(?:e[+-]?\d+)?\b', text_lower))  # Handles scientific notation
        return has_keywords and has_numbers

    @staticmethod
    def _table_has_emissions_data(table: List[List[str]]) -> bool:
        """Check if a table contains emissions-related data."""
        if not table or len(table) < 2:  # Need at least header + data
            return False
            
        # Check header/first row for scope/tier and unit info
        header = " ".join(str(cell).lower() for cell in table[0] if cell)
        has_scope = any(re.search(pattern, header) for pattern in DocumentHandler.EMISSIONS_KEYWORDS)
        has_units = any(re.search(unit, header) for unit in DocumentHandler.UNIT_KEYWORDS)

        # If scope/units are in header, verify rows for numbers
        if has_scope or has_units:
            for row in table[1:]:
                row_text = " ".join(str(cell).lower() for cell in row if cell)
                if re.search(r'\b\d+(?:,\d{3})*(?:\.\d+)?(?:e[+-]?\d+)?\b', row_text):  # Numbers in rows
                    return True

        # Keyword and number check for specific rows
        for row in table:
            row_text = " ".join(str(cell).lower() for cell in row if cell)
            if any(re.search(keyword, row_text) for keyword in DocumentHandler.EMISSIONS_KEYWORDS) and re.search(r'\d+', row_text):
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
    def extract_text_from_webpage(url: str) -> Optional[str]:
        """Extract text from a webpage."""
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            main_content = soup.find(["main", "article", "div", "body"])
            text = main_content.get_text() if main_content else soup.get_text()

            lines = (line.strip() for line in text.splitlines())
            return ' '.join(phrase for line in lines for phrase in line.split("  ") if phrase)

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
