from typing import Optional, Dict
import yfinance as yf
import requests
import logging
from functools import lru_cache

class ISINLookup:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_isin(self, isin: str) -> bool:
        """Validate ISIN using Luhn algorithm"""
        if not isin or len(isin) != 12:
            return False

        # Check first two chars are letters
        if not isin[:2].isalpha():
            return False

        # Check remaining chars are alphanumeric
        if not isin[2:].isalnum():
            return False

        # Convert letters to numbers (A=10, B=11, etc)
        nums = []
        for char in isin.upper():
            if char.isalpha():
                nums.append(str(ord(char) - ord('A') + 10))
            else:
                nums.append(char)

        # Luhn algorithm
        digits = ''.join(nums)
        checksum = 0
        double = True

        for digit in reversed(digits):
            d = int(digit)
            if double:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
            double = not double

        return checksum % 10 == 0

    @lru_cache(maxsize=1000)
    def get_company_info(self, isin: str) -> Optional[Dict]:
        """Get company information from ISIN using Yahoo Finance"""
        try:
            if not self.validate_isin(isin):
                return None

            # Convert ISIN to ticker symbol
            ticker = self._isin_to_ticker(isin)
            if not ticker:
                return None

            # Get company info
            company = yf.Ticker(ticker)
            info = company.info

            return {
                'name': info.get('longName'),
                'ticker': ticker,
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'country': info.get('country')
            }

        except Exception as e:
            self.logger.error(f"Error getting company info for {isin}: {str(e)}")
            return None

    def resolve_company_name(self, name: str) -> Optional[str]:
        """Try to find ISIN from company name"""
        try:
            # Search Yahoo Finance
            search_url = f"https://query2.finance.yahoo.com/v1/finance/search"
            params = {
                'q': name,
                'quotesCount': 1,
                'newsCount': 0
            }
            response = requests.get(search_url, params=params)
            data = response.json()

            if not data.get('quotes'):
                return None

            # Get first result ticker
            ticker = data['quotes'][0].get('symbol')
            if not ticker:
                return None

            # Convert ticker to ISIN
            return self._ticker_to_isin(ticker)

        except Exception as e:
            self.logger.error(f"Error resolving company name {name}: {str(e)}")
            return None

    def _isin_to_ticker(self, isin: str) -> Optional[str]:
        """Convert ISIN to Yahoo Finance ticker"""
        try:
            search_url = f"https://query2.finance.yahoo.com/v1/finance/search"
            params = {
                'q': isin,
                'quotesCount': 1,
                'newsCount': 0
            }
            response = requests.get(search_url, params=params)
            data = response.json()

            if not data.get('quotes'):
                return None

            return data['quotes'][0].get('symbol')

        except Exception as e:
            self.logger.error(f"Error converting ISIN to ticker {isin}: {str(e)}")
            return None

    def _ticker_to_isin(self, ticker: str) -> Optional[str]:
        """Convert ticker to ISIN"""
        try:
            company = yf.Ticker(ticker)
            info = company.info
            isin = info.get('isin')
            if isin and self.validate_isin(isin):
                return isin
            return None

        except Exception as e:
            self.logger.error(f"Error converting ticker to ISIN {ticker}: {str(e)}")
            return None