import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# API Keys
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')

if not CLAUDE_API_KEY or not BRAVE_API_KEY:
    raise ValueError("Missing required API keys in .env file")

# Search Configuration
SEARCH_YEARS = [2024, 2023]  # Years to search for reports
MAX_RESULTS_PER_SEARCH = 5

# Document Processing
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50MB limit
VALID_DOCUMENT_TYPES = ['.pdf', '.html', '.htm']

# Output Configuration
DEFAULT_OUTPUT_DIR = 'output'
