import json
from typing import Dict, Optional
from .search.brave_search import BraveSearchClient
from .extraction.pdf_handler import DocumentHandler
from .analysis.claude_analyzer import EmissionsAnalyzer
from .config import DEFAULT_OUTPUT_DIR
import os

class EmissionsTracker:
    def __init__(self):
        self.search_client = BraveSearchClient()
        self.analyzer = EmissionsAnalyzer()

    def process_company(self, company_name: str) -> Optional[Dict]:
        """Process a company to extract emissions data."""
        try:
            # Step 1: Search for report
            print(f"Searching for {company_name}'s sustainability report...")
            report_data = self.search_client.search_sustainability_report(company_name)
            
            if not report_data:
                print(f"No sustainability report found for {company_name}")
                return None

            # Step 2: Extract text
            print(f"Found report from {report_data['year']}. Processing...")
            text_content = DocumentHandler.get_document_content(report_data['url'])
            
            if not text_content:
                print("Unable to extract text from report")
                return None

            # Step 3: Analyze content
            print("Analyzing report content...")
            emissions_data = self.analyzer.extract_emissions_data(text_content)
            
            if not emissions_data:
                print("Unable to extract emissions data")
                return None

            # Step 4: Combine results
            result = {
                "company": company_name,
                "report_url": report_data['url'],
                "report_year": report_data['year'],
                "emissions_data": emissions_data
            }

            # Save results
            self._save_results(company_name, result)
            
            return result

        except Exception as e:
            print(f"Error processing {company_name}: {str(e)}")
            return None

    def _save_results(self, company_name: str, data: Dict):
        """Save results to JSON file."""
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        filename = os.path.join(DEFAULT_OUTPUT_DIR, 
                              f"{company_name.lower().replace(' ', '_')}.json")
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Results saved to {filename}")


if __name__ == "__main__":
    tracker = EmissionsTracker()
    company_name = input("Enter company name: ")
    result = tracker.process_company(company_name)
    
    if result:
        print("\nResults:")
        print(json.dumps(result, indent=2))
    else:
        print("No results found")