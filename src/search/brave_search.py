import requests
import logging
import re
import os
from typing import Dict, Optional
from ..config import (
    BRAVE_API_KEY, 
    SEARCH_YEARS, 
    MAX_RESULTS_PER_SEARCH
)
from ..extraction.pdf_handler import DocumentHandler


class BraveSearchClient:
    """ 
    Handles searching for sustainability reports using the Brave Search API.

    Key Features:
    - Searches for PDFs using company name and year.
    - Checks a blacklist of URLs before processing (to skip known bad or empty reports).
    - Validates that the PDF contains emissions data (Scope 1 mentioned) before returning.
    - Filters out documents that are clearly not sustainability reports (e.g. proxy statements).

    The idea is to find at least one PDF that seems like a sustainability report for the requested company and year,
    and that contains at least a mention of Scope 1 emissions. If found, we return that PDF's URL and year.

    If no such report is found after searching multiple years and results, we return None.
    """

    def __init__(self):
        # Store the Brave API key and base URL for HTTP requests
        self.api_key = BRAVE_API_KEY
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.headers = {
            "Accept": "*/*",
            "x-subscription-token": self.api_key
        }

        # Initialize the DocumentHandler to extract text from PDFs
        self.document_handler = DocumentHandler()
        
        # Load blacklist file (if it exists) to skip known non-useful URLs
        self.blacklisted_urls = set()
        blacklist_file = "blacklisted_urls.txt"
        if os.path.exists(blacklist_file):
            with open(blacklist_file, "r", encoding="utf-8") as f:
                for line in f:
                    url_line = line.strip()
                    if url_line and not url_line.startswith("#"):
                        self.blacklisted_urls.add(url_line)

        # Regex to detect Scope 1 emissions references in extracted PDF text
        self.scope_1_pattern = re.compile(r'(?i)scope[\s\-_]*1')
        
        # Negative patterns to filter out non-sustainability reports
        self.negative_patterns = [
            'proxy statement',
            '10-k',
            '10k',
            'financial results',
            'basis of preparation',
            'methodology',
            'reporting framework',
            'calculation methodology',
            'reporting guidelines',
            'basis for reporting',
            'calculation guide',
            'data preparation',
            'reporting criteria',
            'accounting methodology'
        ]

        # Track the last PDF URL that failed due to no emissions data
        self.last_failed_url = None

    def search_sustainability_report(self, company_name: str) -> Optional[Dict]:
        logging.info(f"\n{'='*50}")
        logging.info(f"Starting search for {company_name}'s sustainability report")
        logging.info(f"{'='*50}")

        if not company_name.strip():
            logging.error("Empty company name provided")
            return None

        for year in SEARCH_YEARS:
            logging.info(f"\nTrying year: {year}")
            search_term = f"{company_name} global sustainability report {year} filetype:pdf"
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
                    web_results = results.get("web", {}).get("results", [])

                    if web_results:
                        logging.info(f"Found {len(web_results)} potential results")
                        
                        for idx, result_data in enumerate(web_results, 1):
                            url = result_data["url"]
                            logging.info(f"\nChecking result {idx}: {url}")

                            # Skip if URL is blacklisted
                            if url in self.blacklisted_urls:
                                logging.info(f"Skipping blacklisted URL: {url}")
                                continue
                            
                            # Skip URLs with old dates (before 2022)
                            if re.search(r'\b(19\d{2}|20[0-1]\d|2020|2021)\b', url):
                                logging.info(f"Skipping (URL too old): {url}")
                                continue

                            # Check both the title and filename for negative patterns
                            filename = url.split('/')[-1].lower()
                            if any(
                                bad_term in result_data.get("title", "").lower()
                                or bad_term.replace(' ', '-') in filename
                                for bad_term in self.negative_patterns
                            ):
                                logging.info("Skipping (appears to be non-report document)")
                                continue

                            # Validate that the PDF contains emissions data
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
                                        self.last_failed_url = url
                            except Exception as e:
                                logging.error(f"Failed to process PDF: {str(e)}")

                else:
                    logging.error(f"Search API error: {response.status_code}")

            except Exception as e:
                logging.error(f"Search error: {str(e)}")

            logging.info(f"No suitable {year} report found for {company_name}")

        logging.warning(f"\nNo sustainability report found for {company_name}")
        return None
