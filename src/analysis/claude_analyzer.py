import re
import json
import logging
from typing import Dict, Optional
from anthropic import Anthropic
from ..config import CLAUDE_API_KEY


class EmissionsAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=CLAUDE_API_KEY)

        # Comprehensive target sections and table keywords
        self.target_sections = [
            "Greenhouse Gas Emissions", "Climate Change", "Environmental Data",
            "Scope 1", "Scope 2", "Scope 3", "Scope 1 and 2", "Direct emissions",
            "Indirect emissions", "Carbon Footprint", "Carbon removals", "Corporate Emissions",
            "Location-based emissions", "Market-based emissions", "GHG emissions intensity",
            "Subtotal emissions", "Total net carbon footprint", "Product Life Cycle Emissions",
            "Purchased goods and services", "Upstream impacts", "Assessment of progress",
            "Climate and Efficiency", "Environmental Performance", "ESG Metrics"
        ]

        self.table_keywords = [
            "Emissions Data", "GHG Data", "Scope 1", "Scope 2", "Scope 3",
            "Market-based emissions", "Location-based emissions", "Environmental Performance",
            "Metrics and Targets", "Climate Data", "Direct emissions", "Indirect emissions",
            "Subtotal emissions", "Total emissions", "Business travel", "Employee commuting",
            "Energy consumption", "Assessment of progress", "Total carbon emissions"
        ]

    def extract_emissions_data(self, text: str) -> Optional[Dict]:
        """Extract emissions data using Claude with better error handling."""
        logging.info("Starting emissions data extraction...")

        # Extract the most relevant sections, focusing on tables first
        sections = self._extract_relevant_sections(text)
        if not sections.strip():
            logging.info("No relevant sections found, using the full text as a fallback.")
            sections = text

        # Instructions to Claude
        system_instructions = (
            "You are an assistant that ONLY returns valid JSON with no extra text. "
            "If you cannot find any relevant data, return the specified JSON with null values. "
            "No explanations, no additional formatting, no text outside the JSON."
        )

        # A more explicit and controlled prompt
        prompt = f"""
You are analyzing a corporate sustainability report to find greenhouse gas (GHG) emissions data, specifically Scope 1 and Scope 2.

Please follow these instructions carefully:
- Return ONLY a JSON object and NOTHING else.
- The JSON should have this format:

{{
  "scope_1": {{
    "value": <number or null>,
    "unit": "metric tons CO2e",
    "year": <YYYY or null>
  }},
  "scope_2": {{
    "value": <number or null>,
    "unit": "metric tons CO2e",
    "year": <YYYY or null>
  }},
  "source_location": "Short description of where data was found (page numbers if available)"
}}

Notes:
- If multiple years are available, return data for the most recent year you find.
- If units are not in metric tons CO2e, just return the unit as 'metric tons CO2e'.
- If scope data is not explicitly labeled as "Scope 1" or "Scope 2", infer from context.
- No extra commentary outside the JSON.

Text to analyze:
{sections}
""".strip()

        try:
            logging.info("Sending request to Claude...")
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                system=system_instructions,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=4000
            )

            if response.content and response.content[0].text:
                content = response.content[0].text
                logging.info("Response received from Claude")

                # Try to parse the response as JSON
                data = self._parse_json_response(content)
                if data is None:
                    # Attempt regex extraction of JSON portion if Claude returned extra text
                    json_match = re.search(r'(\{.*"scope_1".*"scope_2".*?\})', content, re.DOTALL)
                    if json_match:
                        data_str = json_match.group(1)
                        data = self._parse_json_response(data_str)

                if data:
                    return self._normalize_and_validate(data)
                else:
                    logging.warning("Could not parse emissions data from Claude's response.")
                    return None
            else:
                logging.warning("No content in Claude response")
                return None

        except Exception as e:
            logging.error(f"Error in Claude analysis: {str(e)}")
            return None

    def _extract_relevant_sections(self, text: str, page_threshold: int = 20) -> str:
        """Extract relevant sections, with better handling of large documents."""

        # First, try to find emissions-related tables
        table_matches = re.finditer(r'===.*?TABLE.*?===.*?(?====|\Z)', text, re.DOTALL)
        relevant_tables = []
        for match in table_matches:
            table_text = match.group(0)
            if any(kw.lower() in table_text.lower() for kw in self.table_keywords):
                relevant_tables.append(table_text)

        # If we found relevant tables, return them directly
        if relevant_tables:
            return '\n\n'.join(relevant_tables)

        # Otherwise, we fall back to text searches
        chunks = text.split('===')
        relevant_chunks = []
        for chunk in chunks:
            # Check if the chunk contains any target sections and has scope + numbers
            if any(kw.lower() in chunk.lower() for kw in self.target_sections):
                if re.search(r'(?i)scope\s*[12].*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', chunk):
                    relevant_chunks.append(chunk)

        # Return joined relevant chunks or truncate if none
        return '=== '.join(relevant_chunks) if relevant_chunks else text[:100000]

    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Parse Claude's response as JSON."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logging.error("Failed to parse JSON data from Claude response")
            return None

    def _normalize_and_validate(self, data: Dict) -> Dict:
        """Normalize and validate the emissions data."""
        for scope in ["scope_1", "scope_2"]:
            if scope in data:
                scope_data = data[scope]
                if not isinstance(scope_data, dict):
                    continue

                # Handle value
                try:
                    raw_value = str(scope_data.get("value", "0"))
                    value = float(raw_value.replace(',', '').strip())
                    scope_data["value"] = value
                except (ValueError, TypeError):
                    scope_data["value"] = None

                # Set unit to metric tons CO2e
                scope_data["unit"] = "metric tons CO2e"

                # Handle year safely
                try:
                    year = scope_data.get("year")
                    if year and isinstance(year, (int, float)) and 2000 <= int(year) <= 2100:
                        scope_data["year"] = int(year)
                    else:
                        scope_data["year"] = None
                except (ValueError, TypeError):
                    scope_data["year"] = None

        return data
