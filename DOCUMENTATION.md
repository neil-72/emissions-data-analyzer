# Emissions Data Analyzer - Technical Documentation

## Overview
This tool automatically extracts Scope 1 and Scope 2 carbon emissions data from company sustainability reports using a combination of Brave Search API for document discovery and Claude AI for data extraction.

## System Components

### 1. Search Module (`src/search/brave_search.py`)
- **Purpose**: Finds company sustainability reports using Brave Search API
- **Key Features**:
  - Multiple search strategies (sustainability reports, CDP responses, ESG reports)
  - Relevance scoring for results
  - Filtering for official company domains
- **Main Class**: `BraveSearchClient`
  - `search_sustainability_report()`: Primary method for finding reports
  - `_calculate_relevance_score()`: Ranks search results

### 2. Document Processing (`src/extraction/pdf_handler.py`)
- **Purpose**: Extracts text from PDFs and webpages
- **Key Features**:
  - Handles both PDF and HTML content
  - Retry logic for failed downloads
  - Alternative URL generation
  - Web archive fallback
- **Main Class**: `DocumentHandler`
  - `extract_text_from_pdf()`: PDF processing with retries
  - `extract_text_from_webpage()`: HTML processing
  - `get_document_content()`: Main entry point

### 3. Data Analysis (`src/analysis/claude_analyzer.py`)
- **Purpose**: Extracts emissions data using Claude AI
- **Key Features**:
  - Structured data extraction
  - Handles multiple years of data
  - Provides context and trends
- **Main Class**: `EmissionsAnalyzer`
  - `extract_emissions_data()`: Processes text and returns structured data

### 4. Main Application (`src/main.py`)
- **Purpose**: Orchestrates the entire process
- **Key Features**:
  - End-to-end processing pipeline
  - Error handling
  - Results storage
- **Main Class**: `EmissionsTracker`
  - `process_company()`: Primary method for processing a company

## Data Flow
1. User inputs company name
2. System searches for sustainability report
3. Downloads and extracts text from found document
4. Analyzes text for emissions data
5. Returns structured results

## Output Format
```json
{
    "company": "string",
    "report_url": "string",
    "report_year": number,
    "emissions_data": {
        "scope_1": {
            "value": number,
            "unit": "string",
            "year": number
        },
        "scope_2": {
            "value": number,
            "unit": "string",
            "year": number
        },
        "context": "string"
    }
}
```

## Environment Setup
1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create .env file with API keys:
```env
CLAUDE_API_KEY=your_claude_api_key
BRAVE_API_KEY=your_brave_api_key
```

## Usage
```python
from src.main import EmissionsTracker

tracker = EmissionsTracker()
result = tracker.process_company("Company Name")
print(result)
```

## Error Handling
- PDF Access Errors: System tries alternative URLs and web archive
- Network Issues: Implements retry logic with exponential backoff
- Parse Errors: Graceful fallback with detailed error reporting

## Known Limitations
1. Some companies block PDF downloads
2. Report formats vary significantly
3. Historical data may be inconsistent
4. Some reports may require OCR (not implemented)

## Extension Points
1. Add OCR capabilities
2. Implement more data sources
3. Add data validation
4. Create web interface

## Debugging Tips
1. Check .env file configuration
2. Verify API keys are valid
3. Monitor console output for detailed logs
4. Check network connectivity
5. Verify Python version (3.8+ required)

## Maintenance Notes
- Update API keys regularly
- Monitor rate limits
- Check for updated report formats
- Review search terms periodically