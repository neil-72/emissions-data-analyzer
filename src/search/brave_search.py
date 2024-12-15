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
        """Search for a company's sustainability report using multiple approaches."""
        search_queries = [
            (f"{company_name} sustainability report", 2024),
            (f"{company_name} CDP climate change response", 2023),
            (f"{company_name} ESG report", 2024),
            (f"{company_name} scope 1 scope 2 emissions data", 2024),
            (f"{company_name} corporate responsibility report", 2024)
        ]

        all_results = []
        for base_query, year in search_queries:
            try:
                response = requests.get(
                    self.base_url,
                    headers=self.headers,
                    params={"q": base_query, "count": 15}
                )
                response.raise_for_status()
                results = response.json()

                if results.get("web", {}).get("results"):
                    all_results.extend([
                        {
                            "url": r["url"],
                            "title": r["title"],
                            "year": year,
                            "description": r.get("description", ""),
                            "score": self._calculate_relevance_score(r, company_name)
                        }
                        for r in results["web"]["results"]
                    ])

            except Exception as e:
                print(f"Error in search {base_query}: {str(e)}")
                continue

        # Sort by relevance score and filter
        relevant_results = [r for r in all_results if r["score"] > 0.5]
        if not relevant_results:
            return None

        # Return the most relevant result
        return max(relevant_results, key=lambda x: x["score"])

    def _calculate_relevance_score(self, result: Dict, company_name: str) -> float:
        """Calculate relevance score for a search result."""
        score = 0.0
        url = result["url"].lower()
        title = result["title"].lower()
        description = result.get("description", "").lower()

        # Company name matching
        if company_name.lower() in url:
            score += 0.3

        # Domain authority
        if any(domain in url for domain in [".com", ".org", ".net"]):
            score += 0.1

        # Content indicators
        keywords = ["sustainability", "esg", "responsibility", "cdp", "climate", "emissions", "scope"]
        for keyword in keywords:
            if keyword in url:
                score += 0.1
            if keyword in title:
                score += 0.05
            if keyword in description:
                score += 0.025

        # File type bonus
        if url.endswith(".pdf"):
            score += 0.2

        return min(score, 1.0)