# Technical Documentation

## Project Structure

```
emissions-data-analyzer/
├── src/
│   ├── analysis/           # Claude AI analysis
│   │   ├── __init__.py
│   │   └── claude_analyzer.py
│   ├── extraction/         # PDF handling
│   │   ├── __init__.py
│   │   └── pdf_handler.py
│   ├── isin/              # ISIN lookup
│   │   ├── __init__.py
│   │   └── isin_lookup.py
│   ├── search/            # Report search
│   │   ├── __init__.py
│   │   └── brave_search.py
│   └── web/               # Web interface
│       ├── __init__.py
│       ├── app.py
│       ├── static/
│       └── templates/
├── output/                # Generated JSON files
├── cache/                 # PDF and search cache
├── tests/                 # Unit tests
│   ├── __init__.py
│   └── test_isin_lookup.py
├── .env                   # API keys (not in repo)
├── .env.example           # API key template
├── requirements.txt       # Dependencies
└── README.md             # Project overview
```

## Configuration

### Environment Variables
```bash
# Required API Keys
CLAUDE_API_KEY=your_claude_api_key
BRAVE_API_KEY=your_brave_api_key

# Flask Configuration
FLASK_APP=src.web.app
FLASK_ENV=development  # Use 'production' in production

# Optional
LOG_LEVEL=INFO  # DEBUG for more verbose logging
```

### Development Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
flask run --port=5002

# If port is in use
flask run --port=5003
```

### Production Deployment
```bash
# Using gunicorn with specific port
gunicorn -w 4 'src.web.app:app' --bind 0.0.0.0:5002
```

## Core Components

### 1. Search (src/search/brave_search.py)
- Finds sustainability reports using Brave Search API
- Filters for PDFs and recent reports
- Handles rate limiting and retries

Main method:
```python
def search_sustainability_report(self, company_name: str) -> Optional[Dict]:
    """Find latest sustainability report."""
```

### 2. PDF Processing (src/extraction/pdf_handler.py)
- Extracts text and tables from PDFs
- Handles complex layouts and formats
- Preserves document structure

Main method:
```python
def get_document_content(self, url: str) -> Optional[str]:
    """Download and extract text from PDF"""
```

### 3. Analysis (src/analysis/claude_analyzer.py)
- Uses Claude API to find emissions data
- Extracts current and historical data
- Validates and standardizes units

Main method:
```python
def extract_emissions_data(self, text_content: str, company_name: str) -> Optional[Dict]:
    """Extract and validate emissions data"""
```

### 4. ISIN Support (src/isin/isin_lookup.py)
- Validates ISIN format using Luhn algorithm
- Looks up company info via Yahoo Finance
- Real-time validation in web interface

Key methods:
```python
def validate_isin(self, isin: str) -> bool:
    """Validate ISIN format and checksum"""

def get_company_info(self, isin: str) -> Optional[Dict]:
    """Get company details from ISIN"""
```

## Testing

```bash
# Run all tests
python -m pytest

# Run with coverage report
python -m pytest --cov=src tests/
```

## Common Issues & Solutions

### Port Already in Use
```bash
# Check what's using the port (on macOS/Linux)
lsof -i :5000

# Kill the process
pkill -f flask

# Or use a different port
flask run --port=5003
```

### PDF Processing Issues
- Some scanned PDFs may not be readable
- Very large PDFs (>50MB) may timeout
- Complex tables may not parse correctly

### API Rate Limits
- Brave Search: 10 requests/minute
- Claude API: Depends on plan
- Yahoo Finance: No official limits

## Data Processing

### Supported Units
The system automatically converts these to metric tons CO2e:
- Metric tons (tonnes) CO2e
- Million metric tons CO2e
- Kilotons CO2e
- Short tons CO2e

### Report Sections
Priority areas for data extraction:
1. GHG Emissions tables
2. Environmental Performance sections
3. ESG Metrics
4. Climate Change sections

## Future Improvements

1. **Features**
   - Scope 3 emissions support
   - Better unit conversion
   - Historical data tracking

2. **Technical**
   - Database caching
   - Asynchronous processing
   - Better error handling

3. **UI/UX**
   - Progress tracking
   - Data visualization
   - Bulk processing