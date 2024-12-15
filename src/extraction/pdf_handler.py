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
    """Enhanced document handler for extracting emissions data from PDFs and webpages."""
    
    EMISSIONS_KEYWORDS = [
        # Core emissions patterns
        r'(?i)scope\s*[123](?:[,\s]|$)',  # Matches Scope 1/2/3 with various separators
        r'(?i)ghg[\s-]*emissions?',
        r'(?i)carbon[\s-]*(?:emissions|footprint|dioxide)',
        r'(?i)co2[\s-]*(?:emissions?|equivalent)',
        r'(?i)greenhouse[\s-]*gas(?:[\s-]*emissions?)?',
        
        # Broader emissions context
        r'(?i)emissions?[\s-]*(?:data|summary|inventory|report|intensity)',
        r'(?i)carbon[\s-]*(?:data|inventory|metrics|reporting)',
        r'(?i)climate[\s-]*(?:data|metrics|impact)',
        
        # Table indicators
        r'(?i)emissions?[\s-]*(?:by|per|across)[\s-]*(?:scope|category|year)',
        r'(?i)(?:total|annual)[\s-]*(?:ghg|carbon|co2)[\s-]*emissions?',
        
        # Numerical patterns with common units
        r'\d+(?:,\d{3})*(?:\.\d+)?[\s-]*(?:mt|t|tons?|tonnes?)[\s-]*(?:co2|co2e|carbon)',
        r'\d+(?:,\d{3})*(?:\.\d+)?[\s-]*(?:kg|kilos?)[\s-]*(?:co2|co2e)',
        r'\d+(?:,\d{3})*(?:\.\d+)?[\s-]*mtco2e?'
    ]

    UNIT_KEYWORDS = [
        # Standard units
        r'(?i)metric[\s-]*tons?(?:[\s-]*(?:co2|co2e|carbon))?',
        r'(?i)(?:mt|t)(?:co2|co2e)?',
        r'(?i)tonnes?(?:[\s-]*(?:co2|co2e|carbon))?',
        r'(?i)kilograms?[\s-]*(?:co2|co2e)?',
        r'(?i)kg[\s-]*(?:co2|co2e)?',
        
        # Variations and abbreviations
        r'(?i)mtco2e?',
        r'(?i)tco2e?',
        r'(?i)kt(?:co2|co2e)?',
        r'(?i)g(?:co2|co2e)?'
    ]

    @staticmethod
    def extract_text_from_pdf(url: str, retries: int = 3) -> Optional[str]:
        """Extract text and tables from a PDF URL with enhanced retry logic."""
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()

                content_length = int(response.headers.get('content-length', 0))
                if content_length > MAX_PDF_SIZE:
                    logging.warning(f"PDF exceeds size limit: {content_length} bytes")
                    return None

                pdf_content = io.BytesIO(response.content)
                
                # Try primary extraction
                extracted_content = DocumentHandler._extract_with_plumber(pdf_content)
                if extracted_content:
                    return extracted_content
                
                # Fallback to full content if no emissions data found
                if attempt == retries - 1:
                    return DocumentHandler._extract_with_plumber(pdf_content, fallback=True)

            except requests.RequestException as e:
                logging.error(f"HTTP request failed (attempt {attempt + 1}): {str(e)}")
                if attempt == retries - 1:
                    break
            except Exception as e:
                logging.error(f"PDF extraction error (attempt {attempt + 1}): {str(e)}")
                if attempt == retries - 1:
                    break

        return None

    @staticmethod
    def _extract_with_plumber(pdf_content: io.BytesIO, fallback: bool = False) -> Optional[str]:
        """Extract and process PDF content with enhanced emissions detection."""
        try:
            with pdfplumber.open(pdf_content) as pdf:
                all_content = []
                emissions_pages = set()
                context_buffer = []
                
                # First pass: Identify relevant pages and extract content
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text() or ""
                    tables = page.extract_tables()
                    
                    # Process page text
                    if DocumentHandler._has_emissions_data(page_text):
                        emissions_pages.add(page_num)
                        # Add surrounding pages for context
                        emissions_pages.update(range(max(1, page_num - 1), min(len(pdf.pages), page_num + 2)))
                    
                    # Format page content
                    page_content = [f"=== PAGE {page_num} TEXT ===\n{page_text}"]
                    
                    # Process tables
                    for table_num, table in enumerate(tables, 1):
                        if table and any(row for row in table):  # Skip empty tables
                            table_content = DocumentHandler._format_table(table)
                            if table_content:
                                page_content.append(f"=== PAGE {page_num} TABLE {table_num} ===\n{table_content}")
                                
                                if DocumentHandler._table_has_emissions_data(table):
                                    emissions_pages.add(page_num)
                                    emissions_pages.update(range(max(1, page_num - 1), min(len(pdf.pages), page_num + 2)))
                    
                    all_content.append((page_num, "\n\n".join(page_content)))

                # Second pass: Compile relevant content with context
                if emissions_pages and not fallback:
                    return "\n\n".join(content for page_num, content in all_content if page_num in emissions_pages)
                elif fallback:
                    return "\n\n".join(content for _, content in all_content)
                
                logging.info("No emissions data found in document")
                return None

        except Exception as e:
            logging.error(f"PDF extraction error: {str(e)}")
            return None

    @staticmethod
    def _has_emissions_data(text: str) -> bool:
        """Enhanced detection of emissions-related content in text."""
        if not text:
            return False
            
        text = text.lower()
        
        # Check for emissions keywords
        if any(re.search(pattern, text) for pattern in DocumentHandler.EMISSIONS_KEYWORDS):
            return True
            
        # Check for numerical patterns with units
        number_pattern = r'\d+(?:,\d{3})*(?:\.\d+)?'
        for unit_pattern in DocumentHandler.UNIT_KEYWORDS:
            if re.search(f"{number_pattern}\\s*{unit_pattern}", text):
                return True
        
        return False

    @staticmethod
    def _table_has_emissions_data(table: List[List[str]]) -> bool:
        """Enhanced detection of emissions data in tables."""
        if not table:
            return False

        # Convert table to text for analysis
        table_text = "\n".join(" ".join(str(cell) for cell in row if cell) for row in table)
        table_text = table_text.lower()
        
        # Quick keyword check
        has_keywords = any(re.search(pattern, table_text) for pattern in DocumentHandler.EMISSIONS_KEYWORDS)
        if not has_keywords:
            return False
            
        # Check for numbers with units
        number_pattern = r'\d+(?:,\d{3})*(?:\.\d+)?'
        has_numbers_with_units = any(
            re.search(f"{number_pattern}\\s*{unit_pattern}", table_text)
            for unit_pattern in DocumentHandler.UNIT_KEYWORDS
        )
        
        return has_numbers_with_units

    @staticmethod
    def _format_table(table: List[List[str]]) -> str:
        """Format table data with enhanced structure preservation."""
        if not table:
            return ""

        # Clean and normalize cells
        cleaned_table = []
        for row in table:
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cleaned_row.append("")
                else:
                    # Normalize whitespace while preserving structure
                    cell_text = re.sub(r'\s+', ' ', str(cell)).strip()
                    cleaned_row.append(cell_text)
            cleaned_table.append(cleaned_row)

        # Format as tab-separated values
        return "\n".join("\t".join(row) for row in cleaned_table)

    @staticmethod
    def extract_text_from_webpage(url: str) -> Optional[str]:
        """Extract text from webpage with improved content detection."""
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

            # Find main content area
            content_areas = [
                soup.find("main"),
                soup.find("article"),
                soup.find(id=re.compile(r"(?i)content|main|article")),
                soup.find(class_=re.compile(r"(?i)content|main|article")),
                soup.find("body")
            ]

            content = next((area for area in content_areas if area), soup)
            
            # Extract text with structure preservation
            text_blocks = []
            for element in content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th']):
                text = element.get_text(strip=True)
                if text:
                    text_blocks.append(text)

            return '\n'.join(text_blocks)

        except Exception as e:
            logging.error(f"Webpage extraction error: {str(e)}")
            return None

    @staticmethod
    def get_document_content(url: str) -> Optional[str]:
        """Get content from either PDF or webpage with fallback handling."""
        try:
            if url.lower().endswith('.pdf'):
                content = DocumentHandler.extract_text_from_pdf(url)
                if not content:
                    # Try alternative URLs
                    alt_urls = [
                        f"https://web.archive.org/web/2024/{url}",
                        urljoin(url.rsplit('/', 1)[0] + '/documents/', url.rsplit('/', 1)[1]),
                        urljoin(url.rsplit('/', 1)[0] + '/downloads/', url.rsplit('/', 1)[1])
                    ]
                    for alt_url in alt_urls:
                        content = DocumentHandler.extract_text_from_pdf(alt_url)
                        if content:
                            break
                return content
            else:
                return DocumentHandler.extract_text_from_webpage(url)
        except Exception as e:
            logging.error(f"Document extraction error: {str(e)}")
            return None
