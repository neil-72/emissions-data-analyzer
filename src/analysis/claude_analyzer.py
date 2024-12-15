from anthropic import Anthropic
from typing import Dict, Optional, List
import re
import logging
import json
from ..config import CLAUDE_API_KEY


class EmissionsAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=CLAUDE_API_KEY)

        # Comprehensive target sections based on observations and patterns
        self.target_sections = [
            "Greenhouse Gas Emissions", "Climate Change", "Environmental Data",
            "Scope 1", "Scope 2", "Scope 3", "Scope 1 and 2", "Direct emissions",
            "Indirect emissions", "Carbon Footprint", "Carbon removals", "Corporate Emissions",
            "Location-based emissions", "Market-based emissions", "GHG emissions intensity",
            "Subtotal emissions", "Total net carbon footprint", "Product Life Cycle Emissions",
            "Purchased goods and services", "Upstream impacts", "Assessment of progress",
            "Climate and Efficiency", "Environmental Performance", "ESG Metrics"
        ]

        # Comprehensive table keywords for broader coverage
        self.table_keywords = [
            "Emissions Data", "GHG Data", "Scope 1", "Scope 2", "Scope 3",
            "Market-based emissions", "Location-based emissions", "Environmental Performance",
            "Metrics and Targets", "Climate Data", "Direct emissions", "Indirect emissions",
            "Subtotal emissions", "Total emissions", "Business travel", "Employee commuting",
            "Energy consumption", "Assessment of progress", "Total carbon emissions"
        ]

    def extract_emissions_data(self, text: str) -> Optional[Dict]:
        """Extract emissions data using Claude."""
        logging.info("Starting emissions data extraction...")

        # Extract relevant sections from the text
        sections = self._extract_relevant_sections(text, page_threshold=20)
        if not sections.strip():
            logging.info("No relevant sections found in priority pages, using full text...")
            sections = text

        # Instructions for Claude to return JSON-only data
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
- Prioritize tables and direct numerical data.
- Do not include commentary or explanations outside the JSON.

Text to analyze (may include page markers like '=== START PAGE X ==='):

{sections[:100000]}
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

            if response.content:
                content = response.content[0].text
                logging.info("Response received from Claude")

                # Attempt to parse JSON response
                data = self._parse_json_response(content)
                if data is None:
                    json_match = re.search(r'(\{.*"scope_1".*"scope_2".*?\})', content, re.DOTALL)
                    if json_match:
                        data_str = json_match.group(1)
                        data = self._parse_json_response(data_str)

                # Validate and normalize parsed data
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
        """
        Extract relevant emissions-related sections, prioritizing the first and last few pages.
        """
        lines = text.split('\n')
        pages = self._split_text_into_pages(lines)
        prioritized_pages = pages[:page_threshold] + pages[-page_threshold:]

        sections = []
        for page in prioritized_pages:
            current_section = []
            for line in page:
                is_target = any(kw.lower() in line.lower() for kw in self.target_sections)
                is_table = any(kw.lower() in line.lower() for kw in self.table_keywords)
                has_scope_line = re.search(r'(?i)scope\s*[123]', line)
                has_numbers = re.search(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?', line)

                if is_target or is_table or (has_scope_line and has_numbers):
                    current_section.append(line)
            if current_section:
                sections.append('\n'.join(current_section))

        return '\n\n'.join(sections) if sections else text

    def _split_text_into_pages(self, lines: list) -> list:
        """Split the text into pages using page markers."""
        pages = []
        current_page = []
        for line in lines:
            if "=== START PAGE" in line:
                if current_page:
                    pages.append(current_page)
                current_page = [line]
            elif "=== END PAGE" in line:
                current_page.append(line)
                pages.append(current_page)
                current_page = []
            else:
                current_page.append(line)
        if current_page:
            pages.append(current_page)
        return pages

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
                try:
                    value = float(str(scope_data.get("value", "0")).replace(',', ''))
                    scope_data["value"] = value
                except ValueError:
                    scope_data["value"] = None
                scope_data["unit"] = "metric tons CO2e"
                year = scope_data.get("year")
                if not (2000 <= year <= 2100):
                    scope_data["year"] = None
        return data
