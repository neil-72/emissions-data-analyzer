import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')

# Search Configuration
SEARCH_YEARS = [2024, 2023, 2022]  # Years to search for reports
RESULTS_PER_SEARCH = 10

# File Types
VALID_DOCUMENT_TYPES = ['.pdf', '.html', '.htm']

# Output Configuration
DEFAULT_OUTPUT_DIR = 'output'