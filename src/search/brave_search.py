import requests
from typing import Dict, List, Optional
from ..config import BRAVE_API_KEY, SEARCH_YEARS

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
        # Start with most recent year
        for year in [2024, 2023]:
            print(f"Searching for {company_name} {year} sustainability report...")
            
            # Try different report naming conventions
            search_terms = [
                f"{company_name} sustainability report {year} filetype:pdf",
                f"{company_name} corporate responsibility report {year} filetype:pdf",
                f"{company_name} ESG report {year} filetype:pdf"
            ]
            
            for search_term in search_terms:
                try:
                    response = requests.get(
                        self.base_url,
                        headers=self.headers,
                        params={"q": search_term, "count": 5}
                    )
                    response.raise_for_status()
                    results = response.json()

                    if results.get("web", {}).get("results"):
                        for result in results["web"]["results"]:
                            url = result["url"].lower()
                            # Only consider PDFs from company domains
                            if (
                                company_name.lower() in url 
                                and url.endswith('.pdf')
                                and any(domain in url for domain in [".com", ".org", ".net"])
                            ):
                                print(f"Found potential report: {result['url']}")
                                return {
                                    "url": result["url"],
                                    "title": result["title"],
                                    "year": year,
                                    "description": result.get("description", "")
                                }

                except Exception as e:
                    print(f"Error in search {search_term}: {str(e)}")
                    continue

        print("No official sustainability report found")
        return None