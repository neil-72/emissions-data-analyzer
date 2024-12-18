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
    """# Handles searching for sustainability reports using Brave Search
    # Features:
    # - Searches for PDFs using company name and year
    # - Validates documents contain emissions data
    # - Filters out non-sustainability reports
    """
    def __init__(self):
        self.api_key = BRAVE_API_KEY
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        self.document_handler = DocumentHandler()
        
        # Pattern to validate scope 1 mentions
        self.scope_1_pattern = re.compile(r'(?i)scope[\s\-_]*1')
        
        # Filter obvious non-reports
        self.negative_patterns = [
            'proxy statement',
            '10-k',
            '10k',
            'financial results'
        ]

    def search_sustainability_report(self, company_name: str) -> Optional[Dict]:
        """# Search for a sustainability report PDF
        # Process:
        # 1. Try most recent year first
        # 2. Search multiple variations of report name
        # 3. Validate PDF has scope 1 mentions
        # 4. Return URL and year if found
        """
        if not company_name.strip():
            logging.error("Empty company name provided")
            return None

        for year in SEARCH_YEARS:
            logging.info(f"Searching for {company_name} {year} sustainability report...")
            
            search_term = f"{company_name} sustainability report {year} filetype:pdf"

            try:
                response = requests.get(
                    self.base_url,
                    headers=self.headers,
                    params={"q": search_term, "count": MAX_RESULTS_PER_SEARCH},
                    timeout=30
                )
                response.raise_for_status()
                results = response.json()

                if results.get("web", {}).get("results"):
                    for result_data in results["web"]["results"]:
                        raw_title = result_data.get("title", "")
                        url = result_data["url"]
                        title = raw_title.strip().lower()

                        # Skip obvious non-reports
                        if any(bad_term in title.lower() for bad_term in self.negative_patterns):
                            logging.info(f"Skipping likely non-report: {url}")
                            continue

                        if str(year) in title:
                            logging.info(f"Found candidate report: {url}")
                            
                            # Validate PDF contains scope 1 data
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
                                    logging.info(f"'scope 1' not found in {url}")
                            except Exception as e:
                                logging.error(f"Failed to access {url}: {str(e)}")

            except requests.RequestException as e:
                logging.error(f"Network error: {str(e)}")
            except Exception as e:
                logging.error(f"Unexpected error: {str(e)}")

            logging.info(f"No suitable {year} report found for {company_name}")

        logging.warning(f"No sustainability report found for {company_name}")
        return None
