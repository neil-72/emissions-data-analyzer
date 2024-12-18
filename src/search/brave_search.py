import requests
import logging
import re
from typing import Dict, Optional
from ..config import (
    BRAVE_API_KEY, 
    SEARCH_YEARS, 
    MAX_RESULTS_PER_SEARCH
)
from ..extraction.pdf_handler import DocumentHandler

class EmissionsTracker:
    """# Main class for tracking and analyzing company emissions data
    # Handles the end-to-end process of:
    # 1. Finding sustainability reports via Brave Search
    # 2. Extracting text content from PDFs
    # 3. Using Claude to analyze emissions data
    # 4. Saving structured results as JSON
    """
    def __init__(self):
        try:
            # Core components that handle different parts of the process
            self.search_client = BraveSearchClient()  # Finds reports using Brave Search
            self.analyzer = EmissionsAnalyzer()       # Analyzes text using Claude
            self.document_handler = DocumentHandler()  # Handles PDF extraction
            os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        except Exception as e:
            logging.error(f"Failed to initialize EmissionsTracker: {str(e)}")
            raise

    def process_company(self, company_name: str) -> Optional[Dict]:
        """# Process a single company to extract emissions data
        # Flow:
        # 1. Search for latest sustainability report
        # 2. Extract PDF text content
        # 3. Analyze for emissions data
        # 4. Structure and save results
        """
        if not company_name or not company_name.strip():
            logging.error("Invalid company name provided")
            return None

        try:
            logging.info(f"Starting analysis for {company_name}")

            report_data = self.search_client.search_sustainability_report(company_name)
            if not report_data:
                logging.warning("No sustainability report found")
                return None

            logging.info(f"Found report for {company_name} from year {report_data['year']}")
            text_content = self.document_handler.get_document_content(report_data['url'])
            if not text_content:
                logging.error("Failed to extract text from document")
                return None

            text_length = len(text_content)
            logging.info(f"Successfully extracted text ({text_length:,} characters)")

            if text_length < 50:
                logging.warning("Extracted text suspiciously short")
                return None

            emissions_data = self.analyzer.extract_emissions_data(text_content, company_name)
            if not emissions_data:
                logging.warning("No emissions data found in text")
                return None

            # Structure the final results
            result = {
                "company": company_name,
                "report_url": report_data['url'],
                "report_year": report_data['year'],
                "emissions_data": emissions_data,
                "processed_at": self._get_timestamp()
            }

            self._save_results(company_name, result)
            logging.info("Analysis complete")
            return result

        except Exception as e:
            logging.error(f"Error processing {company_name}: {str(e)}")
            return None

    def _save_results(self, company_name: str, data: Dict):
        """# Save results to JSON file in the output directory
        # Uses company name for filename, lowercased with underscores"""
        filename = os.path.join(
            DEFAULT_OUTPUT_DIR,
            f"{company_name.lower().replace(' ', '_')}.json"
        )
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logging.info(f"Results saved to {filename}")
        except Exception as e:
            logging.error(f"Failed to save results: {str(e)}")

    def _get_timestamp(self) -> str:
        """# Get current timestamp in ISO format for result tracking"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

def main():
    """# Main entry point for command line usage
    # Provides interactive prompt for company names"""
    try:
        tracker = EmissionsTracker()
        print("\nEmissions Data Analyzer")
        print("----------------------")
        print("Enter company names (or 'quit' to exit)")

        while True:
            try:
                company_name = input("\nCompany name: ").strip()
                if company_name.lower() in ['quit', 'exit', 'q']:
                    break
                if not company_name:
                    continue

                result = tracker.process_company(company_name)
                if result:
                    print("\nResults found:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                else:
                    print("\nNo results found")

            except KeyboardInterrupt:
                print("\nOperation cancelled")
                continue

    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        logging.error(f"Program error: {str(e)}")
        print("\nProgram terminated due to error")
    finally:
        print("\nGoodbye!")

if __name__ == "__main__":
    main()
