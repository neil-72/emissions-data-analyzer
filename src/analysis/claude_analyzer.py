import re
import json
import logging
from typing import Dict, Optional, List
from anthropic import Anthropic
from termcolor import colored
from ..config import CLAUDE_API_KEY


class EmissionsAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=CLAUDE_API_KEY)
        self.scope_pattern = r'(?i)scope\s*[12]'

    def extract_emissions_data(self, text: str, company_name: str = None) -> Optional[Dict]:
        """Extract emissions data using Claude."""
        logging.info("Starting emissions data extraction...")

        # Extract relevant lines with context and remove duplicates
        relevant_lines = self._extract_lines_with_context(text, lines_before=15, lines_after=15)
        relevant_lines = list(dict.fromkeys(relevant_lines))  # Remove duplicates
        if not relevant_lines:
            logging.warning("No relevant context found for Scope 1/2 in text")
            return None

        # Write the relevant lines to a file for inspection
        with open("claude_input_data.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(relevant_lines))

        # Split into chunks if text exceeds Claude's input limit
        chunks = self._split_into_chunks(relevant_lines, max_chars=30000)
        all_results = []

        for i, chunk in enumerate(chunks):
            # Write each chunk to a file for inspection
            chunk_filename = f"claude_input_chunk_{i + 1}.txt"
            with open(chunk_filename, "w", encoding="utf-8") as f:
                f.write(chunk)

            result = self._send_to_claude(chunk, company_name)
            if result:
                all_results.append(result)

        # Aggregate results from all chunks
        final_results = self._aggregate_results(all_results)

        # Print formatted output to terminal
        self._pretty_print_output(final_results)
        return final_results

    def _extract_lines_with_context(self, text: str, lines_before: int, lines_after: int) -> List[str]:
        """Extract lines containing relevant keywords and include surrounding context."""
        lines = text.split('\n')
        relevant_lines = []
        for i, line in enumerate(lines):
            if re.search(self.scope_pattern, line):
                start = max(0, i - lines_before)
                end = min(len(lines), i + lines_after + 1)
                relevant_lines.extend(lines[start:end])
        return relevant_lines

    def _split_into_chunks(self, lines: List[str], max_chars: int) -> List[str]:
        """Split the lines into chunks that fit within the character limit."""
        chunks = []
        current_chunk = []
        current_length = 0

        for line in lines:
            line_length = len(line) + 1  # Add 1 for newline
            if current_length + line_length > max_chars:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_length = 0
            current_chunk.append(line)
            current_length += line_length

        if current_chunk:
            chunks.append("\n".join(current_chunk))
        return chunks

    def _send_to_claude(self, text: str, company_name: str = None) -> Optional[Dict]:
        """Send a chunk of text to Claude for analysis."""
        prompt = f"""
Analyze this sustainability report{f' for {company_name}' if company_name else ''}.
Extract the following:
1. Most recent Scope 1 and Scope 2 emissions data, with reporting year and measurement type (market-based or location-based).
2. Scope 1 and Scope 2 data for the previous two years.
3. Context of where the data was found.

Return ONLY this JSON format:
{{
  "company": "{company_name}",
  "sector": "<sector or null>",
  "current_year": {{
    "year": <YYYY or null>,
    "scope_1": {{
      "value": <number or null>,
      "unit": "metric tons CO2e",
      "measurement": "<market-based or location-based or unknown>"
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

    def _parse_and_validate(self, content: str) -> Optional[Dict]:
        """Parse and validate Claude's JSON response."""
        try:
            data = json.loads(content)
            return data
        except json.JSONDecodeError:
            logging.error("Failed to parse JSON from Claude response")
            return None

    def _aggregate_results(self, results: List[Dict]) -> Dict:
        """Combine results from multiple chunks."""
        combined = {
            "current_year": {},
            "previous_years": [],
            "source_details": None,
            "sector": None
        }

        for result in results:
            if not combined["current_year"]:
                combined["current_year"] = result.get("current_year", {})
            combined["previous_years"].extend(result.get("previous_years", []))
            if not combined["source_details"]:
                combined["source_details"] = result.get("source_details", None)
            if not combined["sector"]:
                combined["sector"] = result.get("sector", None)

        return combined

    def _pretty_print_output(self, data: Dict):
        """Format and display the output in the terminal."""
        if not data:
            print(colored("No data to display.", "red"))
            return

        formatted_json = json.dumps(data, indent=4)
        print(colored(f"Results for {data.get('company', 'Unknown Company')}:", "blue", attrs=["bold"]))
        print(colored(formatted_json, "green"))
