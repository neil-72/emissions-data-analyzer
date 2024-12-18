# EmissionsAnalyzer Class

# Handles the extraction of Scope 1 and Scope 2 emissions data from sustainability reports.
# Utilizes Claude API for advanced text analysis and ensures all units are in metric tons CO2e.

import re
import json
import logging
from typing import Dict, Optional, List
from anthropic import Anthropic
from ..config import CLAUDE_API_KEY


class EmissionsAnalyzer:
    # Initialization of the EmissionsAnalyzer
    def __init__(self):
        self.client = Anthropic(api_key=CLAUDE_API_KEY)  # Initialize the Claude API client.
        self.scope_pattern = r'(?i)scope\s*[12]'  # Regex to identify Scope 1 and 2 in text.

    # Main method to extract emissions data
    def extract_emissions_data(self, text: str, company_name: str = None) -> Optional[Dict]:
        """
        Orchestrates the entire data extraction process:
        - Extracts relevant lines with context.
        - Splits text into chunks for Claude API.
        - Sends text chunks to Claude and validates the responses.
        - Ensures all units are in metric tons CO2e.
        """
        logging.info("Starting emissions data extraction...")

        # Extract relevant lines with context, ensuring no duplicates
        relevant_lines = self._extract_lines_with_context(text, lines_before=15, lines_after=15)
        relevant_lines = list(dict.fromkeys(relevant_lines))  # Remove duplicate lines.

        # If no relevant lines are found, log a warning and exit
        if not relevant_lines:
            logging.warning("No relevant context found for Scope 1/2 in text")
            return None

        # Save extracted lines for debugging
        with open("claude_input_data.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(relevant_lines))

        # Split lines into chunks suitable for Claude API
        chunks = self._split_into_chunks(relevant_lines, max_chars=30000)
        all_results = []

        # Process each chunk with Claude API
        for chunk in chunks:
            result = self._send_to_claude(chunk, company_name)
            if result:
                all_results.append(result)

        # Aggregate and return results
        return self._aggregate_results(all_results)

    # Extract lines with relevant keywords and their context
    def _extract_lines_with_context(self, text: str, lines_before: int, lines_after: int) -> List[str]:
        """
        Identifies lines containing relevant keywords (Scope 1/2) and includes surrounding lines.
        """
        lines = text.split('\n')  # Split text into individual lines.
        relevant_lines = []

        for i, line in enumerate(lines):
            if re.search(self.scope_pattern, line):  # Check if the line matches the scope pattern.
                start = max(0, i - lines_before)  # Start line for context.
                end = min(len(lines), i + lines_after + 1)  # End line for context.
                relevant_lines.extend(lines[start:end])

        return relevant_lines

    # Split text into chunks for Claude API
    def _split_into_chunks(self, lines: List[str], max_chars: int) -> List[str]:
        """
        Splits extracted lines into chunks within Claude's input character limit.
        """
        chunks = []
        current_chunk = []
        current_length = 0

        for line in lines:
            line_length = len(line) + 1  # Include newline character.
            if current_length + line_length > max_chars:
                chunks.append("\n".join(current_chunk))  # Save current chunk.
                current_chunk = []
                current_length = 0
            current_chunk.append(line)
            current_length += line_length

        if current_chunk:  # Save any remaining lines as a chunk.
            chunks.append("\n".join(current_chunk))

        return chunks

    # Send a text chunk to Claude for analysis
    def _send_to_claude(self, text: str, company_name: str = None) -> Optional[Dict]:
        """
        Sends a chunk of text to Claude AI for emissions data extraction.
        """
        prompt = f"""
        Analyze this sustainability report{f' for {company_name}' if company_name else ''}.
        Extract the following:
        1. Most recent Scope 1 and Scope 2 emissions data, with reporting year and measurement type (market-based or location-based).
        2. Scope 1 and Scope 2 data for the previous two years.
        3. Context of where the data was found.
        Ensure all units are converted to metric tons CO2e if necessary.

        Return ONLY this JSON format:
        {{
          "company": "{company_name}",
          "sector": "<sector or null>",
          "current_year": {{
            "year": <YYYY or null>,
            "scope_1": {{
              "value": <number or null>,
              "unit": "metric tons CO2e"
            }},
            "scope_2_market_based": {{
              "value": <number or null>,
              "unit": "metric tons CO2e"
            }},
            "scope_2_location_based": {{
              "value": <number or null>,
              "unit": "metric tons CO2e"
            }}
          }},
          "previous_years": [
            {{
              "year": <YYYY or null>,
              "scope_1": {{
                "value": <number or null>,
                "unit": "metric tons CO2e"
              }},
              "scope_2_market_based": {{
                "value": <number or null>,
                "unit": "metric tons CO2e"
              }},
              "scope_2_location_based": {{
                "value": <number or null>,
                "unit": "metric tons CO2e"
              }}
            }}
          ],
          "source_details": {{
            "location": "<where found>",
            "context": "<relevant context>"
          }}
        }}

        Text to analyze:
        {text}
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

            return self._parse_and_validate(response.content[0].text)

        except Exception as e:
            logging.error(f"Error in Claude analysis: {str(e)}")
            return None

    # Validate and normalize the extracted data
    def _parse_and_validate(self, content: str) -> Optional[Dict]:
        """
        Parses Claude's JSON response, validates it, and ensures units are in metric tons CO2e.
        """
        try:
            data = json.loads(content)

            # Check for required keys in the JSON response
            required_keys = {"current_year", "previous_years", "source_details"}
            if not all(key in data for key in required_keys):
                logging.warning("Missing required keys in JSON response")
                return None

            # Normalize units to metric tons CO2e
            for key in ["current_year", "previous_years"]:
                if key in data:
                    for entry in (data[key] if key == "previous_years" else [data[key]]):
                        for scope in ["scope_1", "scope_2_market_based", "scope_2_location_based"]:
                            if scope in entry and entry[scope].get("value") is not None:
                                entry[scope]["value"] = self._convert_to_metric_tons(entry[scope])

            return data

        except json.JSONDecodeError:
            logging.error("Failed to parse JSON from Claude response")
            return None

    # Unit conversion helper method
    def _convert_to_metric_tons(self, scope_data: Dict) -> float:
        """
        Converts any unit to metric tons CO2e if necessary.
        Assumes input is already in metric tons CO2e unless otherwise stated.
        """
        # Placeholder: Add actual unit conversion logic if needed.
        return float(scope_data["value"])

    # Aggregate results from multiple chunks
    def _aggregate_results(self, results: List[Dict]) -> Dict:
        """
        Combines results from multiple Claude API calls into a single output.
        """
        combined = {
            "company": None,
            "sector": None,
            "current_year": {},
            "previous_years": [],
            "source_details": None
        }

        for result in results:
            if not combined["company"]:
                combined["company"] = result.get("company", None)
            if not combined["sector"]:
                combined["sector"] = result.get("sector", None)
            if not combined["current_year"]:
                combined["current_year"] = result.get("current_year", {})
            combined["previous_years"].extend(result.get("previous_years", []))
            if not combined["source_details"]:
                combined["source_details"] = result.get("source_details", None)

        # Remove duplicate entries in previous years
        combined["previous_years"] = list({json.dumps(year): year for year in combined["previous_years"]}.values())

        return combined
