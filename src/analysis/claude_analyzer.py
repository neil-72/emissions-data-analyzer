from anthropic import Anthropic
from typing import Dict, Optional, List
import re
import logging
import json
from ..config import CLAUDE_API_KEY

class EmissionsAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=CLAUDE_API_KEY)
        self.target_sections = [
            "Greenhouse Gas Emissions",
            "Climate Change",
            "Environmental Data",
            "Scope 1 and 2",
            "GHG Emissions",
            "Carbon Footprint",
            "ESG Performance",
            "Environmental Metrics"
        ]
        self.table_keywords = [
            "Emissions Data",
            "GHG Data",
            "Environmental Performance",
            "Metrics and Targets",
            "Climate Data",
            "ESG Metrics"
        ]

    def extract_emissions_data(self, text: str) -> Optional[Dict]:
        """Extract emissions data using Claude."""
        logging.info("Starting emissions data extraction...")
        
        sections = self._extract_relevant_sections(text)
        if not sections:
            logging.info("No relevant sections found, using full text...")
            sections = text

        prompt = f"""You are analyzing a sustainability report to find Scope 1 and 2 emissions data.
        Focus ONLY on extracting these specific data points:
        1. Scope 1 (direct) emissions value and unit for the most recent year
        2. Scope 2 (indirect) emissions value and unit for the most recent year
        3. The reporting year for this data
        
        Important notes:
        - Text will contain page markers like "=== START PAGE X ===" to help locate data
        - Look for tables and data sections, particularly after these keywords: emissions, ghg, carbon, scope
        - Data might be presented in different units (convert if needed to metric tons CO2e)
        - Verify numbers are from the most recent year available
        - Commonly found in: ESG data tables, environmental metrics, GRI/SASB indices
        
        Return ONLY this exact JSON structure with numeric values:
        {{
            "scope_1": {{
                "value": <number>,
                "unit": "metric tons CO2e",
                "year": <YYYY>
            }},
            "scope_2": {{
                "value": <number>,
                "unit": "metric tons CO2e", 
                "year": <YYYY>
            }},
            "source_location": "Brief description of where in report data was found (include page numbers if marked)"
        }}
        
        Text to analyze:
        {sections[:50000]}
        """

        try:
            logging.info("Sending request to Claude...")
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                messages=[{"role": "user", "content": prompt}]
            )
            
            if hasattr(response, 'content') and len(response.content) > 0:
                content = response.content[0].text
                logging.info("Response received from Claude")
                
                # Try to extract JSON even if there's surrounding text
                try:
                    json_match = re.search(r'({[^{]*"scope_1".*"scope_2".*})', content)
                    if json_match:
                        content = json_match.group(1)
                except:
                    pass
                    
                data = self._validate_emissions_data(content)
                return data
            else:
                logging.warning("No content in Claude response")
                return None

        except Exception as e:
            logging.error(f"Error in Claude analysis: {str(e)}")
            return None

    def _extract_relevant_sections(self, text: str) -> str:
        """Extract sections likely to contain emissions data."""
        sections = []
        lines = text.split('\n')
        current_section = []
        in_relevant_section = False
        page_marker = None
        
        for line in lines:
            # Track page markers
            if "=== START PAGE" in line:
                page_marker = line
                continue
            if "=== END PAGE" in line:
                if current_section and page_marker:
                    sections.append(f"{page_marker}\n{''.join(current_section)}\n{line}")
                current_section = []
                page_marker = None
                continue
                
            # Check for relevant content
            is_target = any(keyword.lower() in line.lower() for keyword in self.target_sections)
            is_table = any(keyword.lower() in line.lower() for keyword in self.table_keywords)
            has_scope = re.search(r'(?i)scope\s*[12]', line)
            has_numbers = re.search(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?', line)
            
            if is_target or is_table or (has_scope and has_numbers):
                in_relevant_section = True
                if current_section:
                    sections.append(''.join(current_section))
                current_section = [line]
            elif in_relevant_section:
                current_section.append(line)
                # Check if section should end
                if line.strip() and line.strip()[0].isupper() and len(line.split()) <= 5:
                    in_relevant_section = False
                    if current_section:
                        sections.append(''.join(current_section))
                    current_section = []
        
        if current_section:
            sections.append(''.join(current_section))
        
        return '\n\n'.join(sections)

    def _validate_emissions_data(self, data: str) -> Optional[Dict]:
        """Validate extracted emissions data meets expected ranges and formats."""
        typical_ranges = {
            'scope_1': (100, 10000000),  # Typical corporate ranges
            'scope_2': (1000, 20000000)  # Usually higher than scope 1
        }
        
        try:
            if isinstance(data, str):
                data = json.loads(data)
            
            # Basic structure check
            required_fields = {'scope_1', 'scope_2', 'source_location'}
            if not all(field in data for field in required_fields):
                logging.warning("Missing required fields in data")
                return None
            
            # Validate each scope
            for scope in ['scope_1', 'scope_2']:
                scope_data = data[scope]
                
                # Check all required fields exist
                if not all(field in scope_data for field in ['value', 'unit', 'year']):
                    logging.warning(f"Missing required fields in {scope}")
                    return None
                
                # Validate value
                value = scope_data['value']
                if not isinstance(value, (int, float)):
                    logging.warning(f"{scope} value {value} is not numeric")
                    return None
                    
                # Check range
                min_val, max_val = typical_ranges[scope]
                if not min_val <= value <= max_val:
                    logging.warning(f"{scope} value {value} outside typical range")
                    return None
                
                # Validate unit
                if not isinstance(scope_data['unit'], str) or 'co2' not in scope_data['unit'].lower():
                    logging.warning(f"Invalid unit format for {scope}")
                    return None
                
                # Validate year
                year = scope_data['year']
                if not isinstance(year, int) or not (2020 <= year <= 2024):
                    logging.warning(f"Invalid year for {scope}: {year}")
                    return None
            
            return data
            
        except json.JSONDecodeError:
            logging.error("Failed to parse JSON data")
            return None
        except Exception as e:
            logging.error(f"Error validating data: {str(e)}")
            return None
