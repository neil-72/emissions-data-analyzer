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
        """Search for a company's sustainability report."""
        search_terms = [
            f"{company_name} sustainability report",
            f"{company_name} esg report",
            f"{company_name} corporate responsibility report"
        ]
        
        for year in SEARCH_YEARS:
            for search_term in search_terms:
                query = f"{search_term} {year}"
                print(f"Searching for: {query}")
                
                try:
                    response = requests.get(
                        self.base_url,
                        headers=self.headers,
                        params={
                            "q": query,
                            "count": 10  # Increased from 5
                        }
                    )
                    response.raise_for_status()
                    
                    results = response.json()
                    
                    if results.get("web", {}).get("results"):
                        for result in results["web"]["results"]:
                            url = result["url"].lower()
                            # Look for official company domains and relevant keywords
                            if (
                                company_name.lower() in url
                                and any(term in url for term in [".com", ".org", ".net"])
                                and any(term in url for term in ["sustainability", "esg", "responsibility", "report"])
                                and (url.endswith(".pdf") or "download" in url)
                            ):
                                return {
                                    "url": result["url"],
                                    "title": result["title"],
                                    "year": year,
                                    "description": result.get("description", "")
                                }
                
                except requests.RequestException as e:
                    print(f"Error searching for {query}: {str(e)}")
                    continue
        
        return None