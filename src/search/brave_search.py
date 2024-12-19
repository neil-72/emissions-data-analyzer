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
        logging.info(f"\n{'='*50}")
        logging.info(f"Starting search for {company_name}'s sustainability report")
        logging.info(f"{'='*50}")

        if not company_name.strip():
            logging.error("Empty company name provided")
            return None

        for year in SEARCH_YEARS:
            logging.info(f"\nTrying year: {year}")
            search_term = f"{company_name} sustainability report {year} filetype:pdf"
            logging.info(f"Search query: {search_term}")

            try:
                logging.info("Making request to Brave Search API...")
                response = requests.get(
                    self.base_url,
                    headers=self.headers,
                    params={"q": search_term, "count": MAX_RESULTS_PER_SEARCH},
                    timeout=30
                )
                
                if response.status_code == 200:
                    results = response.json()
                    if results.get("web", {}).get("results"):
                        logging.info(f"Found {len(results['web']['results'])} potential results")
                        
                        for idx, result_data in enumerate(results["web"]["results"], 1):
                            url = result_data["url"]
                            logging.info(f"\nChecking result {idx}: {url}")
                            
                            if any(bad_term in result_data.get("title", "").lower() for bad_term in self.negative_patterns):
                                logging.info("Skipping (appears to be non-report document)")
                                continue

                            logging.info("Validating document contains emissions data...")
                            try:
                                text_content = self.document_handler.get_document_content(url)
                                if text_content:
                                    logging.info(f"Successfully extracted {len(text_content):,} characters")
                                    if self.scope_1_pattern.search(text_content):
                                        logging.info("✓ Found emissions data references")
                                        return {"url": url, "year": year}
                                    else:
                                        logging.info("✗ No emissions data found")
                            except Exception as e:
                                logging.error(f"Failed to process PDF: {str(e)}")

                else:
                    logging.error(f"Search API error: {response.status_code}")

            except Exception as e:
                logging.error(f"Search error: {str(e)}")

            logging.info(f"No suitable {year} report found for {company_name}")

        logging.warning(f"\nNo sustainability report found for {company_name}")
        return None