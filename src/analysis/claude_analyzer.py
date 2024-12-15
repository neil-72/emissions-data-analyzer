from anthropic import Anthropic
from typing import Dict, Optional
from ..config import CLAUDE_API_KEY

class EmissionsAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=CLAUDE_API_KEY)

    def extract_emissions_data(self, text: str) -> Dict:
        """Extract emissions data using Claude."""
        print("\nStarting emissions data extraction...")
        print(f"Text length: {len(text)} characters")
        
        prompt = f"""
        You are analyzing a sustainability report to extract carbon emissions data.
        Focus only on finding Scope 1 and Scope 2 emissions numbers.
        If you find multiple years of data, use the most recent year.
        
        Text to analyze:
        {text[:50000]}  # Limiting text length

        Return ONLY a JSON object with this structure, nothing else:
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
        """

        try:
            print("Sending request to Claude...")
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            if hasattr(response, 'content') and len(response.content) > 0:
                content = response.content[0].text
                print(f"Response received: {content[:200]}...")
                return content
            else:
                print("No content in response")
                return None

        except Exception as e:
            print(f"Detailed error in Claude analysis: {str(e)}")
            print(f"Error type: {type(e)}")
            return None