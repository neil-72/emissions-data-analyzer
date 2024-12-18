import re
import json
import logging
from typing import Dict, Optional
from anthropic import Anthropic
from ..config import CLAUDE_API_KEY

class EmissionsAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=CLAUDE_API_KEY)
        # Keep it simple - just check for scope data
        self.scope_pattern = r'(?i)scope\s*[12]'

    def extract_emissions_data(self, text: str, company_name: str = None) -> Optional[Dict]:
        """Extract emissions data using Claude."""
        logging.info("Starting emissions data extraction...")

        # Basic check for scope data
        if not re.search(self.scope_pattern, text):
            logging.warning("No scope 1/2 mentions found in text")
            return None

        # Keep text within Claude's context window
        sections = text[:30000]  # Conservative limit for context
        
        prompt = f"""
Analyze this sustainability report{f' for {company_name}' if company_name else ''}. 
Find and extract:
1. Most recent Scope 1 & 2 emissions data (with reporting year)
2. Previous years' Scope 1 & 2 data
3. Whether Scope 2 is market-based or location-based
4. Context of where data was found
{f'5. Identify {company_name}\'s sector based on your knowledge' if company_name else ''}

Some data might appear in tables, some in text. Convert all units to metric tons CO2e.
For Scope 2, specify if it's market-based or location-based when possible.

Return ONLY this exact JSON format with NO other text:
{{
  "scope_1": {{
    "value": <number or null>,
    "unit": "metric tons CO2e",
    "year": <YYYY or null>,
    "year_type": "<fiscal or calendar>"
  }},
  "scope_2": {{
    "value": <number or null>,
    "unit": "metric tons CO2e",
    "year": <YYYY or null>,
    "measurement": "<market-based or location-based or unknown>"
  }},
  "source_details": {{
    "location": "<where found>",
    "context": "<relevant context>"
  }},
  "previous_years": [
    {{
      "year": <YYYY>,
      "scope_1": <number>,
      "scope_2": <number>
    }}
  ],
  "sector": "<sector or null>"
}}

Text to analyze:
{sections}
""".strip()

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

            data = self._parse_and_validate(response.content[0].text)
            return data

        except Exception as e:
            logging.error(f"Error in Claude analysis: {str(e)}")
            return None

    def _parse_and_validate(self, content: str) -> Optional[Dict]:
        """Parse and validate Claude's JSON response."""
        try:
            data = json.loads(content)
            
            # Basic validation
            required_keys = {"scope_1", "scope_2", "source_details", "previous_years"}
            if not all(k in data for k in required_keys):
                logging.warning("Missing required keys in JSON response")
                return None

            # Normalize values
            for scope in ["scope_1", "scope_2"]:
                if data[scope].get("value"):
                    try:
                        # Handle number formatting
                        val_str = str(data[scope]["value"]).replace(',', '')
                        data[scope]["value"] = float(val_str)
                    except (ValueError, TypeError):
                        data[scope]["value"] = None

            # Validate previous years
            if data["previous_years"]:
                cleaned_years = []
                for entry in data["previous_years"]:
                    if isinstance(entry.get("year"), int) and entry.get("scope_1") is not None:
                        try:
                            # Clean number formatting
                            entry["scope_1"] = float(str(entry["scope_1"]).replace(',', ''))
                            entry["scope_2"] = float(str(entry["scope_2"]).replace(',', ''))
                            cleaned_years.append(entry)
                        except (ValueError, TypeError):
                            continue
                data["previous_years"] = cleaned_years

            return data

        except json.JSONDecodeError:
            logging.error("Failed to parse JSON from Claude response")
            return None
