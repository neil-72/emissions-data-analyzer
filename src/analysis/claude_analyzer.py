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
        """Extract emissions data (including previous years and sector) using Claude."""
        logging.info("Starting emissions data extraction...")

        sections = self._extract_relevant_sections(text)
        if not sections.strip():
            logging.info("No prioritized sections found, using entire text as fallback.")
            sections = text[:100000]

        # System instructions: return ONLY the JSON, no extra text
        system_instructions = (
            "You are an assistant that returns ONLY valid JSON with NO extra text. "
            "If you cannot find any Scope 1 or Scope 2 GHG emissions data, you must return the JSON with null values. "
            "If you cannot find previous years data or the sector, return them as null. "
            "No explanations, no formatting outside of the JSON."
        )

        # Updated user prompt to include previous years and sector
        prompt = f"""
You are analyzing a corporate sustainability report. Your goal is to find:
- Scope 1 and Scope 2 greenhouse gas (GHG) emissions data for the reported year.
- Any available previous years’ Scope 1 and Scope 2 data mentioned in the text.
- The company’s sector, if identifiable from the text or the company name.

**Instructions:**
- Return ONLY a JSON object and NOTHING else.
- The ONLY keys allowed are: "scope_1", "scope_2", "source_location", "previous_years_data", "sector".
- "previous_years_data" should be an object mapping years (YYYY) to scope_1 and scope_2 data in the same format as the current year:
    {{
      "YYYY": {{
        "scope_1": {{
          "value": <number or null>,
          "unit": "metric tons CO2e",
          "year": <YYYY or null>
        }},
        "scope_2": {{
          "value": <number or null>,
          "unit": "metric tons CO2e",
          "year": <YYYY or null>
        }}
      }},
      ...
    }}
  If no previous years’ data is found, "previous_years_data" should be null.
- The "sector" should be a string if found, otherwise null.

Your final JSON must have this format:

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
  "source_location": "Short description or page numbers or 'Not found' if not available",
  "previous_years_data": {{
    "<YYYY>": {{
      "scope_1": {{ "value": <number or null>, "unit": "metric tons CO2e", "year": <YYYY or null> }},
      "scope_2": {{ "value": <number or null>, "unit": "metric tons CO2e", "year": <YYYY or null> }}
    }},
    ...
  }} or null,
  "sector": "<sector string or null>"
}}

**Additional rules:**
- If no data is found for current scope_1 or scope_2, return null for those values.
- Units must always be "metric tons CO2e".
- If the year is not clearly stated, return null for that year.
- No extra text outside of this JSON is allowed.

Analyze the following text for Scope 1, Scope 2, previous years data, and sector:

{sections}
""".strip()

        try:
            logging.info("Sending request to Claude...")
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                system=system_instructions,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=6000
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
        # Find tables first
        table_matches = re.finditer(r'===.*?TABLE.*?===.*?(?====|\Z)', text, re.DOTALL)
        relevant_tables = []
        for match in table_matches:
            table_text = match.group(0)
            if any(kw.lower() in table_text.lower() for kw in self.table_keywords):
                relevant_tables.append(table_text)
        if relevant_tables:
            return '\n\n'.join(relevant_tables)

        # If no tables found, look for relevant chunks
        chunks = text.split('===')
        relevant_chunks = []
        for chunk in chunks:
            if any(kw.lower() in chunk.lower() for kw in self.target_sections):
                if re.search(r'(?i)scope\s*[12].*?\d', chunk):
                    relevant_chunks.append(chunk)

        if relevant_chunks:
            return '=== '.join(relevant_chunks)

        # Fallback: return first 100k of text
        return text[:100000]

    def _parse_and_clean_json(self, content: str) -> Optional[Dict]:
        """Parse the JSON and ensure all allowed keys are present."""
        data = self._parse_json_response(content)
        if data is None:
            # Attempt regex extraction if extra text appeared
            json_match = re.search(r'(\{.*"scope_1".*"scope_2".*?"sector".*?\})', content, re.DOTALL)
            if json_match:
                data_str = json_match.group(1)
                data = self._parse_json_response(data_str)

        # Allowed keys now include: scope_1, scope_2, source_location, previous_years_data, sector
        if data:
            allowed_keys = {"scope_1", "scope_2", "source_location", "previous_years_data", "sector"}
            cleaned_data = {k: v for k, v in data.items() if k in allowed_keys}

            # Ensure all required keys
            for required_key in ["scope_1", "scope_2", "source_location", "previous_years_data", "sector"]:
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
        # Normalize scope_1 and scope_2 for current year
        for scope in ["scope_1", "scope_2"]:
            data[scope] = self._normalize_scope_data(data.get(scope))

        # previous_years_data normalization
        previous_data = data.get("previous_years_data")
        if previous_data and isinstance(previous_data, dict):
            normalized_previous = {}
            for year_str, year_data in previous_data.items():
                year = self._safe_int(year_str)
                if not year or year < 2000 or year > 2100:
                    year = None

                norm_scope_1 = self._normalize_scope_data(year_data.get("scope_1"), year)
                norm_scope_2 = self._normalize_scope_data(year_data.get("scope_2"), year)

                normalized_previous[str(year) if year else "unknown_year"] = {
                    "scope_1": norm_scope_1,
                    "scope_2": norm_scope_2
                }
            data["previous_years_data"] = normalized_previous if normalized_previous else None
        else:
            data["previous_years_data"] = None

        # sector normalization
        sector = data.get("sector")
        if not isinstance(sector, str) or not sector.strip():
            data["sector"] = None

        # source_location normalization
        source_location = data.get("source_location")
        if not isinstance(source_location, str) or not source_location.strip():
            data["source_location"] = "Not found"

        return data

    def _normalize_scope_data(self, scope_data: Optional[Dict], year: Optional[int] = None) -> Dict:
        """Normalize a single scope (scope_1 or scope_2) data dictionary."""
        if not isinstance(scope_data, dict):
            return {
                "value": None,
                "unit": "metric tons CO2e",
                "year": year if year else None
            }

        val = scope_data.get("value")
        try:
            val = float(str(val).replace(',', '')) if val is not None else None
        except (ValueError, TypeError):
            val = None

        unit = "metric tons CO2e"

        scope_year = scope_data.get("year")
        scope_year = self._safe_int(scope_year)
        if scope_year is not None and (scope_year < 2000 or scope_year > 2100):
            scope_year = None

        if year and not scope_year:
            scope_year = year

        return {
            "value": val,
            "unit": unit,
            "year": scope_year
        }

    def _safe_int(self, value):
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
