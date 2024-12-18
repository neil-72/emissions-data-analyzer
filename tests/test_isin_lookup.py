import unittest
from src.isin.isin_lookup import ISINLookup

class TestISINLookup(unittest.TestCase):
    def setUp(self):
        self.lookup = ISINLookup()

    def test_validate_isin_valid(self):
        # Test valid ISIN
        valid_isin = "US67066G1040"  # Nvidia
        self.assertTrue(self.lookup.validate_isin(valid_isin))

    def test_validate_isin_invalid_length(self):
        # Test invalid length
        invalid_isin = "US67066"
        self.assertFalse(self.lookup.validate_isin(invalid_isin))

    def test_validate_isin_invalid_chars(self):
        # Test invalid characters
        invalid_isin = "US67066G104$"
        self.assertFalse(self.lookup.validate_isin(invalid_isin))

    def test_validate_isin_invalid_country(self):
        # Test invalid country code
        invalid_isin = "12ABCDEFGHIJ"
        self.assertFalse(self.lookup.validate_isin(invalid_isin))

if __name__ == '__main__':
    unittest.main()