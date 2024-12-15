# Emissions Data Analyzer - Technical Documentation

## Overview

This tool automatically extracts Scope 1 and Scope 2 carbon emissions data from company sustainability reports using a combination of the Brave Search API for document discovery and Claude AI for data extraction.

## System Components

### 1. Search Module (`src/search/brave_search.py`)
- **Purpose**: Finds company sustainability reports using the Brave Search API.
- **Key Features**:
  - Multiple search strategies for sustainability reports, CDP responses, and ESG reports.
  - Relevance scoring for search results.
  - Filtering for official company domains.
- **Main Class**: `BraveSearchClient`
  - `search_sustainability_report()`: Main method for locating reports.
  - `_calculate_relevance_score()`: Ranks search results based on relevance.

### 2. Document Processing (`src/extraction/pdf_handler.py`)
- **Purpose**: Extracts text from PDFs and webpages.
- **Key Features**:
  - Handles both PDF and HTML content.
  - Retry logic for failed downloads.
  - Alternative URL generation and web archive fallback.
  - Page-level emissions data detection.
- **Main Class**: `DocumentHandler`
  - `extract_text_from_pdf()`: Processes PDFs with retries and page markers.
  - `extract_text_from_webpage()`: Processes HTML documents.
  - `get_document_content()`: Main entry point for content extraction.
  - `EMISSIONS_KEYWORDS`: List of terms to detect relevant emissions data.

### 3. Data Analysis (`src/analysis/claude_analyzer.py`)
- **Purpose**: Extracts emissions data using Claude AI.
- **Key Features**:
  - Structured data extraction.
  - Smart targeting of report sections.
  - Data validation and normalization.
  - Multiple extraction strategies.
- **Main Class**: `EmissionsAnalyzer`
  - `extract_emissions_data()`: Core method for extracting emissions data.
  - `_extract_relevant_sections()`: Targets critical sections of reports.
  - `_validate_emissions_data()`: Ensures extracted data meets quality standards.

### 4. Main Application (`src/main.py`)
- **Purpose**: Orchestrates the entire emissions data analysis pipeline.
- **Key Features**:
  - End-to-end report processing.
  - Robust error handling and retry mechanisms.
  - Results storage in standardized formats.
  - Detailed logging for debugging.
- **Main Class**: `EmissionsTracker`
  - `process_company()`: Main method for analyzing emissions data for a company.

## Data Validation

### Validation Ranges
- **Scope 1**: 100 - 10,000,000 metric tons CO2e.
- **Scope 2**: 1,000 - 20,000,000 metric tons CO2e.

### Data Quality Checks
1. Numeric value validation.
2. Unit format verification.
3. Year format checking.
4. Range validation against corporate benchmarks.
5. Cross-referencing Scope 1 and Scope 2 data for consistency.

## Target Sections

### Primary Sections
The system specifically targets the following report sections:
- Greenhouse Gas Emissions.
- Climate Change.
- Environmental Data.
- Scope 1 and 2.
- GHG Emissions.
- Carbon Footprint.

### Table Indicators
Key patterns that indicate relevant emissions data:
- Table headers containing 'scope' or 'emissions'.
- Numeric sequences with units such as tCO2e or MTCO2e.
- Year columns followed by numeric data.
- Indented lists of emissions figures.

## Error Handling

### PDF Access Issues
1. Retry failed downloads with exponential backoff.
2. Attempt alternative URLs for the report.
3. Use web archives to retrieve inaccessible documents.
4. Handle alternative document formats where available.

### Data Extraction Issues
1. Use targeted section extraction when possible.
2. Fall back to searching the full document.
3. Search for alternative emissions data sources within the report.
4. Detect and process table-specific formats for structured data.

### Validation Issues
1. Identify and correct unit conversion errors.
2. Verify alignment of extracted data with expected years.
3. Compare extracted data against corporate emissions benchmarks.
4. Search for common data patterns to ensure accuracy.

## Known Limitations
1. Some companies block PDF downloads or restrict access.
2. Report formats vary significantly across industries and regions.
3. Historical data may be inconsistent or incomplete.
4. Optical Character Recognition (OCR) for scanned PDFs is not currently implemented.

## Extension Points
1. Add OCR capabilities for processing scanned documents.
2. Incorporate additional data sources for emissions metrics.
3. Expand validation rules to include more comprehensive checks.
4. Develop a web-based interface for easier user interaction.

## Debugging Tips
1. Verify `.env` file configuration for API keys.
2. Check that the API keys (Claude and Brave) are active and valid.
3. Monitor console logs for detailed error messages and debugging information.
4. Ensure network connectivity for API requests.
5. Verify Python version compatibility (3.8 or higher is required).

## Maintenance Notes
1. Update API keys periodically to ensure uninterrupted access.
2. Monitor API rate limits for both Brave and Claude services.
3. Regularly review and update search terms to match evolving report formats.
4. Test the system with new reports to ensure compatibility with updated layouts.
