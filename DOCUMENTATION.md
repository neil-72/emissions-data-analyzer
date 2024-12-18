# Emissions Data Analyzer - Technical Documentation

## Overview

This tool extracts Scope 1 and Scope 2 carbon emissions data from company sustainability reports using Brave Search for report discovery and Claude AI for data extraction.

## System Components

### 1. Search Module (src/search/brave_search.py)
- **Purpose**: Locate company sustainability reports via the Brave Search API
- **Key Features**:
  - Searches for sustainability reports, ESG reports, and CDP disclosures
  - Implements multiple search strategies to improve result relevance
  - ISIN lookup and validation for accurate company identification
- **Main Class**: BraveSearchClient
  - search_sustainability_report(): Finds the most relevant sustainability report

### 2. Document Processing (src/extraction/pdf_handler.py)
- **Purpose**: Extract text and structure from sustainability reports
- **Key Features**:
  - Handles PDFs with table recognition and text extraction
  - Searches for keywords and patterns related to emissions
  - Includes fallback methods for inaccessible documents
- **Main Class**: DocumentHandler
  - get_document_content(): Extracts structured text from PDF files
  - extract_text_from_pdf(): Handles raw PDF processing

### 3. Data Analysis (src/analysis/claude_analyzer.py)
- **Purpose**: Extract emissions data from report text using Claude AI
- **Key Features**:
  - Targets specific keywords and contexts related to emissions
  - Supports structured extraction of current and historical data
  - Generates JSON-formatted output with source attribution
- **Main Class**: EmissionsAnalyzer
  - extract_emissions_data(): Main method for extracting emissions data

### 4. Web Interface
- **Purpose**: Provide REST API and user interface for data access
- **Routes**:
  1. **GET /**
     - Serves the main web interface
     - Template: `index.html`
  2. **POST /analyze**
     ```json
     {
       "identifier": "string",
       "id_type": "company|isin"
     }
     ```
  3. **GET /validate-isin/<isin>**
     - Validates ISIN and returns company info

## API Documentation

### POST /analyze

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
    "company": "Nvidia",
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
    "previous_years": [
      {
        "scope_1": {
          "unit": "metric tons CO2e",
          "value": 12346
        },
        "scope_2_location_based": {
          "unit": "metric tons CO2e",
          "value": 142909
        },
        "scope_2_market_based": {
          "unit": "metric tons CO2e",
          "value": 60671
        },
        "year": 2023
      }
    ],
    "source_details": {
      "context": "The emissions data was found in tables and text across multiple pages...",
      "location": "Pages 29-32, 39-40"
    }
  },
  "processed_at": "2024-12-18T23:28:50.305280",
  "report_url": "https://example.com/sustainability-report-2024.pdf",
  "report_year": 2024
}
```

## Target Sections

### Primary Sections
The system looks for emissions data in the following report areas:
- Greenhouse Gas Emissions
- Climate Change Commitments
- Environmental Data Tables
- ESG Metrics and Performance

### Table Indicators
The system prioritizes tables containing:
- "Scope 1" and "Scope 2" labels
- Units like "tCO2e" or "MTCO2e"
- Year-based columns adjacent to numeric data

## Error Handling

### PDF Access Issues
1. Retries failed downloads with exponential backoff
2. Attempts alternative URLs for inaccessible reports
3. Logs failed attempts for further investigation

### Data Extraction Issues
1. Extracts relevant sections when table parsing fails
2. Ensures fallback strategies for unstructured data
3. Uses multiple passes for improved accuracy

### Common Error Codes
1. **400 Bad Request**
   - Missing required parameters
   - Invalid ISIN format
2. **404 Not Found**
   - Company not found
   - No sustainability report found
3. **500 Internal Server Error**
   - PDF processing errors
   - Network errors

## Known Limitations
1. OCR is not implemented for scanned PDFs
2. Sector identification relies on contextual data
3. Assumes data is in metric tons CO2e

## Running the Application

### Development Mode
```bash
export FLASK_APP=src/web/app.py
export FLASK_ENV=development
flask run
```

### Production Mode
```bash
gunicorn -w 4 'src.web.app:app'
```

## Maintenance

### Regular Tasks
1. Update search terms for evolving report formats
2. Monitor API usage limits
3. Test with new reports for compatibility

### Performance Optimization
1. **Caching**
   - ISIN lookups cached
   - PDF processing results cached
2. **Rate Limiting**
   - API requests throttled
   - PDF downloads controlled
3. **Memory Management**
   - Large PDF handling
   - Temporary file cleanup

### Security
1. **API Key Management**
   - Store keys in environment variables
   - Regular key rotation
2. **Input Validation**
   - Sanitize all user inputs
   - ISIN format strictly validated
3. **Error Messages**
   - Limited detail in production
   - No sensitive data exposure