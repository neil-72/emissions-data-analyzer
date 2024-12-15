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
  - Page-level emissions data detection
- **Main Class**: `DocumentHandler`
  - `extract_text_from_pdf()`: PDF processing with retries and page markers
  - `extract_text_from_webpage()`: HTML processing
  - `get_document_content()`: Main entry point
  - `EMISSIONS_KEYWORDS`: List of key terms used to detect data

### Primary Sections
The system specifically looks for these terms when processing PDFs:
- Greenhouse Gas Emissions
- Climate Change + numbers
- Environmental Data + "scope"
- Direct/Indirect emissions
- CO2e metrics
- Year + numbers pattern

### Table Indicators
Common patterns that indicate valuable emissions data:
- Table headers with 'scope'
- Numeric sequences with units (tCO2e, MTCO2e)
- Year columns followed by numbers
- Indented number lists

### 3. Data Analysis (`src/analysis/claude_analyzer.py`)
- **Purpose**: Extracts emissions data using Claude AI
- **Key Features**:
  - Structured data extraction
  - Smart section targeting
  - Data validation
  - Multiple extraction strategies
- **Main Class**: `EmissionsAnalyzer`
  - `extract_emissions_data()`: Main extraction method
  - `_extract_relevant_sections()`: Targets key report sections
  - `_validate_emissions_data()`: Validates extracted data

### 4. Main Application (`src/main.py`)
- **Purpose**: Orchestrates the entire process
- **Key Features**:
  - End-to-end processing pipeline
  - Enhanced error handling
  - Results storage
  - Detailed logging
- **Main Class**: `EmissionsTracker`
  - `process_company()`: Primary method for processing a company

## Data Validation

### Validation Ranges
- **Scope 1**: 100 - 10,000,000 metric tons CO2e
- **Scope 2**: 1,000 - 20,000,000 metric tons CO2e

### Data Quality Checks
1. Numeric value validation
2. Unit format verification
3. Year format checking
4. Range validation
5. Cross-reference between scopes

## Target Sections

### Primary Sections
- Greenhouse Gas Emissions
- Climate Change
- Environmental Data
- Scope 1 and 2
- GHG Emissions
- Carbon Footprint

### Table Indicators
- Emissions Data
- GHG Data
- Environmental Performance
- Metrics and Targets

## Error Handling

### PDF Access Issues
1. Retry with exponential backoff
2. Try alternative URLs
3. Check web archive
4. Use alternative document formats

### Data Extraction Issues
1. Try targeted section extraction
2. Fall back to full document search
3. Look for alternative data sources
4. Check for table-specific formats

### Validation Issues
1. Check for unit conversion errors
2. Verify year alignment
3. Compare with typical ranges
4. Look for data entry patterns

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
