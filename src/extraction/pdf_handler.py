import pdfplumber
import requests
from typing import Optional, List, Dict
import io
import logging
import re
from ..config import MAX_PDF_SIZE

class DocumentHandler:
    """# PDF Document Handler for Emissions Data Extraction
    # Key capabilities:
    # - Extracts both tables and text from PDFs
    # - Handles multi-column layouts intelligently 
    # - Preserves document structure and formatting
    # - Tags content types (TABLE, TEXT, DATA, HEADER)
    # - Maintains page numbers and section markers
    """
    def __init__(self):
        # Core patterns to identify relevant sections
        self.data_patterns = [
            r'(?i)scope\s*[123]',     # Emissions scope references
            r'(?i)emissions',          # Direct emissions mentions 
            r'(?i)fy\d{2}',           # Fiscal year patterns e.g., FY23
            r'(?i)(19|20)\d{2}',      # Calendar year patterns
            r'(?i)mtco2e?'            # Common unit patterns
        ]
        # Column handling settings
        self.x_tolerance = 3          # Horizontal spacing for word grouping
        self.y_tolerance = 3          # Vertical spacing for line detection

    def get_document_content(self, url: str) -> Optional[str]:
        """# Main method to download and process PDF
        # 1. Downloads PDF with error handling
        # 2. Validates PDF content type
        # 3. Extracts and processes content
        # 4. Saves raw extraction for debugging"""
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

            extracted = self._extract_content(io.BytesIO(response.content))

            # Save raw extraction for debugging
            if extracted:
                with open("raw_extracted_data.txt", "w", encoding="utf-8") as f:
                    f.write(extracted)

            return extracted

        except Exception as e:
            logging.error(f"Failed to get document: {str(e)}")
            return None

    def _extract_content(self, pdf_content: io.BytesIO) -> Optional[str]:
        """# Main content extraction logic
        # Process:
        # 1. First pass identifies relevant pages
        # 2. Extracts tables first (more structured)
        # 3. Then extracts surrounding text
        # 4. Preserves page numbers and content markers"""
        try:
            with pdfplumber.open(pdf_content) as pdf:
                extracted_content = []
                
                # Find pages with relevant content first
                relevant_pages = []
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    if any(re.search(pattern, text) for pattern in self.data_patterns):
                        relevant_pages.append(page_num)

                # Process identified pages
                for page_num in relevant_pages:
                    page = pdf.pages[page_num]
                    
                    # Handle tables first
                    tables = page.extract_tables()
                    for table_num, table in enumerate(tables, 1):
                        if table and len(table) > 1:
                            processed_table = self._process_table(table)
                            if processed_table:
                                extracted_content.append(
                                    f"=== TABLE {table_num} ON PAGE {page_num + 1} ===\n{processed_table}\n"
                                )

                    # Then handle text with column awareness
                    text = self._extract_text_with_columns(page)
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

    def _extract_text_with_columns(self, page) -> str:
        """# Smart multi-column text extraction
        # 1. Gets word positions and coordinates
        # 2. Groups words by vertical position (rows)
        # 3. Orders words within rows by horizontal position
        # 4. Reconstructs proper reading order"""
        def sort_by_position(word):
            return (-word['top'], word['x0'])
        
        try:
            words = page.extract_words(
                x_tolerance=self.x_tolerance,
                y_tolerance=self.y_tolerance
            )
            
            if not words:
                return page.extract_text() or ""
                
            words.sort(key=sort_by_position)
            
            # Group words into lines
            lines = []
            current_line = []
            current_y = None
            
            for word in words:
                if current_y is None:
                    current_y = word['top']
                elif abs(word['top'] - current_y) > self.y_tolerance:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = []
                    current_y = word['top']
                current_line.append(word['text'])
                
            if current_line:
                lines.append(' '.join(current_line))
                
            return '\n'.join(lines)
            
        except Exception as e:
            logging.warning(f"Column extraction failed, falling back to simple extraction: {str(e)}")
            return page.extract_text() or ""

    def _process_table(self, table: List[List]) -> Optional[str]:
        """# Process tables while preserving structure
        # Features:
        # - Identifies headers and scope sections
        # - Tracks indentation for hierarchical data
        # - Labels row types (HEADER, DATA, TOTAL)
        # - Maintains table formatting"""
        if not table:
            return None

        # Track document structure
        current_scope = None
        formatted_rows = []
        header_row = None

        # Handle header row
        if table[0]:
            header_row = [str(cell).strip() for cell in table[0] if cell]
            if header_row:
                formatted_rows.append("HEADER: " + " | ".join(header_row))

        # Process data rows
        for row_idx, row in enumerate(table[1:], 1):
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
                formatted_rows.append(f"SCOPE: {row_text}")
                continue

            # Handle hierarchical data with indentation
            if current_scope:
                first_cell = str(row[0])
                leading_spaces = len(first_cell) - len(first_cell.lstrip())
                indent_level = leading_spaces // 2

                row_type = "TOTAL" if any(t in row_text.lower() for t in ['total', 'subtotal']) else "DATA"
                formatted_rows.append(f"{'  ' * indent_level}{row_type}: {row_text}")
            else:
                formatted_rows.append(f"DATA: {row_text}")

        return "\n".join(formatted_rows) if formatted_rows else None

    def _process_text(self, text: str) -> Optional[str]:
        """# Process text sections with structure
        # Features:
        # - Identifies section headers and data lines
        # - Preserves numerical data context
        # - Maintains paragraph structure
        # - Marks important sections"""
        if not text:
            return None

        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Tag important lines
            if any(re.search(pattern, line) for pattern in self.data_patterns):
                if re.search(r'(?i)(table|figure|notes?|section)', line):
                    processed_lines.append(f"SECTION: {line}")
                elif re.search(r'\d', line):
                    processed_lines.append(f"DATA: {line}")
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)

        return "\n".join(processed_lines) if processed_lines else None
