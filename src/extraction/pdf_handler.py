import PyPDF2
import requests
from typing import Optional, List, Dict
import io
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
import logging
import re
from ..config import MAX_PDF_SIZE

class DocumentHandler:
    EMISSIONS_KEYWORDS = [
        'scope 1', 'scope 2', 'ghg emissions', 'co2',
        'greenhouse gas', 'carbon emissions', 'carbon footprint',
        'direct emissions', 'indirect emissions',
        'metric tons co2e', 'tonnes co2e', 'emissions summary',
        'climate data', 'environmental metrics'
    ]

    # Patterns to identify tables or numeric data that might appear in tabular form.
    TABLE_PATTERNS = [
        r'[\|\t].+[\|\t].+\n',    # Pipes or tabs
        r'\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:tons?|tonnes|mt|co2)',  # Numeric units
        r'(?i)scope\s*[12].*?\d', # Lines containing scope references and numbers
        r'\b20[12]\d\b.*?\d',     # Year followed by numbers
    ]

    @staticmethod
    def extract_text_from_pdf(url: str, retries: int = 3) -> Optional[str]:
        """Extract text from a PDF URL with retries, focusing on relevant emissions data."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for attempt in range(retries):
            try:
                response = requests.get(url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()

                content_length = int(response.headers.get('content-length', 0))
                if content_length > MAX_PDF_SIZE:
                    logging.warning(f"PDF too large: {content_length} bytes")
                    return None

                pdf_content = bytearray()
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        pdf_content.extend(chunk)

                pdf_file = io.BytesIO(pdf_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)

                text_content = []
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        raw_text = page.extract_text()
                        if raw_text and DocumentHandler._has_emissions_data(raw_text):
                            processed_text = DocumentHandler._process_table_text(raw_text)
                            marked_text = f"=== START PAGE {page_num + 1} ===\n{processed_text}\n=== END PAGE {page_num + 1} ==="
                            text_content.append(marked_text)
                        else:
                            # Even if page isn't rich in emissions data, still keep it:
                            # Claude might cross-reference sections.
                            text_content.append(raw_text if raw_text else "")
                    except Exception as e:
                        logging.warning(f"Page {page_num + 1} extraction failed: {str(e)}")
                        continue

                if not text_content:
                    logging.warning("No text content extracted from PDF")
                    return None

                return "\n".join(text_content)

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    # Try alternative URLs if access is denied
                    alt_urls = DocumentHandler._get_alternative_urls(url)
                    for alt_url in alt_urls:
                        try:
                            return DocumentHandler.extract_text_from_pdf(alt_url, retries=1)
                        except:
                            continue
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                continue

        return None

    @staticmethod
    def _has_emissions_data(text: str) -> bool:
        """Check if text contains potential emissions data."""
        text_lower = text.lower()
        keyword_matches = sum(1 for kw in DocumentHandler.EMISSIONS_KEYWORDS if kw in text_lower)

        has_table = any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in DocumentHandler.TABLE_PATTERNS)
        # Look for numbers that could represent emissions. Relaxed criteria, just identify the presence of large numbers.
        number_matches = re.findall(r'\b\d{3,7}(?:\.\d+)?\b', text)
        valid_numbers = [float(n.replace(',', '')) for n in number_matches if 100 <= float(n.replace(',', '')) <= 10_000_000]

        # Additional check for years to ensure we have temporal data
        has_years = bool(re.search(r'\b20[12]\d\b', text))

        # More lenient conditions: If we have at least two keywords or at least one keyword plus a table pattern or numeric data, consider relevant.
        return (keyword_matches >= 2) or (keyword_matches >= 1 and (has_table or has_years or len(valid_numbers) > 0))

    @staticmethod
    def _process_table_text(text: str) -> str:
        """Process and preserve structure for text containing tables."""
        lines = text.split('\n')
        processed_lines = []
        in_table = False

        for line in lines:
            line = line.rstrip()
            if not line:
                # Blank line likely ends a table section
                in_table = False
                continue

            # Check if this line looks like part of a table or numeric data line
            if any(re.search(pattern, line, flags=re.IGNORECASE) for pattern in DocumentHandler.TABLE_PATTERNS):
                in_table = True

            if in_table:
                # Keep table-like structure as is
                processed_lines.append(line)
            else:
                # For non-table lines, strip multiple spaces but keep the line content
                processed_lines.append(' '.join(line.split()))

        return '\n'.join(processed_lines)

    @staticmethod
    def _get_alternative_urls(url: str) -> List[str]:
        """Generate alternative URLs to try if direct access fails."""
        alternatives = [
            f"https://web.archive.org/web/2024/{url}"
        ]
        if "images." in url:
            alternatives.append(url.replace("images.", "www."))

        base_url = url.rsplit('/', 1)[0]
        filename = url.rsplit('/', 1)[1]
        alternatives.extend([
            urljoin(base_url + '/documents/', filename),
            urljoin(base_url + '/downloads/', filename),
            urljoin(base_url + '/pdfs/', filename),
            urljoin(base_url + '/reports/', filename)
        ])

        return alternatives

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
