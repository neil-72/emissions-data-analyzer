import re
import json
import logging
from typing import Dict, Optional, List
from anthropic import Anthropic
from ..config import CLAUDE_API_KEY

class EmissionsAnalyzer:
    """# Main Emissions Data Analyzer using Claude
    # Key capabilities:
    # - Processes sustainability report text from PDFs
    # - Identifies and extracts Scope 1 and 2 emissions data
    # - Handles both tabular and narrative text formats
    # - Maintains data context and page references
    # - Aggregates data across multiple years
    """
    def __init__(self):
        self.client = Anthropic(api_key=CLAUDE_API_KEY)
        # Simple regex works best for finding emissions data
        self.scope_pattern = r'(?i)scope\s*[12]'

    def extract_emissions_data(self, text: str, company_name: str = None) -> Optional[Dict]:
        """# Main extraction pipeline
        # Process:
        # 1. Find relevant sections containing emissions data
        # 2. Keep context (15 lines before/after)
        # 3. Remove duplicate content
        # 4. Split into chunks if text is too long
        # 5. Send each chunk to Claude
        # 6. Combine and validate results
        """
        logging.info("Starting emissions data extraction...")

        # Get relevant text with context
        relevant_lines = self._extract_lines_with_context(text, lines_before=15, lines_after=15)
        relevant_lines = list(dict.fromkeys(relevant_lines))  # Remove duplicates

        if not relevant_lines:
            logging.warning("No relevant context found for Scope 1/2 in text")
            return None

        # Save for debugging and verification
        with open("claude_input_data.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(relevant_lines))

        # Handle large documents via chunking
        chunks = self._split_into_chunks(relevant_lines, max_chars=30000)
        all_results = []

        # Process each chunk
        for chunk in chunks:
            result = self._send_to_claude(chunk, company_name)
            if result:
                all_results.append(result)

        # Combine results intelligently
        return self._aggregate_results(all_results)

    def _extract_lines_with_context(self, text: str, lines_before: int, lines_after: int) -> List[str]:
        """# Smart context extraction
        # Features:
        # - Finds emissions data mentions
        # - Keeps surrounding lines for context
        # - Preserves table structures when found
        # - Handles page boundaries
        # - Maintains document formatting
        """
        lines = text.split('\n')
        relevant_lines = []
        for i, line in enumerate(lines):
            if re.search(self.scope_pattern, line):
                start = max(0, i - lines_before)
                end = min(len(lines), i + lines_after + 1)
                
                # Keep full tables when found
                if any(lines[j].startswith('=== TABLE') for j in range(start, end)):
                    while start > 0 and not lines[start].startswith('=== TABLE'):
                        start -= 1
                
                relevant_lines.extend(lines[start:end])
        return relevant_lines

    def _split_into_chunks(self, lines: List[str], max_chars: int) -> List[str]:
        """# Smart document chunking
        # Features:
        # - Respects maximum token limits
        # - Preserves table integrity
        # - Keeps related content together
        # - Maintains section boundaries
        # - Avoids splitting mid-context
        """
        chunks = []
        current_chunk = []
        current_length = 0

        for line in lines:
            line_length = len(line) + 1  # Include newline
            
            # Start new chunk if needed
            if current_length + line_length > max_chars:
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_length = 0
            
            # Keep tables together
            if line.startswith('=== TABLE'):
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_length = 0

            current_chunk.append(line)
            current_length += line_length

        if current_chunk:
            chunks.append("\n".join(current_chunk))
        return chunks

    def _send_to_claude(self, text: str, company_name: str = None) -> Optional[Dict]:
        """# Claude analysis with structured format
        # Features:
        # - Clear document format explanation
        # - Specific data requirements
        # - Consistent JSON structure
        # - Unit standardization
        # - Clean output format
        """
        prompt = f"""
Analyze this sustainability report{f' for {company_name}' if company_name else ''}.

The text contains marked sections:
- "=== TABLE X ON PAGE Y ===" indicates table data
- "HEADER:" shows column names
- "DATA:" contains values
- "=== TEXT ON PAGE Y ===" shows narrative sections

Focus on:
1. Extract Scope 1 and Scope 2 emissions values
2. Get both market-based and location-based Scope 2 when available
3. Include current year and up to 2 previous years
4. Note page numbers where data was found
5. All values should be in metric tons CO2e

Return exactly this JSON format:
{{
  "company": "{company_name or 'unknown'}",
  "sector": string or null,
  "current_year": {{
    "year": YYYY,
    "scope_1": {{
      "value": number,
      "unit": "metric tons CO2e"
    }},
    "scope_2_market_based": {{
      "value": number or null,
      "unit": "metric tons CO2e"
    }},
    "scope_2_location_based": {{
      "value": number or null,
      "unit": "metric tons CO2e"
    }}
  }},
  "previous_years": [
    {{
      "year": YYYY,
      "scope_1": {{
        "value": number,
        "unit": "metric tons CO2e"
      }},
      "scope_2_market_based": {{
        "value": number or null,
        "unit": "metric tons CO2e"
      }},
      "scope_2_location_based": {{
        "value": number or null,
        "unit": "metric tons CO2e"
      }}
    }}
  ],
  "source_details": {{
    "location": "Pages X-Y",
    "context": "Brief description of where data was found"
  }}
}}

Text to analyze:
{text}
"""

        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",  # Latest stable model
                messages=[{"role": "user", "content": prompt}],
                temperature=0,  # Deterministic output
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
        """# Response validation
        # Checks:
        # - Valid JSON structure
        # - Required fields present
        # - Consistent data format
        # - Complete response
        """
        try:
            data = json.loads(content)
            
            # Basic validation
            required_fields = ['company', 'current_year', 'previous_years', 'source_details']
            if not all(field in data for field in required_fields):
                logging.error("Missing required fields in Claude response")
                return None
                
            return data
            
        except json.JSONDecodeError:
            logging.error("Failed to parse JSON from Claude response")
            return None

    def _aggregate_results(self, results: List[Dict]) -> Dict:
        """# Result aggregation
        # Features:
        # - Combines data from multiple chunks
        # - Removes duplicate years
        # - Sorts chronologically
        # - Keeps most recent data
        # - Merges source details
        """
        if not results:
            return None

        # Use first result as base
        combined = results[0].copy()
        seen_years = {combined['current_year']['year']}
        
        # Add unique years from other chunks
        for result in results[1:]:
            # Skip duplicate current years
            if result['current_year']['year'] not in seen_years:
                seen_years.add(result['current_year']['year'])
                combined['previous_years'].append(result['current_year'])
                
            # Add unique previous years
            for year_data in result.get('previous_years', []):
                if year_data['year'] not in seen_years:
                    seen_years.add(year_data['year'])
                    combined['previous_years'].append(year_data)
        
        # Sort previous years newest to oldest
        combined['previous_years'].sort(key=lambda x: x['year'], reverse=True)
        
        # Keep only 2 previous years
        combined['previous_years'] = combined['previous_years'][:2]
        
        return combined
