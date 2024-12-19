import json
import logging
import os
from typing import Dict, Optional
from .search.brave_search import BraveSearchClient
from .extraction.pdf_handler import DocumentHandler
from .analysis.claude_analyzer import EmissionsAnalyzer
from .config import DEFAULT_OUTPUT_DIR

# ###############################################################################################################
# Configure logging to show detailed progress
# This ensures we get detailed INFO level logs which help us trace the execution flow.
# ###############################################################################################################
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class EmissionsTracker:
    def __init__(self):
        try:
            # #####################################################################################################
            # Initialize the search, analyzer, and PDF extraction.
            # If any of these fails, we log and raise an exception.
            # #####################################################################################################
            self.search_client = BraveSearchClient()
            self.analyzer = EmissionsAnalyzer()
            self.document_handler = DocumentHandler()

            # Create the default output directory if it doesn't exist
            os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        except Exception as e:
            logging.error(f"Failed to initialize EmissionsTracker: {str(e)}")
            raise

    def process_company(self, company_name: str) -> Optional[Dict]:
        """Process a company to extract emissions data."""
        # ###########################################################################################################
        # Validate that the company name is provided.
        # If not, log an error and return None.
        # ###########################################################################################################
        if not company_name or not company_name.strip():
            logging.error("Invalid company name provided")
            return None

        try:
            logging.info(f"\n{'='*50}")
            logging.info(f"Starting analysis for {company_name}")
            logging.info(f"{'='*50}")

            # #######################################################################################################
            # Step 1: Search for the company's sustainability report
            # #######################################################################################################
            logging.info("Searching for sustainability report...")
            report_data = self.search_client.search_sustainability_report(company_name)
            if not report_data:
                logging.warning("No sustainability report found")
                return None

            logging.info(f"Found report for {company_name} from year {report_data['year']}")
            logging.info(f"URL: {report_data['url']}")

            # #######################################################################################################
            # Step 2: Extract text from the identified report
            # #######################################################################################################
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

            # #######################################################################################################
            # Step 3: Analyze emissions data using the Claude Analyzer
            # #######################################################################################################
            logging.info("Analyzing emissions data...")
            emissions_data = self.analyzer.extract_emissions_data(text_content, company_name)
            if not emissions_data:
                logging.warning("No emissions data found in text")
                return None

            # #######################################################################################################
            # Create the result dictionary that includes the extracted data
            # #######################################################################################################
            result = {
                "company": company_name,
                "report_url": report_data['url'],
                "report_year": report_data['year'],
                "emissions_data": emissions_data,
                "processed_at": self._get_timestamp()
            }

            # #######################################################################################################
            # Save results
            # #######################################################################################################
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
            # #######################################################################################################
            # Write the results to the output JSON file with nice formatting.
            # #######################################################################################################
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logging.info(f"Results saved to {filename}")
        except Exception as e:
            logging.error(f"Failed to save results: {str(e)}")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    # ###############################################################################################################
    # Add a helper method to append URL to a blacklist file if data is empty.
    # We only check scope_1 for the current_year.
    # If scope_1 value is None, we add the URL to the blacklist.
    # ###############################################################################################################
    def _add_to_blacklist(self, url: str):
        blacklist_file = "blacklisted_urls.txt"
        with open(blacklist_file, "a", encoding="utf-8") as f:
            f.write(url + "\n")
        logging.info(f"URL added to blacklist: {url}")


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

                # ###################################################################################################
                # Run the analysis and get the result
                # ###################################################################################################
                result = tracker.process_company(company_name)
                if result:
                    # Print the results
                    print("\nResults found:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))

                    # ###################################################################################################
                    # Here is our simple check:
                    # After we have the final result, let's check if current_year's scope_1 value is None.
                    # If it is, we will add the report_url to the blacklist.
                    # ###################################################################################################
                    emissions_data = result.get("emissions_data", {})
                    current_year = emissions_data.get("current_year", {})
                    scope_1_value = current_year.get("scope_1", {}).get("value")

                    # If scope_1 is empty (None), we blacklist the URL
                    if scope_1_value is None:
                        report_url = result.get("report_url")
                        if report_url:
                            tracker._add_to_blacklist(report_url)

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
