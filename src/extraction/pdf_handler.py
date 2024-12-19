from parsestudio.parse import PDFParser
import requests
import tempfile
import os
from typing import Optional, Dict, List
import logging
import re
from ..config import MAX_PDF_SIZE

class EnhancedDocumentHandler:
    """PDF Document Handler using ParseStudio for Emissions Data Extraction
    Maintains similar functionality to original but with improved parsing
    """
    def __init__(self):
        # Initialize ParseStudio with Docling backend
        # Use OCR and accurate table detection
        self.parser = PDFParser(
            parser="docling",
            parser_kwargs={
                "pipeline_options": {
                    "do_ocr": True,
                    "do_table_structure": True,
                    "table_structure_options": {
                        "do_cell_matching": True,
                        "mode": "ACCURATE"
                    }
                }
            }
        )

        # Same patterns as your original implementation
        self.data_patterns = [
            r'(?i)scope\s*[123]',     
            r'(?i)emissions',          
            r'(?i)fy\d{2}',           
            r'(?i)(19|20)\d{2}',      
            r'(?i)mtco2e?'            
        ]

    def get_document_content(self, url: str) -> Optional[str]:
        """Main method to download and process PDF
        1. Downloads PDF to temp file
        2. Validates content type
        3. Processes with ParseStudio
        4. Combines relevant content
        """
        try:
            # Download PDF
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

            # Save to temp file (ParseStudio needs file path)
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf.write(response.content)
                temp_path = temp_pdf.name

            try:
                # Parse PDF with ParseStudio
                outputs = self.parser.run(
                    temp_path, 
                    modalities=["text", "tables"]
                )

                if not outputs:
                    return None

                # Process first document
                extracted_content = self._process_document(outputs[0])

                # Save raw extraction for debugging like original
                if extracted_content:
                    with open("raw_extracted_data.txt", "w", encoding="utf-8") as f:
                        f.write(extracted_content)

                return extracted_content

            finally:
                # Clean up temp file
                os.unlink(temp_path)

        except Exception as e:
            logging.error(f"Failed to get document: {str(e)}")
            return None

    def _process_document(self, doc_output) -> Optional[str]:
        """Process ParseStudio output maintaining original structure
        1. Identifies relevant pages
        2. Processes tables and text
        3. Maintains formatting and markers
        """
        try:
            extracted_content = []
            
            # Get full text to identify relevant pages
            full_text = doc_output.text.text
            
            # Split into pages (assuming page markers in text)
            pages = self._split_into_pages(full_text)
            
            # Find relevant pages
            for page_num, page_text in enumerate(pages, 1):
                if not any(re.search(pattern, page_text) for pattern in self.data_patterns):
                    continue
                    
                # Process tables on this page
                relevant_tables = [
                    table for table in doc_output.tables
                    if table.metadata.page_number == page_num
                ]
                
                for table_num, table in enumerate(relevant_tables, 1):
                    processed_table = self._process_table(table)
                    if processed_table:
                        extracted_content.append(
                            f"=== TABLE {table_num} ON PAGE {page_num} ===\n{processed_table}\n"
                        )

                # Process text
                processed_text = self._process_text(page_text)
                if processed_text:
                    extracted_content.append(
                        f"=== TEXT ON PAGE {page_num} ===\n{processed_text}\n"
                    )

            return "\n".join(extracted_content) if extracted_content else None

        except Exception as e:
            logging.error(f"Processing error: {str(e)}")
            return None

    def _split_into_pages(self, text: str) -> List[str]:
        """Split full text into pages based on markers"""
        # You might need to adjust this based on how ParseStudio formats the text
        pages = []
        current_page = []
        
        for line in text.split('\n'):
            if re.match(r'={3,}\s*PAGE\s+\d+\s*={3,}', line):
                if current_page:
                    pages.append('\n'.join(current_page))
                current_page = []
            else:
                current_page.append(line)
                
        if current_page:
            pages.append('\n'.join(current_page))
            
        return pages or [text]  # Return original text if no page markers

    def _process_table(self, table) -> Optional[str]:
        """Process ParseStudio table maintaining original structure"""
        if not table or not table.dataframe.empty:
            return None

        formatted_rows = []
        df = table.dataframe
        
        # Handle header
        header_row = list(df.columns)
        if header_row:
            formatted_rows.append("HEADER: " + " | ".join(str(col).strip() for col in header_row))

        # Process data rows
        current_scope = None
        for _, row in df.iterrows():
            row_text = " | ".join(str(cell).strip() for cell in row if str(cell).strip())
            if not row_text:
                continue

            # Check for scope headers
            scope_match = None
            for cell in row:
                if isinstance(cell, str) and re.search(r'(?i)scope\s*[123]', cell):
                    scope_match = cell
                    break

            if scope_match:
                current_scope = scope_match
                formatted_rows.append(f"SCOPE: {row_text}")
                continue

            # Handle data rows with indentation
            if current_scope:
                first_cell = str(row.iloc[0])
                leading_spaces = len(first_cell) - len(first_cell.lstrip())
                indent_level = leading_spaces // 2

                row_type = "TOTAL" if any(t in row_text.lower() for t in ['total', 'subtotal']) else "DATA"
                formatted_rows.append(f"{'  ' * indent_level}{row_type}: {row_text}")
            else:
                formatted_rows.append(f"DATA: {row_text}")

        return "\n".join(formatted_rows) if formatted_rows else None

    def _process_text(self, text: str) -> Optional[str]:
        """Process text maintaining original structure and markers"""
        if not text:
            return None

        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Tag important lines (same as original)
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
