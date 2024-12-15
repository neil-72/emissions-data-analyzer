import requests
from typing import Dict, Optional
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
        for year in SEARCH_YEARS:
            query = f"{company_name} sustainability report {year} pdf"
            
            try:
                response = requests.get(
                    self.base_url,
                    headers=self.headers,
                    params={"q": query, "count": 5}
                )
                response.raise_for_status()
                
                results = response.json()
                
                if results.get("web", {}).get("results"):
                    for result in results["web"]["results"]:
                        if any(term in result["url"].lower() 
                               for term in ["sustainability", "esg", "report"]):
                            return {
                                "url": result["url"],
                                "title": result["title"],
                                "year": year,
                                "description": result.get("description", "")
                            }
            
            except requests.RequestException as e:
                print(f"Error searching for {company_name} {year} report: {str(e)}")
                continue
        
        return None