import pdfplumber
import requests
from typing import Optional, List, Dict, Tuple
import io
from urllib.parse import urljoin
import logging
import re
from bs4 import BeautifulSoup
from ..config import MAX_PDF_SIZE

class DocumentHandler:
    # Enhanced keyword patterns for better detection
    EMISSIONS_KEYWORDS = [
        # Direct scope references
        r'(?i)scope\s*1\b', r'(?i)scope\s*2\b', r'(?i)scope\s*3\b',
        r'(?i)scope\s*1[,\s]', r'(?i)scope\s*2[,\s]', r'(?i)scope\s*3[,\s]',
        
        # Emissions terms
        r'(?i)ghg\s*emissions?',
        r'(?i)co2\s*(?:emissions|equivalent)',
        r'(?i)greenhouse\s*gas(?:\s*emissions)?',
        r'(?i)carbon\s*(?:emissions|footprint|dioxide)',
        r'(?i)direct\s*emissions?',
        r'(?i)indirect\s*emissions?',
        
        # Table and section headers
        r'(?i)emissions?\s*(?:data|summary|inventory|report)',
        r'(?i)carbon\s*(?:data|inventory|metrics)',
        
        # Numerical patterns with units
        r'\d+(?:,\d{3})*(?:\.\d+)?\s*(?:mt|t)(?:co2|co2e|carbon)',
        r'\d+(?:,\d{3})*(?:\.\d+)?\s*(?:metric\s*tons?)(?:co2|co2e)'
    ]

    # Enhanced unit detection patterns
    UNIT_KEYWORDS = [
        r'(?i)metric\s*tons?\s*(?:co2e?)?',
        r'(?i)tonnes?\s*(?:co2e?)?',
        r'(?i)mt(?:co2e?)?',
        r'(?i)tco2e?',
        r'(?i)kilograms?\s*(?:co2e?)?',
        r'(?i)kg\s*co2e?'
    ]

    @staticmethod
    def extract_text_from_pdf(url: str, retries: int = 3) -> Optional[str]:
        """Extract text and tables from a PDF URL with retry logic."""
        headers = {'User-Agent': 'Mozilla/5.0'}
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()

                content_length = int(response.headers.get('content-length', 0))
                if content_length > MAX_PDF_SIZE:
                    logging.warning(f"PDF too large: {content_length} bytes")
                    return None

                pdf_content = io.BytesIO(response.content)
                extracted_content = DocumentHandler._extract_with_plumber(pdf_content)
                
                if extracted_content:
                    return extracted_content
                
                # If no emissions content found, try alternative extraction
                return DocumentHandler._extract_with_plumber(pdf_content, fallback=True)

            except requests.RequestException as e:
                logging.error(f"HTTP request failed on attempt {attempt + 1}: {str(e)}")
                if attempt < retries - 1:
                    continue
            except Exception as e:
                logging.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                if attempt < retries - 1:
                    continue

        return None

    @staticmethod
    def _extract_with_plumber(pdf_content: io.BytesIO, fallback: bool = False) -> Optional[str]:
        """Extract text and tables from a PDF using pdfplumber with enhanced detection."""
        try:
            with pdfplumber.open(pdf_content) as pdf:
                emissions_content = []
                all_content = []
                page_context = {}  # Store context for each page
                
                # First pass: Extract all content and build context
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text() or ""
                    tables = page.extract_tables()
                    
                    # Store full page content
                    page_content = f"=== PAGE {page_num} TEXT ===\n{page_text}"
                    all_content.append(page_content)
                    
                    # Extract tables with context
                    for table in tables:
                        if table:  # Skip empty tables
                            formatted_table = DocumentHandler._format_table(table)
                            table_content = f"=== PAGE {page_num} TABLE ===\n{formatted_table}"
                            all_content.append(table_content)
                            
                            # Check for emissions data in table
                            if DocumentHandler._table_has_emissions_data(table):
                                emissions_content.append(table_content)
                                page_context[page_num] = True
                    
                    # Check for emissions data in text
                    if DocumentHandler._has_emissions_data(page_text):
                        emissions_content.append(page_content)
                        page_context[page_num] = True
                        
                        # Include adjacent pages for context
                        for adj_page in [page_num - 1, page_num + 1]:
                            if adj_page > 0 and adj_page <= len(pdf.pages):
                                page_context[adj_page] = True
                
                # If we found emissions content, return it with context
                if emissions_content:
                    # Add relevant context pages
                    context_content = []
                    for page_num, content in enumerate(all_content, 1):
                        if page_num in page_context:
                            context_content.append(content)
                    
                    return "\n\n".join(context_content)
                
                # Fallback: return all content if requested and no emissions content found
                if fallback:
                    logging.warning("No emissions-specific content found, returning full content")
                    return "\n\n".join(all_content)
                
                logging.warning("No emissions-related content found")
                return None

        except Exception as e:
            logging.error(f"Error extracting data with pdfplumber: {str(e)}")
            return None

    @staticmethod
    def _has_emissions_data(text: str) -> bool:
        """Enhanced check for emissions-related content in text."""
        if not text:
            return False
            
        text_lower = text.lower()
        
        # Check for keywords
        if any(re.search(keyword, text_lower) for keyword in DocumentHandler.EMISSIONS_KEYWORDS):
            return True
            
        # Look for numerical patterns that might indicate emissions data
        numbers_with_units = re.findall(
            r'\d+(?:,\d{3})*(?:\.\d+)?\s*(?:mt|tons?|tonnes?|kg)(?:\s*co2e?)?',
            text_lower
        )
        
        return len(numbers_with_units) > 0

    @staticmethod
    def _table_has_emissions_data(table: List[List[str]]) -> bool:
        """Enhanced detection of emissions data in tables."""
        if not table:
            return False

        # Check header row for emissions indicators
        if table[0]:
            header = [str(cell).lower() for cell in table[0] if cell]
            header_text = " ".join(header)
            if any(re.search(keyword, header_text) for keyword in DocumentHandler.EMISSIONS_KEYWORDS):
                return True

        # Analyze each row for patterns indicating emissions data
        for row in table:
            row_text = " ".join(str(cell).lower() for cell in row if cell)
            
            # Check for direct keyword matches
            if any(re.search(keyword, row_text) for keyword in DocumentHandler.EMISSIONS_KEYWORDS):
                # If we find a keyword and a number, likely emissions data
                if re.search(r'\d+(?:,\d{3})*(?:\.\d+)?', row_text):
                    return True

        return False

    @staticmethod
    def _format_table(table: List[List[str]]) -> str:
        """Enhanced table formatting with improved unit detection."""
        if not table:
            return ""

        formatted_rows = []
        header = None

        # Process header separately if it exists
        if table[0]:
            header = table[0]
            formatted_rows.append("\t".join(str(cell) for cell in header))

        # Process data rows
        for row in table[1:] if header else table:
            row_text = " ".join(str(cell) for cell in row if cell)
            
            # Enhanced unit detection
            units = []
            for unit_pattern in DocumentHandler.UNIT_KEYWORDS:
                matches = re.finditer(unit_pattern, row_text.lower())
                units.extend(match.group(0) for match in matches)
            
            # Use most specific unit if multiple found
            unit = next((u for u in units if 'co2' in u.lower()), units[0] if units else "unknown unit")
            
            formatted_row = "\t".join(str(cell) for cell in row)
            formatted_rows.append(f"{formatted_row} ({unit})")

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
        """Extract text from a webpage with improved content extraction."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove non-content elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()

            # Try to find main content area
            content_priorities = [
                soup.find("main"),
                soup.find("article"),
                soup.find(id=re.compile(r"(?i)content|main|article")),
                soup.find(class_=re.compile(r"(?i)content|main|article")),
                soup.find("body")
            ]

            content = next((el for el in content_priorities if el), soup)
            
            # Extract text while preserving some structure
            lines = []
            for element in content.stripped_strings:
                line = element.strip()
                if line:
                    lines.append(line)

            return '\n'.join(lines)

        except Exception as e:
            logging.error(f"Error extracting webpage text: {str(e)}")
            return None

    @staticmethod
    def get_document_content(url: str) -> Optional[str]:
        """Get content from either a PDF or a webpage with improved handling."""
        try:
            if url.lower().endswith('.pdf'):
                content = DocumentHandler.extract_text_from_pdf(url)
                if not content:
                    # Try alternative URLs if primary URL fails
                    for alt_url in DocumentHandler._get_alternative_urls(url):
                        content = DocumentHandler.extract_text_from_pdf(alt_url)
                        if content:
                            break
                return content
            else:
                return DocumentHandler.extract_text_from_webpage(url)
        except Exception as e:
            logging.error(f"Error getting document content: {str(e)}")
            return None
