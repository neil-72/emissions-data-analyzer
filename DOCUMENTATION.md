# Technical Documentation

## Architecture Overview

The application consists of several key components:

1. **Data Collection Layer**
   - `BraveSearchClient`: Handles sustainability report search
   - `DocumentHandler`: Processes PDF documents

2. **Analysis Layer**
   - `EmissionsAnalyzer`: Extracts and processes emissions data
   - Data validation and normalization

3. **Web Interface**
   - Flask application with RESTful endpoints
   - Interactive data display
   - Download functionality

## Component Details

### Web Interface (src/web/)

#### Routes

1. **GET /** 
   - Serves the main web interface
   - Template: `index.html`

2. **POST /analyze**
   - Analyzes emissions data for a company
   - Parameters:
     ```json
     {
       "identifier": "company_name"
     }
     ```
   - Returns analyzed emissions data

### API Documentation

#### POST /analyze

Analyze emissions data for a specified company.

**Request Format:**
```json
{
  "identifier": "company_name"
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

**Error Responses:**

1. **400 Bad Request**
   - Missing or invalid company name
   ```json
   {"error": "Company name required"}
   ```

2. **404 Not Found**
   - No sustainability report found
   - No emissions data found
   ```json
   {"error": "No sustainability report found"}
   ```

3. **500 Internal Server Error**
   - PDF processing errors
   - Network errors
   - Analysis errors
   ```json
   {"error": "Error processing PDF document"}
   ```

### Data Processing

#### Unit Handling
1. Automatic detection of input units
2. Conversion to metric tons CO2e
3. Validation of unit consistency

#### Data Structure

The emissions data structure includes:
- Current year emissions (Scope 1, Scope 2)
- Historical emissions data when available
- Source document details and context
- Unit standardization to metric tons CO2e
- Timestamps and processing metadata

## Error Handling

### Common Error Scenarios

1. **PDF Processing**
   - Non-readable PDFs
   - Complex table layouts
   - Missing or corrupt files

2. **API Issues**
   - Rate limits
   - Authentication failures
   - Network timeouts

3. **Data Validation**
   - Invalid units
   - Out of range values
   - Inconsistent data

### Error Logging

```python
# Example error handling
try:
    result = process_document(url)
except PDFProcessingError as e:
    logger.error(f"PDF processing failed: {str(e)}")
    raise HTTPException(status_code=500)
except ValidationError as e:
    logger.warning(f"Data validation failed: {str(e)}")
    raise HTTPException(status_code=400)
```

## Security Considerations

1. **API Key Management**
   - Store keys in environment variables
   - Regular key rotation
   - Rate limiting implementation

2. **Input Validation**
   - Sanitize all user inputs
   - Validate URLs before processing
   - Restrict file types and sizes

3. **Error Messages**
   - Generic errors in production
   - Detailed logging for debugging
   - No sensitive data in responses

## Performance Optimization

1. **Memory Management**
   - Stream large PDFs
   - Clean up temporary files
   - Implement caching

2. **Request Handling**
   - Rate limiting
   - Response caching
   - Asynchronous processing

3. **API Usage**
   - Batch requests where possible
   - Cache API responses
   - Implement retries with backoff