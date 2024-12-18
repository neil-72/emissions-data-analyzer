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

class BraveSearchClient:
    def __init__(self):
        self.api_key = BRAVE_API_KEY
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        self.document_handler = DocumentHandler()
        
        # Keep the simple but effective scope 1 pattern
        self.scope_1_pattern = re.compile(r'(?i)scope[\s\-_]*1')
        
        # Add basic negative patterns to filter obvious non-reports
        self.negative_patterns = [
            'proxy statement',
            '10-k',
            '10k',
            'financial results'
        ]

    def search_sustainability_report(self, company_name: str) -> Optional[Dict]:
        """Search for a sustainability report PDF, preferring more recent years and ensuring 'scope 1' mention."""
        if not company_name.strip():
            logging.error("Empty company name provided")
            return None

        for year in SEARCH_YEARS:
            logging.info(f"Searching for {company_name} {year} sustainability report...")
            
            # Keep the same effective search terms
            search_terms = [
                f"{company_name} sustainability report {year} filetype:pdf",
                f"{company_name} corporate responsibility report {year} filetype:pdf",
                f"{company_name} ESG report {year} filetype:pdf"  # Added ESG variation
            ]

            for search_term in search_terms:
                try:
                    response = requests.get(
                        self.base_url,
                        headers=self.headers,
                        params={"q": search_term, "count": MAX_RESULTS_PER_SEARCH},
                        timeout=30  # Add timeout
                    )
                    response.raise_for_status()
                    results = response.json()

                    if results.get("web", {}).get("results"):
                        for result_data in results["web"]["results"]:
                            raw_title = result_data.get("title", "")
                            url = result_data["url"]
                            title = raw_title.strip().lower()

                            # Quick check for obvious non-reports
                            if any(bad_term in title.lower() for bad_term in self.negative_patterns):
                                logging.info(f"Skipping likely non-report: {url}")
                                continue

                            # Keep the year check
                            year_present = str(year) in title
                            if year_present:
                                logging.info(f"Found candidate report: {url}")
                                
                                # Use document handler with retry
                                for attempt in range(3):  # Add retry logic
                                    try:
                                        text_content = self.document_handler.get_document_content(url)
                                        if text_content and self.scope_1_pattern.search(text_content):
                                            logging.info(f"'scope 1' found in {url}")
                                            return {
                                                "url": url,
                                                "title": raw_title,
                                                "year": year
                                            }
                                        else:
                                            logging.info(f"'scope 1' not found in {url}, trying next result...")
                                        break  # Exit retry loop if we got content
                                    except Exception as e:
                                        if attempt == 2:  # Last attempt
                                            logging.error(f"Failed to access {url} after 3 attempts: {str(e)}")
                                        else:
                                            logging.warning(f"Attempt {attempt + 1} failed, retrying...")

                except requests.RequestException as e:
                    logging.error(f"Network error in search '{search_term}': {str(e)}")
                except Exception as e:
                    logging.error(f"Unexpected error in search '{search_term}': {str(e)}")

            logging.info(f"No suitable {year} report with 'scope 1' found for {company_name}, checking next available year...")

        logging.warning("No official sustainability report found that mentions 'scope 1'")
        return None
