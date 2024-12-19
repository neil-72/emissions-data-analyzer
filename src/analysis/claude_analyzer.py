import json
import logging
from typing import Dict, Optional
import anthropic
from ..config import CLAUDE_API_KEY

class EmissionsAnalyzer:
    def __init__(self):
        self.client = anthropic.Client(api_key=CLAUDE_API_KEY)

    def extract_emissions_data(self, text_content: str, company_name: str) -> Optional[Dict]:
        logging.info(f"\n{'='*50}")
        logging.info(f"Starting emissions data extraction for {company_name}")
        logging.info(f"{'='*50}")
        
        try:
            logging.info("Preparing request to Claude...")
            
            prompt = f"""Extract Scope 1 and Scope 2 emissions data from this sustainability report text.
            Company: {company_name}
            
            Important guidelines:
            1. Only extract explicitly stated emissions values
            2. Convert all values to metric tons CO2e
            3. Include both market-based and location-based Scope 2 if available
            4. Return only the most recent year's data
            5. Return data in a structured format
            
            Text content:
            {text_content[:10000]}...
            """
            
            logging.info(f"Analyzing text content ({len(text_content):,} characters)...")
            logging.info("Sending request to Claude for analysis...")
            
            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0,
                system="You are an expert at analyzing sustainability reports and extracting emissions data. Return only valid, explicitly stated emissions data in JSON format.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            logging.info("Response received from Claude")
            logging.info("Parsing extracted data...")
            
            try:
                result = json.loads(message.content)
                
                if result.get('scope_1') and result.get('scope_2_market_based'):
                    logging.info(f"\nExtracted Data Summary:")
                    logging.info(f"- Scope 1: {result['scope_1']['value']} {result['scope_1']['unit']}")
                    logging.info(f"- Scope 2 (Market): {result['scope_2_market_based']['value']} {result['scope_2_market_based']['unit']}")
                    if result.get('scope_2_location_based'):
                        logging.info(f"- Scope 2 (Location): {result['scope_2_location_based']['value']} {result['scope_2_location_based']['unit']}")
                    
                    return result
                else:
                    logging.warning("No valid emissions data found in Claude's response")
                    return None

            except json.JSONDecodeError:
                logging.error("Failed to parse Claude's response as JSON")
                return None

        except Exception as e:
            logging.error(f"Error in emissions data extraction: {str(e)}")
            return None