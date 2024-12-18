import pdfplumber
import requests
from typing import Optional, List, Dict
import io
import logging
import re
from ..config import MAX_PDF_SIZE

class DocumentHandler:
    def __init__(self):
        # Core patterns focused on emissions and financial data
        self.data_patterns = [
            r'(?i)scope\s*[123]',
            r'(?i)emissions',
            r'(?i)fy\d{2}',  # Fiscal year patterns
            r'(?i)(19|20)\d{2}',  # Year patterns
            r'(?i)mtco2e?'  # Common unit patterns
        ]

    def get_document_content(self, url: str) -> Optional[str]:
        """Main method to extract content from PDF."""
        try:
            response = requests.get(
                url,
                headers={'User-Agent': 'Mozilla/5.0'},
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            
            # Basic PDF validation
            if 'application/pdf' not in response.headers.get('content-type', '').lower():
                logging.warning(f"URL {url} does not point to a PDF")
                return None

            return self._extract_content(io.BytesIO(response.content))

        except Exception as e:
            logging.error(f"Failed to get document: {str(e)}")
            return None

    def _extract_content(self, pdf_content: io.BytesIO) -> Optional[str]:
        """Extract text and tables with structure preservation."""
        try:
            with pdfplumber.open(pdf_content) as pdf:
                extracted_content = []
                
                # First pass - identify pages with relevant data
                relevant_pages = []
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    if any(re.search(pattern, text) for pattern in self.data_patterns):
                        relevant_pages.append(page_num)

                # Process relevant pages
                for page_num in relevant_pages:
                    page = pdf.pages[page_num]
                    
                    # Get tables first - they're more structured
                    tables = page.extract_tables()
                    for table_num, table in enumerate(tables, 1):
                        if table and len(table) > 1:  # Has content
                            processed_table = self._process_table(table)
                            if processed_table:
                                extracted_content.append(
                                    f"=== TABLE {table_num} ON PAGE {page_num + 1} ===\n{processed_table}\n"
                                )

                    # Get surrounding text for context
                    text = page.extract_text()
                    if text:
                        context = self._process_text(text)
                        if context:
                            extracted_content.append(
                                f"=== TEXT ON PAGE {page_num + 1} ===\n{context}\n"
                            )

                return "\n".join(extracted_content) if extracted_content else None

        except Exception as e:
            logging.error(f"Extraction error: {str(e)}")
            return None

    def _process_table(self, table: List[List]) -> Optional[str]:
        """Process table with structure preservation."""
        if not table:
            return None

        # Track structure
        current_scope = None
        current_section = None
        formatted_rows = []
        header_row = None

        # Process header row first
        if table[0]:
            header_row = [str(cell).strip() for cell in table[0] if cell]
            if header_row:
                formatted_rows.append("HEADER: " + " | ".join(header_row))

        # Process data rows
        for row_idx, row in enumerate(table[1:], 1):
            # Clean row data
            row_cells = [str(cell).strip() if cell else "" for cell in row]
            row_text = " | ".join(cell for cell in row_cells if cell)
            if not row_text:
                continue

            # Check for scope headers
            scope_match = None
            for cell in row_cells:
                if re.search(r'(?i)scope\s*[123]', cell):
                    scope_match = cell
                    break

            if scope_match:
                current_scope = scope_match
                # Preserve full row as a scope header
                formatted_rows.append(f"SCOPE: {row_text}")
                continue

            # Handle indented sub-items
            if current_scope:
                # Check indentation of first cell
                first_cell = str(row[0])
                leading_spaces = len(first_cell) - len(first_cell.lstrip())
                indent_level = leading_spaces // 2

                # Format with indentation and scope context
                row_type = "TOTAL" if any(t in row_text.lower() for t in ['total', 'subtotal']) else "DATA"
                formatted_rows.append(f"{'  ' * indent_level}{row_type}: {row_text}")
            else:
                # Regular data row
                formatted_rows.append(f"DATA: {row_text}")

        return "\n".join(formatted_rows) if formatted_rows else None

    def _process_text(self, text: str) -> Optional[str]:
        """Process text sections with basic structure."""
        if not text:
            return None

        # Split into lines and clean
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Identify and mark important lines
            if any(re.search(pattern, line) for pattern in self.data_patterns):
                # Check if it's a header-like line
                if re.search(r'(?i)(table|figure|notes?|section)', line):
                    processed_lines.append(f"SECTION: {line}")
                # Check if it contains numeric data
                elif re.search(r'\d', line):
                    processed_lines.append(f"DATA: {line}")
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)

        return "\n".join(processed_lines) if processed_lines else None
