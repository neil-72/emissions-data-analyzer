import json
import logging
import os
from typing import Dict, Optional
from .search.brave_search import BraveSearchClient
from .extraction.pdf_handler import DocumentHandler
from .analysis.claude_analyzer import EmissionsAnalyzer
from .config import DEFAULT_OUTPUT_DIR

# Configure logging
logging.basicConfig(level=logging.INFO)

class EmissionsTracker:
    def __init__(self):
        self.search_client = BraveSearchClient()
        self.analyzer = EmissionsAnalyzer()
        self.document_handler = DocumentHandler()

    def process_company(self, company_name: str) -> Optional[Dict]:
        """Process a company to extract emissions data."""
        try:
            logging.info(f"Starting analysis for {company_name}")
            
            # Step 1: Search for report
            report_data = self.search_client.search_sustainability_report(company_name)
            if not report_data:
                logging.warning("No sustainability report found")
                return None

            # Step 2: Extract text
            logging.info(f"Found report for {company_name} from year {report_data['year']}")
            text_content = self.document_handler.get_document_content(report_data['url'])
            if not text_content:
                logging.error("Failed to extract text from document")
                return None

            logging.info(f"Successfully extracted text ({len(text_content)} characters)")
            
            # Step 3: Analyze for emissions data
            emissions_data = self.analyzer.extract_emissions_data(text_content)
            if not emissions_data:
                logging.warning("No emissions data found in text")
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
            logging.info("Analysis complete")
            return result

        except Exception as e:
            logging.error(f"Error processing {company_name}: {str(e)}")
            return None

    def _save_results(self, company_name: str, data: Dict):
        """Save results to JSON file."""
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        filename = os.path.join(DEFAULT_OUTPUT_DIR, 
                                f"{company_name.lower().replace(' ', '_')}.json")
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logging.info(f"Results saved to {filename}")


if __name__ == "__main__":
    tracker = EmissionsTracker()
    company_name = input("Enter company name: ")
    result = tracker.process_company(company_name)
    
    if result:
        logging.info("Final Results:")
        print(json.dumps(result, indent=2))
    else:
        logging.info("No results found")
