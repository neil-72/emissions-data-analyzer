import os
from pathlib import Path
from datetime import datetime

# Base directories
BASE_DIR = Path(__file__).parent.parent
DEFAULT_OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)

# API Settings
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')

# Logging settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Rate limiting
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Cache settings
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# PDF Processing
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50MB
PDF_TIMEOUT = 30  # seconds

# Search settings
SEARCH_YEARS = [
    datetime.now().year,     # 2024
    datetime.now().year - 1, # 2023
    datetime.now().year - 2  # 2022 - some companies' latest is still 2022
]
MAX_RESULTS_PER_SEARCH = 5
MAX_REPORT_AGE_YEARS = 4

# Unit conversion settings
DEFAULT_UNIT = 'metric tons CO2e'
VALID_UNITS = [
    'metric tons CO2e',
    'tonnes CO2e',
    'tCO2e',
    'million metric tons CO2e',
    'kilotons CO2e',
    'short tons CO2e'
]
