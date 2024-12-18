# Technical Documentation

## Architecture Overview

The application consists of several key components:

1. **Data Collection Layer**
   - `BraveSearchClient`: Handles API-based sustainability report search
   - `ISINLookup`: Manages ISIN to company name resolution
   - `DocumentHandler`: Processes PDF documents and text extraction

2. **Analysis Layer**
   - `EmissionsAnalyzer`: Extracts and processes emissions data
   - Data validation and normalization
   - Unit conversion handling

3. **Web Interface**
   - Flask application with RESTful endpoints
   - Real-time validation and preview
   - Interactive data display
   - Download functionality

## Component Details

### Web Interface

#### Routes

1. **GET /** 
   - Serves the main web interface
   - Template: `index.html`

2. **POST /analyze**
   - Analyzes emissions data for a company
   - Parameters:
     ```json
     {
       "identifier": "string",
       "id_type": "company|isin"
     }
     ```

3. **GET /validate-isin/<isin>**
   - Validates ISIN and returns company info
   - Returns:
     ```json
     {
       "valid": boolean,
       "company_name": "string",
       "error": "string"
     }
     ```

### ISIN Lookup

The `ISINLookup` class provides:
1. ISIN format validation
2. Company name resolution via Yahoo Finance
3. Caching for performance
4. Error handling and reporting

#### Validation Rules
- 12 characters long
- First 2 characters are letters (country code)
- Remaining 10 characters are alphanumeric
- Valid checksum using Luhn algorithm

## API Documentation

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

### GET /validate-isin/{isin}

Validate ISIN and get company information.

**Parameters:**
- `isin`: ISIN to validate (path parameter)

**Response:**
```json
{
  "valid": boolean,
  "company_name": "string",
  "error": "string"
}
```

## Error Handling

### Common Error Codes

1. **400 Bad Request**
   - Missing required parameters
   - Invalid ISIN format
   ```json
   {"error": "Invalid ISIN format"}
   ```

2. **404 Not Found**
   - Company not found
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

## Running the Application

### Development Mode
```bash
# Set environment variables
export FLASK_APP=src/web/app.py
export FLASK_ENV=development

# Run Flask
flask run
```

### Production Mode
```bash
# Using gunicorn
gunicorn -w 4 'src.web.app:app'
```

## Testing

### Unit Tests
Run unit tests with:
```bash
python -m pytest tests/
```

### Sample Test Cases
1. ISIN Validation
   - Valid ISIN: US0378331005 (Apple Inc)
   - Invalid format: ABC123
   - Invalid checksum: US0378331004

2. Emissions Data
   - Complete data (all scopes)
   - Historical data validation
   - Source attribution verification

## Performance Optimization

1. **Caching**
   - ISIN lookups cached
   - PDF processing results cached
   - API responses cached where appropriate

2. **Rate Limiting**
   - API requests throttled
   - ISIN validation rate limited
   - PDF downloads controlled

3. **Memory Management**
   - Large PDF handling
   - Temporary file cleanup
   - Cache size limits

## Security Considerations

1. **API Key Management**
   - Store keys in environment variables
   - Regular key rotation
   - Rate limiting implementation

2. **Input Validation**
   - Sanitize all user inputs
   - ISIN format strictly validated
   - URL parameters checked

3. **Error Messages**
   - Limited detail in production
   - No sensitive data exposure
   - Logging properly configured

## Maintenance

1. **Logging**
   - Application events logged
   - Error tracking
   - Performance monitoring

2. **Monitoring**
   - API endpoint health
   - Cache performance
   - Error rates

3. **Updates**
   - Dependency management
   - Security patches
   - Feature updates