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
        r'(?i)scope\s*1', r'(?i)scope\s*2', r'(?i)scope\s*3',
        'ghg emissions', 'co2', 'greenhouse gas',
        'carbon emissions', 'carbon footprint',
        'direct emissions', 'indirect emissions'
    ]
    UNIT_KEYWORDS = [
        r'metric tons', r'tonnes', r'tons', r'kg', r'kilograms'
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
        text_lower = text.lower()
        return any(re.search(keyword, text_lower) for keyword in DocumentHandler.EMISSIONS_KEYWORDS)

    @staticmethod
    def _table_has_emissions_data(table: List[List[str]]) -> bool:
        """Check if a table contains emissions-related data."""
        for row in table:
            row_text = " ".join(cell.lower() for cell in row if cell)
            if any(re.search(keyword, row_text) for keyword in DocumentHandler.EMISSIONS_KEYWORDS):
                return True
        return False

    @staticmethod
    def _format_table(table: List[List[str]]) -> str:
        """Format table rows into a readable string with units."""
        formatted_rows = []
        for row in table:
            # Extract the unit if present in the row
            row_text = " ".join(cell or "" for cell in row)
            units = [u for u in DocumentHandler.UNIT_KEYWORDS if re.search(u, row_text.lower())]
            unit = units[0] if units else "unknown unit"

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
