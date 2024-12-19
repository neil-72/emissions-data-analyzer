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
    # Handles searching for sustainability reports using the Brave Search API.
    #
    # Key Features:
    # - Searches for PDFs using company name and year.
    # - Checks a blacklist of URLs before processing (to skip known bad or empty reports).
    # - Validates that the PDF contains emissions data (Scope 1 mentioned) before returning.
    # - Filters out documents that are clearly not sustainability reports (e.g. proxy statements).
    #
    # The idea is to find at least one PDF that seems like a sustainability report for the requested company and year,
    # and that contains at least a mention of Scope 1 emissions. If found, we return that PDF's URL and year.
    #
    # If no such report is found after searching multiple years and results, we return None.
    """

    def __init__(self):
        # ###########################################################################################################
        # Store the Brave API key and base URL. These are used for the HTTP requests to Brave's search API.
        # ###########################################################################################################
        self.api_key = BRAVE_API_KEY
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.headers = {
            "Accept": "*/*",
            "x-subscription-token": self.api_key
        }

        # Initialize the DocumentHandler, which we use to extract text from PDFs
        self.document_handler = DocumentHandler()
        
        # ###########################################################################################################
        # Load the blacklist file (if it exists) to skip known non-useful URLs.
        # This helps us avoid re-processing PDFs that we previously determined have no useful emissions data.
        #
        # We'll store all blacklisted URLs in a set for quick membership checks.
        # ###########################################################################################################
        self.blacklisted_urls = set()
        blacklist_file = "blacklisted_urls.txt"
        if os.path.exists(blacklist_file):
            with open(blacklist_file, "r", encoding="utf-8") as f:
                for line in f:
                    url_line = line.strip()
                    # Ignore empty lines or lines starting with '#', which we may use for comments.
                    if url_line and not url_line.startswith("#"):
                        self.blacklisted_urls.add(url_line)

        # ###########################################################################################################
        # A regex pattern to detect references to "Scope 1" in the extracted text.
        # If the PDF does not mention Scope 1, we consider it not useful for our analysis.
        # ###########################################################################################################
        self.scope_1_pattern = re.compile(r'(?i)scope[\s\-_]*1')
        
        # ###########################################################################################################
        # Negative patterns help us filter out known documents that are not sustainability reports.
        # For example, proxy statements, 10-K forms, and financial results are usually not sustainability reports.
        # ###########################################################################################################
        self.negative_patterns = [
            'proxy statement',
            '10-k',
            '10k',
            'financial results'
        ]

        # ###########################################################################################################
        # Track the last PDF URL that failed due to no emissions data.
        # If all searches fail, the caller (main code) could use this info to blacklist the last tried URL 
        # that had no data.
        # ###########################################################################################################
        self.last_failed_url = None

    def search_sustainability_report(self, company_name: str) -> Optional[Dict]:
        """
        # Search for a sustainability report PDF for a given company.
        #
        # Process:
        # 1. We try each year in SEARCH_YEARS (defined in config).
        # 2. For each year, we query Brave Search for a PDF with keywords like: "<company> global sustainability report <year> filetype:pdf"
        # 3. We get a list of results. For each result:
        #    - Skip if URL is blacklisted (known bad URL from previous attempts).
        #    - Skip if the title suggests it's a non-report (e.g., a proxy statement).
        #    - Download the PDF and extract text.
        #    - Check if the text contains "Scope 1".
        #      If yes, this likely is a sustainability report with emissions data, so we return this URL and year.
        #      If no, we log that no emissions data was found and note this URL as the last_failed_url.
        #
        # If we exhaust all results for all years and find no suitable report, we return None.
        #
        # By returning None, the caller knows that no good PDF was found.
        """

        logging.info(f"\n{'='*50}")
        logging.info(f"Starting search for {company_name}'s sustainability report")
        logging.info(f"{'='*50}")

        # If the user doesn't provide a company name, there's nothing to search.
        if not company_name.strip():
            logging.error("Empty company name provided")
            return None

        # Iterate over the configured search years (e.g., 2024, 2023, etc.)
        for year in SEARCH_YEARS:
            logging.info(f"\nTrying year: {year}")
            search_term = f"{company_name} global sustainability report {year} filetype:pdf"
            logging.info(f"Search query: {search_term}")

            try:
                logging.info("Making request to Brave Search API...")
                # Perform the HTTP request to Brave API
                response = requests.get(
                    self.base_url,
                    headers=self.headers,
                    params={"q": search_term, "count": MAX_RESULTS_PER_SEARCH},
                    timeout=30
                )
                
                if response.status_code == 200:
                    # Parse JSON response
                    results = response.json()
                    web_results = results.get("web", {}).get("results", [])

                    if web_results:
                        logging.info(f"Found {len(web_results)} potential results")
                        
                        # Check each result one by one
                        for idx, result_data in enumerate(web_results, 1):
                            url = result_data["url"]
                            logging.info(f"\nChecking result {idx}: {url}")

                            # Skip if URL is blacklisted
                            if url in self.blacklisted_urls:
                                logging.info(f"Skipping blacklisted URL: {url}")
                                continue
                            
                            # Skip if title suggests it's not a sustainability report
                            if any(bad_term in result_data.get("title", "").lower() for bad_term in self.negative_patterns):
                                logging.info("Skipping (appears to be non-report document)")
                                continue

                            # Validate that the PDF contains emissions data
                            logging.info("Validating document contains emissions data...")
                            try:
                                text_content = self.document_handler.get_document_content(url)
                                if text_content:
                                    logging.info(f"Successfully extracted {len(text_content):,} characters")
                                    
                                    # Check for Scope 1 mention
                                    if self.scope_1_pattern.search(text_content):
                                        logging.info("✓ Found emissions data references")
                                        return {"url": url, "year": year}
                                    else:
                                        logging.info("✗ No emissions data found")
                                        # Record this URL as the last failed URL
                                        self.last_failed_url = url
                            except Exception as e:
                                # If something goes wrong with PDF processing, log it and move on.
                                logging.error(f"Failed to process PDF: {str(e)}")

                else:
                    # If Brave search returned an error status, log it.
                    logging.error(f"Search API error: {response.status_code}")

            except Exception as e:
                # If the HTTP request or processing failed, log and try next year
                logging.error(f"Search error: {str(e)}")

            logging.info(f"No suitable {year} report found for {company_name}")

        # If we reach here, it means we tried all years and didn't find a suitable report.
        logging.warning(f"\nNo sustainability report found for {company_name}")
        return None