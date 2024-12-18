# Emissions Data Analyzer - Technical Documentation

## Overview

This tool automatically extracts Scope 1 and Scope 2 carbon emissions data from company sustainability reports using the Brave Search API for document discovery and Claude AI for intelligent data extraction.

## System Components

### 1. Search Module (`src/search/brave_search.py`)
- **Purpose**: Locates company sustainability reports in PDF format.
- **Key Features**:
  - PDF-focused search with filetype filtering
  - Validation of documents for emissions content
  - Filtering of non-report documents (10-K, proxy statements)
  - Configurable search years
- **Main Class**: `BraveSearchClient`
  - `search_sustainability_report()`: Finds and validates sustainability reports
  - Built-in validation for Scope 1 mentions
  - Comprehensive error handling and logging

### 2. Document Processing (`src/extraction/pdf_handler.py`)
- **Purpose**: Extracts structured content from PDF reports.
- **Key Features**:
  - Multi-column text detection and handling
  - Table structure preservation
  - Content type tagging (TABLE, TEXT, DATA, HEADER)
  - Page number tracking
  - Size limit enforcement
- **Main Class**: `DocumentHandler`
  - `get_document_content()`: Main extraction method
  - `_extract_text_with_columns()`: Smart column handling
  - `_process_table()`: Table structure preservation
  - `_process_text()`: Text context preservation

### 3. Data Analysis (`src/analysis/claude_analyzer.py`)
- **Purpose**: Uses Claude AI to extract and structure emissions data.
- **Key Features**:
  - Uses Claude 3 Sonnet model
  - Text chunking for large documents
  - Unit normalization to metric tons CO2e
  - Historical data extraction
  - Source context preservation
- **Main Class**: `EmissionsAnalyzer`
  - `extract_emissions_data()`: Core extraction method
  - `_send_to_claude()`: AI interaction
  - `_parse_and_validate()`: Data validation
  - `_aggregate_results()`: Result combination

### 4. Main Application (`src/main.py`)
- **Purpose**: Orchestrates the analysis pipeline.
- **Key Features**:
  - Command-line interface
  - JSON output format
  - Error handling and logging
  - Clean exit handling
- **Main Class**: `EmissionsTracker`
  - `process_company()`: Main processing method
  - `_save_results()`: Result storage
  - Comprehensive error handling

## Data Processing Flow

1. **Input**: Company name
2. **Search**: Locate recent sustainability report PDFs
3. **Validation**: Verify document relevance
4. **Extraction**: Process PDF content
5. **Analysis**: Extract emissions data using AI
6. **Output**: Structured JSON with:
   - Current year emissions
   - Historical data
   - Source context
   - Processing metadata

## Output Format

```json
{
  "company": "Company Name",
  "report_url": "PDF URL",
  "report_year": "YYYY",
  "emissions_data": {
    "current_year": {
      "year": "YYYY",
      "scope_1": {
        "value": "number",
        "unit": "metric tons CO2e"
      },
      "scope_2_market_based": {
        "value": "number",
        "unit": "metric tons CO2e"
      },
      "scope_2_location_based": {
        "value": "number",
        "unit": "metric tons CO2e"
      }
    },
    "previous_years": [
      {
        "year": "YYYY",
        "scope_1": {},
        "scope_2_market_based": {},
        "scope_2_location_based": {}
      }
    ]
  },
  "processed_at": "ISO timestamp"
}
```

## Known Limitations

1. PDF-only support (no HTML processing)
2. Requires direct PDF access (no login walls)
3. English language focus
4. Resource-intensive for large reports
5. API key requirements (Brave Search and Claude)

## Setup Requirements

1. Python 3.8 or higher
2. Brave Search API key
3. Claude API key
4. Required Python packages:
   - requests
   - pdfplumber
   - anthropic
   - logging

## Error Handling

The system implements comprehensive error handling:
1. Network timeout protection
2. PDF validation
3. Content extraction fallbacks
4. AI response validation
5. Result aggregation checks

## Debugging Tips

1. Check API keys in configuration
2. Monitor logging output
3. Verify PDF accessibility
4. Check network connectivity
5. Validate input company names

## Future Development

Potential areas for enhancement:
1. Support for additional document formats
2. Multi-language support
3. Batch processing capability
4. Web interface development
5. Additional data source integration

## Maintenance

Regular maintenance tasks:
1. Update API keys as needed
2. Monitor API usage and limits
3. Update dependencies
4. Test with new report formats
5. Review and update logging