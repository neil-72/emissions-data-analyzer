from anthropic import Anthropic
from typing import Dict, Optional
from ..config import CLAUDE_API_KEY

class EmissionsAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=CLAUDE_API_KEY)

    def extract_emissions_data(self, text: str) -> Dict:
        """Extract emissions data using Claude."""
        prompt = f"""
        Extract Scope 1 and Scope 2 carbon emissions data from this text.
        Return only a JSON object with this structure:
        {{
            "scope_1": {{
                "value": number,
                "unit": "string",
                "year": number
            }},
            "scope_2": {{
                "value": number,
                "unit": "string",
                "year": number
            }},
            "context": "string explaining trends or notes"
        }}

        Text to analyze:
        {text}
        """

        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return response.content[0].text
        except Exception as e:
            print(f"Error analyzing with Claude: {str(e)}")
            return None