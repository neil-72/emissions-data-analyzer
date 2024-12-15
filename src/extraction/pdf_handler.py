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
    # Emissions-related keywords
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

    # Data section indicators
    SECTION_HINTS = [
        r'(?i)appendix',
        r'(?i)data',
        r'(?i)emissions\s+data',
        r'(?i)total\s+emissions',
        r'(?i)corporate\s+emissions',
        r'(?i)comprehensive\s+emissions',
        r'(?i)environmental\s+data'
    ]

    # Unit-related patterns
    UNIT_KEYWORDS = [
        r'(?i)metric tons?', r'(?i)tonnes?', r'(?i)tons?', r'(?i)kg', r'(?i)kilograms?',
        r'(?i)mtco2e?', r'(?i)000\s*tonnes?', r'(?i)mt\s*co2'
    ]

    UNIT_NORMALIZATION = {
        r"(?i)mtco2e?": "metric tons CO2e",
        r"(?i)tco2e?": "metric tons CO2e",
        r"(?i)kilotonnes?": "thousand metric tons CO2e",
        r"(?i)tons?": "metric tons",
        r"(?i)thousand metric tons": "thousand metric tons",
    }

    @staticmethod
    def _normalize_unit(unit_text: str) -> str:
        """Normalize unit text to standard format."""
        for pattern, normalized_unit in DocumentHandler.UNIT_NORMALIZATION.items():
            if re.search(pattern, unit_text):
                return normalized_unit
        return "unknown unit"

    @staticmethod
    def extract_text_from_pdf(url: str, retries: int = 3) -> Optional[str]:
        """Extract text and tables from a PDF URL."""
        headers = {'User-Agent': 'Mozilla/5.0'}
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()

                content_length = int(response.headers.get('content-length', 0))
                if content_length > MAX_PDF_SIZE:
                    logging.warning(f"PDF too large: {content_length} bytes, attempting chunked processing.")
                    return DocumentHandler._process_large_pdf(response.content)

                pdf_content = io.BytesIO(response.content)
                return DocumentHandler._extract_with_plumber(pdf_content)

            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < retries - 1:
                    continue

        return None

    @staticmethod
    def _extract_with_plumber(pdf_content: io.BytesIO) -> Optional[str]:
        """Extract text and tables from a PDF using pdfplumber with enhanced data section handling."""
        try:
            with pdfplumber.open(pdf_content) as pdf:
                relevant_content = []
                total_chars = 0
                max_chars = 50000  # Limit total characters
                
                # First pass - look for data tables in appendix/data sections
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    
                    # Check if this is a data/appendix section
                    if any(re.search(hint, page_text) for hint in DocumentHandler.SECTION_HINTS):
                        tables = page.extract_tables()
                        for table in tables:
                            if DocumentHandler._table_has_emissions_data(table):
                                filtered_rows = DocumentHandler._filter_emissions_rows(table)
                                if filtered_rows:
                                    table_text = DocumentHandler._format_table(filtered_rows)
                                    if total_chars + len(table_text) < max_chars:
                                        relevant_content.append(f"=== PAGE {page_num + 1} TABLE ===\n{table_text}")
                                        total_chars += len(table_text)

                # Second pass - look for other emissions content if needed
                if total_chars < max_chars:
                    for page_num, page in enumerate(pdf.pages):
                        if total_chars >= max_chars:
                            break
                            
                        page_text = page.extract_text() or ""
                        if DocumentHandler._has_emissions_data(page_text):
                            context_text = DocumentHandler._extract_with_context(pdf, page_num)
                            if context_text and total_chars + len(context_text) < max_chars:
                                relevant_content.append(context_text)
                                total_chars += len(context_text)

                if not relevant_content:
                    logging.warning("No emissions-related content found.")
                    return None
                
                result = "\n".join(relevant_content)
                logging.info(f"Extracted {len(result):,} characters of relevant content")
                return result

        except Exception as e:
            logging.error(f"Error extracting data with pdfplumber: {str(e)}")
            return None

    @staticmethod
    def _process_large_pdf(pdf_bytes: bytes) -> Optional[str]:
        """Process large PDFs by extracting text in chunks."""
        try:
            pdf_stream = io.BytesIO(pdf_bytes)
            with pdfplumber.open(pdf_stream) as pdf:
                relevant_content = []
                total_chars = 0
                max_chars = 50000

                # Prioritize data/appendix sections
                for page_num, page in enumerate(pdf.pages):
                    if total_chars >= max_chars:
                        break

                    page_text = page.extract_text() or ""
                    is_data_section = any(re.search(hint, page_text) for hint in DocumentHandler.SECTION_HINTS)
                    
                    # Extract tables from data sections first
                    if is_data_section:
                        tables = page.extract_tables()
                        for table in tables:
                            if DocumentHandler._table_has_emissions_data(table):
                                filtered_rows = DocumentHandler._filter_emissions_rows(table)
                                if filtered_rows:
                                    table_text = DocumentHandler._format_table(filtered_rows)
                                    if total_chars + len(table_text) < max_chars:
                                        relevant_content.append(f"=== PAGE {page_num + 1} TABLE ===\n{table_text}")
                                        total_chars += len(table_text)

                # If we still have room, look for other emissions data
                if total_chars < max_chars:
                    for page_num, page in enumerate(pdf.pages):
                        if total_chars >= max_chars:
                            break
                            
                        page_text = page.extract_text() or ""
                        if DocumentHandler._has_emissions_data(page_text):
                            context_text = DocumentHandler._extract_with_context(pdf, page_num)
                            if context_text and total_chars + len(context_text) < max_chars:
                                relevant_content.append(context_text)
                                total_chars += len(context_text)

                return "\n".join(relevant_content) if relevant_content else None

        except Exception as e:
            logging.error(f"Error processing large PDF: {str(e)}")
            return None

    @staticmethod
    def _extract_with_context(pdf, page_num: int, context_window: int = 1) -> Optional[str]:
        """Extract content from the target page with surrounding context."""
        sections = []
        start = max(0, page_num - context_window)
        end = min(len(pdf.pages), page_num + context_window + 1)

        for i in range(start, end):
            page_text = pdf.pages[i].extract_text() or ""
            if i == page_num or DocumentHandler._has_emissions_data(page_text):
                sections.append(f"=== PAGE {i + 1} ===\n{page_text}")

        return "\n\n".join(sections) if sections else None

    @staticmethod
    def _has_emissions_data(text: str) -> bool:
        """Check if text contains emissions-related keywords and numbers."""
        if not text:
            return False
        text_lower = text.lower()
        has_keywords = any(re.search(keyword, text_lower) for keyword in DocumentHandler.EMISSIONS_KEYWORDS)
        has_numbers = bool(re.search(r'\b\d+(?:,\d{3})*(?:\.\d+)?(?:e[+-]?\d+)?\b', text_lower))
        return has_keywords and has_numbers

    @staticmethod
    def _table_has_emissions_data(table: List[List[str]]) -> bool:
        """Check if a table contains emissions-related data."""
        if not table or len(table) < 2:
            return False
            
        # Check whole table content
        table_text = " ".join(" ".join(str(cell).lower() for cell in row if cell) for row in table)
        
        # Look for scope mentions
        has_scope = any(re.search(pattern, table_text) for pattern in DocumentHandler.EMISSIONS_KEYWORDS)
        
        # Look for units
        has_units = any(re.search(unit, table_text) for unit in DocumentHandler.UNIT_KEYWORDS)
        
        # Look for numbers in typical emissions range (100-1M)
        has_valid_numbers = bool(re.search(r'\b\d{3,8}(?:\.\d+)?\b', table_text))
        
        return has_scope and (has_units or has_valid_numbers)

    @staticmethod
    def _filter_emissions_rows(table: List[List[str]]) -> List[List[str]]:
        """Filter rows that contain emissions-related data."""
        filtered_rows = []
        
        # Always keep header row
        if table and len(table) > 0:
            filtered_rows.append(table[0])
            
        # Filter other rows
        for row in table[1:]:
            row_text = " ".join(str(cell) for cell in row if cell)
            if any(re.search(pattern, row_text.lower()) for pattern in DocumentHandler.EMISSIONS_KEYWORDS):
                filtered_rows.append(row)
                
        return filtered_rows if len(filtered_rows) > 1 else []  # Return empty if only header

    @staticmethod
    def _format_table(table: List[List[str]]) -> str:
        """Format table rows into a readable string with normalized units."""
        if not table:
            return ""

        # Extract a default unit from the entire table text
        table_text = " ".join(" ".join(str(cell).lower() for cell in row if cell) for row in table)
        table_units = [u for u in DocumentHandler.UNIT_KEYWORDS if re.search(u, table_text)]
        default_unit = table_units[0] if table_units else "unknown unit"
        default_unit = DocumentHandler._normalize_unit(default_unit)

        formatted_rows = []
        for row in table:
            # Check for unit in this specific row
            row_text = " ".join(cell or "" for cell in row)
            row_units = [u for u in DocumentHandler.UNIT_KEYWORDS if re.search(u, row_text.lower())]
            unit = row_units[0] if row_units else default_unit
            unit = DocumentHandler._normalize_unit(unit)

            # Append formatted row with detected normalized unit
            formatted_rows.append("\t".join(cell or "" for cell in row) + f" ({unit})")
        return "\n".join(formatted_rows)

    @staticmethod
    def extract_text_from_webpage(url: str) -> Optional[str]:
        """Extract text and table data from a webpage."""
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Extract text
            main_content = soup.find(["main", "article", "div", "body"])
            if main_content:
                text = main_content.get_text()
            else:
                text = soup.get_text()

            # Extract table data
            tables = soup.find_all("table")
            table_texts = []
            for tbl in tables:
                rows = tbl.find_all("tr")
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    row_text = [cell.get_text(strip=True) for cell in cells if cell.get_text(strip=True)]
                    if row_text:
                        table_texts.append("\t".join(row_text))
            table_content = "\n".join(table_texts)

            combined_text = text + "\n" + table_content if table_content else text

            # Clean extra whitespace
            lines = (line.strip() for line in combined_text.splitlines())
            cleaned_text = ' '.join(phrase for line in lines for phrase in line.split("  ") if phrase)
            return cleaned_text

        except Exception as e:
            logging.error(f"Error extracting webpage content: {str(e)}")
            return None

    @staticmethod
    def get_document_content(url: str) -> Optional[str]:
        """Get content from either a PDF or a webpage."""
        if url.lower().endswith('.pdf'):
            return DocumentHandler.extract_text_from_pdf(url)
        else:
            return DocumentHandler.extract_text_from_webpage(url)

