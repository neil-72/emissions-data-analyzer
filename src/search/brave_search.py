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
        # Regex to detect "scope 1" in various formats (e.g., "Scope   1", "Scope-1", "scope1", etc.)
        self.scope_1_pattern = re.compile(r'(?i)scope[\s\-_]*1')

    def search_sustainability_report(self, company_name: str) -> Optional[Dict]:
        """Search for a sustainability report PDF, preferring more recent years and ensuring 'scope 1' mention."""
        if not company_name.strip():
            logging.error("Empty company name provided")
            return None

        for year in SEARCH_YEARS:
            logging.info(f"Searching for {company_name} {year} sustainability report...")

            search_terms = [
                f"{company_name} sustainability report {year} filetype:pdf",
                f"{company_name} corporate responsibility report {year} filetype:pdf"
            ]

            for search_term in search_terms:
                try:
                    response = requests.get(
                        self.base_url,
                        headers=self.headers,
                        params={"q": search_term, "count": MAX_RESULTS_PER_SEARCH}
                    )
                    response.raise_for_status()
                    results = response.json()

                    if results.get("web", {}).get("results"):
                        for result_data in results["web"]["results"]:
                            raw_title = result_data.get("title", "")
                            url = result_data["url"]
                            title = raw_title.strip().lower()

                            year_present = str(year) in title
                            if year_present:
                                logging.info(f"Found candidate report: {url}")
                                # Extract text to check for scope 1 mention
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
                except requests.RequestException as e:
                    logging.error(f"Network error in search '{search_term}': {str(e)}")
                except Exception as e:
                    logging.error(f"Unexpected error in search '{search_term}': {str(e)}")

            logging.info(f"No suitable {year} report with 'scope 1' found for {company_name}, checking next available year...")

        logging.warning("No official sustainability report found that mentions 'scope 1'")
        return None
