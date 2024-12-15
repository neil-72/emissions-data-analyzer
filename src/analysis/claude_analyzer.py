import re
import json
import logging
from typing import Dict, Optional
from anthropic import Anthropic
from ..config import CLAUDE_API_KEY


class EmissionsAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=CLAUDE_API_KEY)

        # Sections that might contain relevant data
        self.target_sections = [
            "Greenhouse Gas Emissions", "Climate Change", "Environmental Data",
            "Scope 1", "Scope 2", "Scope 3", "Scope 1 and 2", "Direct emissions",
            "Indirect emissions", "Carbon Footprint", "Carbon removals", "Corporate Emissions",
            "Location-based emissions", "Market-based emissions", "GHG emissions intensity",
            "Subtotal emissions", "Total net carbon footprint", "Product Life Cycle Emissions",
            "Purchased goods and services", "Upstream impacts", "Assessment of progress",
            "Climate and Efficiency", "Environmental Performance", "ESG Metrics"
        ]

        # Keywords to detect emissions-related tables
        self.table_keywords = [
            "Emissions Data", "GHG Data", "Scope 1", "Scope 2", "Scope 3",
            "Market-based emissions", "Location-based emissions", "Environmental Performance",
            "Metrics and Targets", "Climate Data", "Direct emissions", "Indirect emissions",
            "Subtotal emissions", "Total emissions", "Business travel", "Employee commuting",
            "Energy consumption", "Assessment of progress", "Total carbon emissions"
        ]

    def extract_emissions_data(self, text: str) -> Optional[Dict]:
        """Extract emissions data using Claude with strict formatting rules."""
        logging.info("Starting emissions data extraction...")

        sections = self._extract_relevant_sections(text)
        if not sections.strip():
            logging.info("No prioritized sections found, using entire text as fallback.")
            sections = text[:100000]  # Limit to 100k chars if extremely large

        # System instructions to ensure only JSON is returned
        system_instructions = (
            "You are an assistant that returns ONLY valid JSON with NO extra text. "
            "If you cannot find any Scope 1 or Scope 2 GHG emissions data, you must return the JSON with null values. "
            "No explanations, no formatting outside of the JSON."
        )

        # User prompt to Claude
        prompt = f"""
You are analyzing a corporate sustainability report to find ONLY Scope 1 and Scope 2 greenhouse gas (GHG) emissions data.

**Instructions:**
- Return ONLY a JSON object and NOTHING else.
- The ONLY keys allowed are: "scope_1", "scope_2", and "source_location".
- If no data is found, return null values for both scopes and "source_location": "Not found".
- The JSON must have this exact format:

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
  "source_location": "Short description or page numbers or 'Not found' if not available"
}}

**Additional rules:**
- Do not return any fields other than scope_1, scope_2, and source_location.
- If multiple years are available, choose the most recent.
- Units must always be "metric tons CO2e".
- If the year is not clearly stated, return null for the year.
- If values are not clearly stated for a scope, return null for that scope.

Analyze the following text for Scope 1 and Scope 2 GHG emissions data:

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
                data = self._parse_and_clean_json(content)
                if data is not None:
                    return self._normalize_and_validate(data)
                else:
                    logging.warning("No valid JSON or unexpected data format received from Claude.")
                    return None
            else:
                logging.warning("No content in Claude response")
                return None

        except Exception as e:
            logging.error(f"Error in Claude analysis: {str(e)}")
            return None

    def _extract_relevant_sections(self, text: str, page_threshold: int = 20) -> str:
        """
        Attempts to extract relevant sections. We prioritize:
        1. Emissions-related tables
        2. Chunks mentioning target keywords and scope numbers
        """
        # Find tables first
        table_matches = re.finditer(r'===.*?TABLE.*?===.*?(?====|\Z)', text, re.DOTALL)
        relevant_tables = []
        for match in table_matches:
            table_text = match.group(0)
            if any(kw.lower() in table_text.lower() for kw in self.table_keywords):
                relevant_tables.append(table_text)
        if relevant_tables:
            return '\n\n'.join(relevant_tables)

        # If no tables found, look for text chunks with relevant keywords
        chunks = text.split('===')
        relevant_chunks = []
        for chunk in chunks:
            if any(kw.lower() in chunk.lower() for kw in self.target_sections):
                # Check for mention of scope 1 or scope 2 with numbers
                if re.search(r'(?i)scope\s*[12].*?\d', chunk):
                    relevant_chunks.append(chunk)
        if relevant_chunks:
            return '=== '.join(relevant_chunks)

        # Fallback: return first 100k of text
        return text[:100000]

    def _parse_and_clean_json(self, content: str) -> Optional[Dict]:
        """Parse the JSON and remove any extraneous keys."""
        # Attempt direct JSON parse
        data = self._parse_json_response(content)
        if data is None:
            # Attempt regex extraction if Claude included extra text
            json_match = re.search(r'(\{.*"scope_1".*"scope_2".*?\})', content, re.DOTALL)
            if json_match:
                data_str = json_match.group(1)
                data = self._parse_json_response(data_str)

        # Clean to only allowed keys
        if data:
            allowed_keys = {"scope_1", "scope_2", "source_location"}
            cleaned_data = {k: v for k, v in data.items() if k in allowed_keys}
            # Ensure all required keys exist
            for required_key in ["scope_1", "scope_2", "source_location"]:
                if required_key not in cleaned_data:
                    cleaned_data[required_key] = None
            return cleaned_data
        return None

    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Attempt to parse a string as JSON."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logging.error("Failed to parse JSON data from Claude response")
            return None

    def _normalize_and_validate(self, data: Dict) -> Dict:
        """
        Ensure data matches the required schema exactly:
        {
          "scope_1": {
            "value": <float or null>,
            "unit": "metric tons CO2e",
            "year": <int or null>
          },
          "scope_2": {
            "value": <float or null>,
            "unit": "metric tons CO2e",
            "year": <int or null>
          },
          "source_location": <str or "Not found">
        }
        """
        for scope in ["scope_1", "scope_2"]:
            scope_data = data.get(scope)
            if not isinstance(scope_data, dict):
                # If no valid data, set default null values
                data[scope] = {
                    "value": None,
                    "unit": "metric tons CO2e",
                    "year": None
                }
                continue

            # Normalize value
            val = scope_data.get("value")
            try:
                val = float(str(val).replace(',', '')) if val is not None else None
            except (ValueError, TypeError):
                val = None

            # Normalize unit
            unit = "metric tons CO2e"

            # Normalize year
            year = scope_data.get("year")
            try:
                year_int = int(year)
                if year_int < 2000 or year_int > 2100:
                    year_int = None
            except (ValueError, TypeError):
                year_int = None

            data[scope] = {
                "value": val,
                "unit": unit,
                "year": year_int
            }

        # Ensure source_location is a string or default "Not found"
        source_location = data.get("source_location")
        if not isinstance(source_location, str) or not source_location.strip():
            source_location = "Not found"
        data["source_location"] = source_location

        return data
