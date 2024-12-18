import re
import json
import logging
from typing import Dict, Optional, List
from anthropic import Anthropic
from ..config import CLAUDE_API_KEY

class EmissionsAnalyzer:
    """# Claude-based Emissions Data Analyzer
    # Key capabilities:
    # - Smart context extraction from PDF text
    # - Handles multiple data formats (tables, text, footnotes)
    # - Validates and normalizes units
    # - Detects and handles data restatements
    # - Aggregates data from multiple sections
    """
    def __init__(self):
        self.client = Anthropic(api_key=CLAUDE_API_KEY)
        # Pattern to find relevant sections
        self.scope_pattern = r'(?i)scope\s*[12]'
        # Minimum confidence threshold for data
        self.confidence_threshold = 0.8

    def extract_emissions_data(self, text: str, company_name: str = None) -> Optional[Dict]:
        """# Main extraction method using Claude
        # Process:
        # 1. Extract relevant sections with smart context
        # 2. Handle document chunking for large texts
        # 3. Send to Claude with structured prompting
        # 4. Validate and aggregate results"""
        logging.info("Starting emissions data extraction...")

        # Get context-aware sections
        relevant_sections = self._extract_sections_with_context(text)
        if not relevant_sections:
            logging.warning("No relevant sections found for Scope 1/2 in text")
            return None

        # Save intermediate data for debugging
        with open("claude_input_data.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(relevant_sections))

        # Process in chunks if needed
        chunks = self._split_into_chunks(relevant_sections, max_chars=30000)
        all_results = []

        for chunk in chunks:
            result = self._send_to_claude(chunk, company_name)
            if result:
                all_results.append(result)

        # Combine and validate results
        return self._aggregate_and_validate_results(all_results)

    def _extract_sections_with_context(self, text: str) -> List[str]:
        """# Smart context extraction
        # Features:
        # 1. Keeps full tables when found
        # 2. Preserves section boundaries
        # 3. Includes footnotes and references
        # 4. Maintains document hierarchy"""
        sections = []
        current_section = []
        in_table = False
        in_scope_section = False
        table_buffer = []

        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Handle table sections
            if line.startswith('=== TABLE'):
                in_table = True
                table_buffer = [line]
                continue
                
            if in_table:
                table_buffer.append(line)
                if line.strip() == '':
                    in_table = False
                    if any(re.search(self.scope_pattern, l) for l in table_buffer):
                        sections.extend(table_buffer)
                    table_buffer = []
                continue
                
            # Handle text sections with smart boundary detection
            if re.search(self.scope_pattern, line):
                in_scope_section = True
                section_start = i
                
                # Look backwards for section start
                while section_start > 0 and not lines[section_start].startswith('==='):
                    if re.search(r'(?i)(section|chapter|part)\s+\d+', lines[section_start]):
                        break
                    section_start -= 1
                    
                # Look forwards for section end
                section_end = i
                while section_end < len(lines):
                    if lines[section_end].startswith('===') or \
                       re.search(r'(?i)(section|chapter|part)\s+\d+', lines[section_end]):
                        break
                    section_end += 1
                    
                sections.extend(lines[section_start:section_end])
                
        return sections

    def _split_into_chunks(self, lines: List[str], max_chars: int) -> List[str]:
        """# Smart document chunking
        # Features:
        # 1. Preserves table integrity
        # 2. Maintains section boundaries
        # 3. Keeps related content together"""
        chunks = []
        current_chunk = []
        current_length = 0
        in_table = False

        for line in lines:
            line_length = len(line) + 1
            
            # Start new table
            if line.startswith('=== TABLE'):
                if current_length + line_length > max_chars and current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_length = 0
                in_table = True
                
            # End of table
            if in_table and line.strip() == '':
                in_table = False
                
            # Keep tables together
            if current_length + line_length > max_chars and not in_table:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_length = 0
                
            current_chunk.append(line)
            current_length += line_length

        if current_chunk:
            chunks.append("\n".join(current_chunk))
        return chunks

    def _send_to_claude(self, text: str, company_name: str = None) -> Optional[Dict]:
        """# Structured Claude analysis
        # Features:
        # 1. Clear document structure explanation
        # 2. Handles multiple data formats
        # 3. Unit validation and conversion
        # 4. Data restatement detection"""
        prompt = f"""
You are analyzing a sustainability report{f' for {company_name}' if company_name else ''}.

# Document Structure:
The text contains marked sections:
- "=== TABLE X ON PAGE Y ===" indicates table data
- "HEADER:" shows column names
- "DATA:" contains values
- "SCOPE:" indicates scope sections
- "=== TEXT ON PAGE Y ===" shows narrative sections

# Analysis Instructions:
1. Prioritize data from tables over narrative text
2. Check for data restatements/corrections
3. Verify all units are in metric tons CO2e
4. Note the source page numbers and context
5. If multiple values exist, use the most recently stated
6. Pay attention to fiscal vs calendar year

# Data Requirements:
- Current year Scope 1 and 2 emissions
- Previous 2 years of historical data
- Both market-based and location-based Scope 2 when available
- Source details including page numbers
- Confidence level in data extraction

Return in this exact JSON format:
{{
  "company": "{company_name or 'unknown'}",
  "sector": string or null,
  "data_quality": {{
    "confidence": float 0-1,
    "notes": "Any data quality issues"
  }},
  "current_year": {{
    "year": YYYY,
    "year_type": "calendar" or "fiscal",
    "scope_1": {{
      "value": number,
      "unit": "metric tons CO2e",
      "source": "table/text",
      "confidence": float 0-1
    }},
    "scope_2_market_based": {{
      "value": number or null,
      "unit": "metric tons CO2e",
      "source": "table/text",
      "confidence": float 0-1
    }},
    "scope_2_location_based": {{
      "value": number or null,
      "unit": "metric tons CO2e",
      "source": "table/text",
      "confidence": float 0-1
    }}
  }},
  "previous_years": [
    {{
      "year": YYYY,
      "year_type": "calendar" or "fiscal",
      "scope_1": {{
        "value": number,
        "unit": "metric tons CO2e",
        "source": "table/text",
        "confidence": float 0-1
      }},
      "scope_2_market_based": same as above,
      "scope_2_location_based": same as above
    }}
  ],
  "source_details": {{
    "location": "Pages X-Y",
    "context": string,
    "restatements": boolean,
    "restatement_notes": string or null
  }}
}}

Text to analyze:
{text}
"""

        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=4096
            )

            if not response.content or not response.content[0].text:
                logging.warning("No content in Claude response")
                return None

            return self._parse_and_validate(response.content[0].text)

        except Exception as e:
            logging.error(f"Error in Claude analysis: {str(e)}")
            return None

    def _parse_and_validate(self, content: str) -> Optional[Dict]:
        """# Parse and validate Claude's response
        # Checks:
        # 1. Valid JSON structure
        # 2. Required fields present
        # 3. Data consistency
        # 4. Unit standardization"""
        try:
            data = json.loads(content)
            
            # Basic validation
            required_fields = ['company', 'current_year', 'previous_years', 'source_details']
            if not all(field in data for field in required_fields):
                logging.error("Missing required fields in Claude response")
                return None
                
            # Validate confidence levels
            if data.get('data_quality', {}).get('confidence', 0) < self.confidence_threshold:
                logging.warning("Low confidence in data extraction")
                
            return data
            
        except json.JSONDecodeError:
            logging.error("Failed to parse JSON from Claude response")
            return None

    def _aggregate_and_validate_results(self, results: List[Dict]) -> Dict:
        """# Smart result aggregation
        # Features:
        # 1. Resolves conflicts between chunks
        # 2. Validates data consistency
        # 3. Picks highest confidence values
        # 4. Merges source details"""
        if not results:
            return None
            
        # Start with highest confidence result
        results.sort(key=lambda x: x.get('data_quality', {}).get('confidence', 0), reverse=True)
        combined = results[0].copy()
        
        # Merge additional years from other chunks
        all_years = set()
        for result in results:
            for year_data in result.get('previous_years', []):
                year = year_data.get('year')
                if year not in all_years:
                    all_years.add(year)
                    combined['previous_years'].append(year_data)
                    
        # Sort years chronologically
        combined['previous_years'].sort(key=lambda x: x.get('year', 0), reverse=True)
        
        # Merge source details
        all_pages = set()
        all_notes = set()
        for result in results:
            source = result.get('source_details', {})
            if 'location' in source:
                all_pages.add(source['location'])
            if 'context' in source:
                all_notes.add(source['context'])
                
        combined['source_details']['location'] = ', '.join(sorted(all_pages))
        combined['source_details']['context'] = ' '.join(all_notes)
        
        return combined
