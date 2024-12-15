import requests
from typing import Dict, List, Optional
import logging
from ..config import (
    BRAVE_API_KEY, 
    SEARCH_YEARS, 
    MAX_RESULTS_PER_SEARCH,
    VALID_DOMAINS
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
                            url = result["url"].lower()
                            
                            # Validate URL
                            if self._is_valid_report_url(url, company_name):
                                logging.info(f"Found potential report: {result['url']}")
                                return {
                                    "url": result["url"],
                                    "title": result["title"],
                                    "year": year,
                                    "description": result.get("description", "")
                                }

                except requests.RequestException as e:
                    logging.error(f"Network error in search '{search_term}': {str(e)}")
                    continue
                except Exception as e:
                    logging.error(f"Unexpected error in search '{search_term}': {str(e)}")
                    continue

        logging.warning("No official sustainability report found")
        return None

    def _is_valid_report_url(self, url: str, company_name: str) -> bool:
        """Validate if URL is likely an official company report."""
        url_lower = url.lower()
        company_lower = company_name.lower()
        
        return all([
            url_lower.endswith('.pdf'),
            company_lower in url_lower,
            any(domain in url_lower for domain in VALID_DOMAINS),
            not any(term in url_lower for term in ['linkedin', 'facebook', 'twitter'])
        ])
