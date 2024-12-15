from anthropic import Anthropic
from typing import Dict, Optional, List
import re
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
            "Carbon Footprint"
        ]
        self.table_keywords = [
            "Emissions Data",
            "GHG Data",
            "Environmental Performance",
            "Metrics and Targets"
        ]

    def extract_emissions_data(self, text: str) -> Dict:
        """Extract emissions data using Claude."""
        print("\nStarting emissions data extraction...")
        
        # First try to find relevant sections
        sections = self._extract_relevant_sections(text)
        if not sections:
            print("Could not find relevant sections. Trying full text...")
            sections = text

        # Prepare prompt with targeted sections
        prompt = f"""You are analyzing a sustainability report to find Scope 1 and 2 emissions data.
        Focus ONLY on extracting these specific data points:
        1. Scope 1 (direct) emissions value and unit for the most recent year
        2. Scope 2 (indirect) emissions value and unit for the most recent year
        3. The reporting year for this data
        
        Look for tables, data sections, or environmental metrics sections. Common locations include:
        - Executive summary
        - ESG data tables
        - Climate/Environmental performance sections
        - GRI/SASB indices
        
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
            "source_location": "Brief description of where in report data was found"
        }}
        
        Text to analyze:
        {sections[:50000]}
        """

        try:
            print("Sending request to Claude...")
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                messages=[{"role": "user", "content": prompt}]
            )
            
            if hasattr(response, 'content') and len(response.content) > 0:
                content = response.content[0].text
                print(f"Response received: {content[:200]}...")
                data = self._validate_emissions_data(content)
                return data
            else:
                print("No content in response")
                return None

        except Exception as e:
            print(f"Detailed error in Claude analysis: {str(e)}")
            print(f"Error type: {type(e)}")
            return None

    def _extract_relevant_sections(self, text: str) -> str:
        """Extract sections likely to contain emissions data."""
        sections = []
        lines = text.split('\n')
        current_section = []
        in_relevant_section = False
        
        for line in lines:
            # Check if line contains any target keywords
            is_target = any(keyword.lower() in line.lower() for keyword in self.target_sections)
            is_table = any(keyword.lower() in line.lower() for keyword in self.table_keywords)
            
            if is_target or is_table:
                in_relevant_section = True
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            elif in_relevant_section:
                current_section.append(line)
                # Check if section should end (e.g., new heading)
                if line.strip() and line.strip()[0].isupper() and len(line.split()) <= 5:
                    in_relevant_section = False
                    sections.append('\n'.join(current_section))
                    current_section = []
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        return '\n\n'.join(sections)

    def _validate_emissions_data(self, data: Dict) -> Dict:
        """Validate extracted emissions data meets expected ranges and formats."""
        typical_ranges = {
            'scope_1': (100, 10000000),  # Typical corporate ranges
            'scope_2': (1000, 20000000)  # Usually higher than scope 1
        }
        
        try:
            # Parse JSON if string
            if isinstance(data, str):
                import json
                data = json.loads(data)
            
            # Validate each scope
            for scope in ['scope_1', 'scope_2']:
                if scope not in data:
                    print(f"Missing {scope} data")
                    return None
                    
                scope_data = data[scope]
                value = scope_data['value']
                
                # Check numeric
                if not isinstance(value, (int, float)):
                    print(f"Warning: {scope} value {value} is not numeric")
                    return None
                
                # Check range
                min_val, max_val = typical_ranges[scope]
                if not min_val <= value <= max_val:
                    print(f"Warning: {scope} value {value} outside typical range")
                    return None
                
                # Check unit format
                if 'unit' not in scope_data or not isinstance(scope_data['unit'], str):
                    print(f"Invalid unit format for {scope}")
                    return None
                
                # Check year format
                if 'year' not in scope_data or not isinstance(scope_data['year'], int):
                    print(f"Invalid year format for {scope}")
                    return None
                
            return data
            
        except Exception as e:
            print(f"Error validating data: {str(e)}")
            return None