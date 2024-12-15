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
        """Search specifically for official company sustainability reports."""
        if not company_name.strip():
            logging.error("Empty company name provided")
            return None

        for year in SEARCH_YEARS:
            logging.info(f"Searching for {company_name} {year} sustainability report...")

            search_terms = [
                f"{company_name} sustainability report {year} filetype:pdf",
                f"{company_name} corporate responsibility report {year} filetype:pdf",
                f"{company_name} ESG report {year} filetype:pdf",
                f"{company_name} environmental report {year} filetype:pdf"
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
                        for result in results["web"]["results"]:
                            raw_title = result.get("title", "")
                            url = result["url"]

                            # Normalize the title
                            title = raw_title.strip().lower()
                            logging.debug(f"Raw title: '{raw_title}' | Normalized title: '{title}'")

                            # Validate the year is in the title
                            if str(year) in title and company_name.lower() in title:
                                logging.info(f"Found valid report: {url}")
                                return {
                                    "url": url,
                                    "title": raw_title,
                                    "year": year
                                }

                            logging.info(f"Skipping result: Year {year} not in title '{raw_title}'")

                except requests.RequestException as e:
                    logging.error(f"Network error in search '{search_term}': {str(e)}")
                    continue
                except Exception as e:
                    logging.error(f"Unexpected error in search '{search_term}': {str(e)}")
                    continue

        logging.warning("No official sustainability report found")
        return None
