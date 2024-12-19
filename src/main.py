import json
import logging
import os
from typing import Dict, Optional
from .search.brave_search import BraveSearchClient
from .extraction.pdf_handler import DocumentHandler
from .analysis.claude_analyzer import EmissionsAnalyzer
from .config import DEFAULT_OUTPUT_DIR

# Configure logging to show detailed progress
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class EmissionsTracker:
    def __init__(self):
        try:
            self.search_client = BraveSearchClient()
            self.analyzer = EmissionsAnalyzer()
            self.document_handler = DocumentHandler()
            os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        except Exception as e:
            logging.error(f"Failed to initialize EmissionsTracker: {str(e)}")
            raise

    def process_company(self, company_name: str) -> Optional[Dict]:
        """Process a company to extract emissions data."""
        if not company_name or not company_name.strip():
            logging.error("Invalid company name provided")
            return None

        try:
            logging.info(f"\n{'='*50}")
            logging.info(f"Starting analysis for {company_name}")
            logging.info(f"{'='*50}")

            logging.info("Searching for sustainability report...")
            report_data = self.search_client.search_sustainability_report(company_name)
            if not report_data:
                logging.warning("No sustainability report found")
                return None

            logging.info(f"Found report for {company_name} from year {report_data['year']}")
            logging.info(f"URL: {report_data['url']}")

            logging.info("Extracting text from report...")
            text_content = self.document_handler.get_document_content(report_data['url'])
            if not text_content:
                logging.error("Failed to extract text from document")
                return None

            text_length = len(text_content)
            logging.info(f"Successfully extracted text ({text_length:,} characters)")

            if text_length < 50:
                logging.warning("Extracted text suspiciously short")
                return None

            logging.info("Analyzing emissions data...")
            emissions_data = self.analyzer.extract_emissions_data(text_content, company_name)
            if not emissions_data:
                logging.warning("No emissions data found in text")
                return None

            result = {
                "company": company_name,
                "report_url": report_data['url'],
                "report_year": report_data['year'],
                "emissions_data": emissions_data,
                "processed_at": self._get_timestamp()
            }

            self._save_results(company_name, result)
            logging.info(f"\n{'='*50}")
            logging.info("Analysis complete")
            logging.info(f"{'='*50}")
            return result

        except Exception as e:
            logging.error(f"Error processing {company_name}: {str(e)}")
            return None

    def _save_results(self, company_name: str, data: Dict):
        """Save results to JSON file."""
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
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

def main():
    """Main entry point for command line usage."""
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