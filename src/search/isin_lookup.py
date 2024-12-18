import requests
from bs4 import BeautifulSoup
import logging
from typing import Optional

class ISINLookup:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_company_name(self, isin: str) -> Optional[str]:
        """Convert ISIN to company name using Yahoo Finance."""
        try:
            if not self._validate_isin(isin):
                logging.error(f"Invalid ISIN format: {isin}")
                return None

            # First try to find the Yahoo Finance symbol
            symbol = self._find_yahoo_symbol(isin)
            if not symbol:
                return None

            # Get company details from the symbol page
            url = f"https://finance.yahoo.com/quote/{symbol}"
            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # The company name is usually in the h1 tag
            h1_element = soup.find('h1')
            if h1_element:
                # Clean up the company name (remove Inc., Corp., etc.)
                company_name = h1_element.text.split('(')[0].strip()
                return company_name

            return None

        except Exception as e:
            logging.error(f"Error looking up ISIN {isin}: {str(e)}")
            return None

    def _validate_isin(self, isin: str) -> bool:
        """Basic ISIN format validation."""
        if not isin or not isinstance(isin, str):
            return False

        # ISIN format: 2 letters followed by 10 alphanumeric characters
        isin = isin.strip().upper()
        if len(isin) != 12:
            return False

        if not isin[:2].isalpha():
            return False

        if not isin[2:].isalnum():
            return False

        return True

    def _find_yahoo_symbol(self, isin: str) -> Optional[str]:
        """Find Yahoo Finance symbol for an ISIN."""
        try:
            # Search for the ISIN
            search_url = f"https://finance.yahoo.com/lookup?s={isin}"
            response = self.session.get(search_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for the first search result
            table = soup.find('table')
            if table:
                first_row = table.find('tr', {'class': 'simpTblRow'})
                if first_row:
                    symbol_cell = first_row.find('td')
                    if symbol_cell:
                        return symbol_cell.text.strip()

            return None

        except Exception as e:
            logging.error(f"Error finding Yahoo symbol for ISIN {isin}: {str(e)}")
            return None
