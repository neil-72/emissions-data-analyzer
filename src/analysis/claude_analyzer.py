import json
import logging
from typing import Dict, Optional
import anthropic
from ..config import CLAUDE_API_KEY

class EmissionsAnalyzer:
    def __init__(self):
        self.client = anthropic.Client(api_key=CLAUDE_API_KEY)

    def extract_emissions_data(self, text_content: str, company_name: str) -> Optional[Dict]:
        try:
            prompt = f"""Extract Scope 1 and Scope 2 emissions data from this sustainability report text.
            Company: {company_name}
            
            Important guidelines:
            1. Only extract explicitly stated emissions values
            2. Convert all values to metric tons CO2e
            3. Include both market-based and location-based Scope 2 if available
            4. Return only the most recent year's data
            5. Return data in JSON format
            
            Text content:
            {text_content[:10000]}...
            """
            
            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0,
                system="You are an expert at analyzing sustainability reports and extracting emissions data. Return only valid, explicitly stated emissions data in JSON format.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            try:
                result = json.loads(message.content)
                
                if result.get('scope_1') and result.get('scope_2_market_based'):
                    return result
                else:
                    return None

            except json.JSONDecodeError:
                logging.error("Failed to parse Claude's response as JSON")
                return None

        except Exception as e:
            logging.error(f"Error in emissions data extraction: {str(e)}")
            return None