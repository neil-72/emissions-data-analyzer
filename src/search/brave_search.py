import requests
from typing import Dict, Optional
import logging
from ..config import (
    BRAVE_API_KEY, 
    SEARCH_YEARS, 
    MAX_RESULTS_PER_SEARCH
)

class BraveSearchClient:
    def __init__(self):
        self.api_key = BRAVE_API_KEY
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }

    def search_sustainability_report(self, company_name: str) -> Optional[Dict]:
        """Search for a sustainability report PDF, preferring more recent years."""
        if not company_name.strip():
            logging.error("Empty company name provided")
            return None

        for year in SEARCH_YEARS:
            logging.info(f"Searching for {company_name} {year} sustainability report...")

            search_terms = [
                f"{company_name} sustainability report {year} filetype:pdf",
                f"{company_name} corporate responsibility report {year} filetype:pdf"
            ]

            found_for_this_year = False
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
                        for result in results["web"]["results"]:
                            raw_title = result.get("title", "")
                            url = result["url"]
                            title = raw_title.strip().lower()

                            year_present = str(year) in title
                            if year_present:
                                logging.info(f"Found valid report: {url}")
                                return {
                                    "url": url,
                                    "title": raw_title,
                                    "year": year
                                }
                            else:
                                logging.info(f"Skipping result: Missing year {year} in title '{raw_title}'")
                except requests.RequestException as e:
                    logging.error(f"Network error in search '{search_term}': {str(e)}")
                except Exception as e:
                    logging.error(f"Unexpected error in search '{search_term}': {str(e)}")

            if not found_for_this_year:
                logging.info(f"No suitable {year} report found for {company_name}, checking next available year...")

        logging.warning("No official sustainability report found")
        return None
