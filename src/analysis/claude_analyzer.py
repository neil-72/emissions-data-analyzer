from anthropic import Anthropic
from typing import Dict, Optional
import re
import logging
import json
from ..config import CLAUDE_API_KEY

class EmissionsAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=CLAUDE_API_KEY)
        self.target_sections = [
            "Greenhouse Gas Emissions", "Climate Change", "Environmental Data",
            "Scope 1 and 2", "GHG Emissions", "Carbon Footprint",
            "ESG Performance", "Environmental Metrics"
        ]
        self.table_keywords = [
            "Emissions Data", "GHG Data", "Environmental Performance",
            "Metrics and Targets", "Climate Data", "ESG Metrics"
        ]

    def extract_emissions_data(self, text: str) -> Optional[Dict]:
        """Extract emissions data using Claude."""
        logging.info("Starting emissions data extraction...")

        sections = self._extract_relevant_sections(text)
        if not sections.strip():
            logging.info("No relevant sections found, using full text...")
            sections = text

        # Strong instructions for JSON-only output
        system_instructions = (
            "You are an assistant that ONLY returns valid JSON with no extra text. "
            "If you cannot find any relevant data, return the specified JSON with null values. "
            "No explanations, no additional formatting, no text outside the JSON."
        )

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
- If units are not in metric tons CO2e, convert or interpret them as metric tons CO2e.
- If scope data is not explicitly labeled as "Scope 1" or "Scope 2", infer from context.
- Do not include commentary or explanations outside the JSON.
- If no data is found, return the JSON with null values for all numbers and an empty string for source_location.

Text to analyze (may include page markers like '=== START PAGE X ==='):

{sections[:50000]}
""".strip()

        try:
            logging.info("Sending request to Claude...")
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                system=system_instructions,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0,
                max_tokens=4000
            )

            if response.content:
                content = response.content[0].text
                logging.info("Response received from Claude")

                # Try to directly parse the entire response as JSON
                data = self._parse_json_response(content)
                if data is None:
                    # Try regex-based extraction as a fallback
                    json_match = re.search(r'(\{.*"scope_1".*"scope_2".*?\})', content, re.DOTALL)
                    if json_match:
                        data_str = json_match.group(1)
                        data = self._parse_json_response(data_str)

                # Final validation and normalization
                if data:
                    data = self._normalize_and_validate(data)
                else:
                    logging.warning("Could not parse emissions data from Claude's response.")

                return data
            else:
                logging.warning("No content in Claude response")
                return None

        except Exception as e:
            logging.error(f"Error in Claude analysis: {str(e)}")
            return None

    def _extract_relevant_sections(self, text: str) -> str:
        """Extract sections likely to contain emissions data."""
        lines = text.split('\n')
        sections = []
        current_section = []
        in_relevant_section = False
        page_marker = None

        # Heuristic: start a "section" when we see a target keyword, table keyword, or scope line
        for line in lines:
            if "=== START PAGE" in line:
                page_marker = line
                continue
            if "=== END PAGE" in line:
                # End current section if it existed
                if current_section and page_marker:
                    sections.append(f"{page_marker}\n{''.join(current_section)}\n{line}")
                current_section = []
                page_marker = None
                in_relevant_section = False
                continue

            is_target = any(kw.lower() in line.lower() for kw in self.target_sections)
            is_table = any(kw.lower() in line.lower() for kw in self.table_keywords)
            has_scope_line = re.search(r'(?i)scope\s*[12]', line)
            has_numbers = re.search(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?', line)

            if is_target or is_table or (has_scope_line and has_numbers):
                # Start a new relevant section
                if current_section:
                    sections.append(''.join(current_section))
                current_section = [line + "\n"]
                in_relevant_section = True
            elif in_relevant_section:
                # Continue current section until a probable new section begins
                current_section.append(line + "\n")

        # Catch trailing section
        if current_section:
            sections.append(''.join(current_section))

        return '\n\n'.join(sections)

    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Try to parse Claude's response as JSON."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logging.error("Failed to parse JSON data from Claude response")
            return None

    def _normalize_and_validate(self, data: Dict) -> Optional[Dict]:
        """Normalize units and values without rejecting partial data."""
        required_scopes = ["scope_1", "scope_2"]
        if not all(scope in data for scope in required_scopes):
            logging.warning("Missing scope_1 or scope_2 in returned data. Returning anyway.")

        for scope in required_scopes:
            if scope in data:
                scope_data = data[scope]

                # Normalize value
                value = scope_data.get("value")
                if isinstance(value, str):
                    value = value.replace(',', '').strip()
                    try:
                        value = float(value)
                    except ValueError:
                        logging.warning(f"Non-numeric value for {scope}: {scope_data['value']}. Setting to None.")
                        value = None
                scope_data["value"] = value

                # Normalize units
                unit = scope_data.get("unit", "").lower()
                if "co2" in unit or "ton" in unit:
                    scope_data["unit"] = "metric tons CO2e"
                else:
                    scope_data["unit"] = "metric tons CO2e"

                # Validate year
                year = scope_data.get("year")
                if year and isinstance(year, int):
                    if not (2000 <= year <= 2100):
                        logging.warning(f"Year {year} out of normal range, keeping as is.")
                else:
                    # Set year to None if not valid
                    if year is None or not isinstance(year, int):
                        logging.warning(f"No valid year found for {scope}, setting to None.")
                        scope_data["year"] = None

        return data
