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
├── tests/                 # Unit tests
│   ├── __init__.py
│   └── test_isin_lookup.py
├── .env                   # API keys (not in repo)
├── .env.example           # API key template
├── .flaskenv             # Flask settings
├── requirements.txt       # Dependencies
└── README.md             # Project overview
```

## API Endpoints

### POST /analyze
Analyze emissions data for a company.

**Request:**
```json
{
  "identifier": "string",
  "id_type": "company|isin"
}
```

**Success Response (200):**
```json
{
  "company": "Nvidia",
  "emissions_data": {
    "current_year": {
      "scope_1": {
        "unit": "metric tons CO2e",
        "value": 14390
      },
      "scope_2_location_based": {
        "unit": "metric tons CO2e",
        "value": 178087
      },
      "scope_2_market_based": {
        "unit": "metric tons CO2e",
        "value": 40555
      },
      "year": 2024
    },
    "previous_years": [...],
    "source_details": {
      "context": "Data extracted from sustainability report",
      "location": "Pages 29-32, 39-40"
    }
  }
}
```

### GET /validate-isin/{isin}
Validate ISIN and get company info.

**Success Response (200):**
```json
{
  "valid": true,
  "company_name": "Nvidia Corporation",
  "sector": "Technology",
  "country": "United States"
}
```

**Error Responses:**
- 400: Invalid ISIN format
- 404: Company not found

## Core Components

### 1. PDF Handler (src/extraction/pdf_handler.py)
- Uses pdfplumber for text extraction
- Table structure recognition
- Error handling for corrupt PDFs

Main method:
```python
def get_document_content(self, url: str) -> Optional[str]:
    """Download and extract text from PDF"""
```

### 2. Claude Analyzer (src/analysis/claude_analyzer.py)
- Processes text to find emissions data
- Handles different report formats
- Unit standardization

Main method:
```python
def extract_emissions_data(self, text: str, company: str) -> Optional[Dict]:
    """Extract emissions data using Claude"""
```

### 3. ISIN Lookup (src/isin/isin_lookup.py)
- ISIN validation using Luhn algorithm
- Company info from Yahoo Finance
- Caching for performance

Key methods:
```python
def validate_isin(self, isin: str) -> bool:
    """Validate ISIN format and checksum"""

def get_company_info(self, isin: str) -> Optional[Dict]:
    """Get company details from ISIN"""
```

### 4. Brave Search (src/search/brave_search.py)
- Finds sustainability reports
- Handles API rate limits
- Result filtering

Main method:
```python
def search_sustainability_report(self, company: str) -> Optional[Dict]:
    """Find latest sustainability report"""
```

## Error Handling

1. **Input Validation**
   - Company name required
   - ISIN format validation
   - PDF URL validation

2. **API Errors**
   - Rate limit handling
   - Connection timeouts
   - Invalid responses

3. **Processing Errors**
   - PDF extraction failures
   - Data not found
   - Invalid unit formats

## Dependencies

Key packages:
- anthropic: Claude AI API
- pdfplumber: PDF processing
- yfinance: Company lookups
- Flask: Web interface
- requests: HTTP client
- pandas: Data handling

## Environment Variables

```bash
# Required
CLAUDE_API_KEY=your_claude_api_key
BRAVE_API_KEY=your_brave_api_key

# Optional
FLASK_ENV=development
FLASK_DEBUG=1
```

## Development

### Running Tests
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest
```

### Local Development
```bash
# Start Flask development server
flask run --debug

# Watch for file changes
flask run --debug --reload
```

## Production Deployment

```bash
# Using gunicorn
gunicorn -w 4 'src.web.app:app'
```

Recommended settings:
- 4+ worker processes
- Rate limiting enabled
- Error logging configured
- HTTPS required

## Data Processing

### Unit Conversions
Supported input formats:
- Metric tons (tonnes) CO2e
- Short tons CO2e
- Kilograms CO2e
- Million metric tons CO2e

### Report Sections
Priority areas for data extraction:
1. GHG Emissions tables
2. Environmental Performance
3. Climate Change sections
4. ESG Metrics

## Known Issues

1. **PDF Processing**
   - Some scanned PDFs unreadable
   - Complex tables may break
   - Large files slow to process

2. **Data Extraction**
   - Inconsistent unit formats
   - Missing historical data
   - Sector classification limited

3. **API Limits**
   - Brave Search rate limits
   - Claude API costs
   - Yahoo Finance timeouts

## Future Improvements

1. **Features**
   - Scope 3 emissions support
   - OCR for scanned PDFs
   - Better sector analysis

2. **Technical**
   - Database caching
   - Async processing
   - PDF text cleaning

3. **UI/UX**
   - Better error messages
   - Progress tracking
   - Data comparisons