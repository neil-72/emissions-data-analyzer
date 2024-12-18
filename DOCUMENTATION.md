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
   - Returns analyzed emissions data

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

### Data Processing

#### Unit Handling
1. Automatic detection of input units
2. Conversion to metric tons CO2e
3. Validation of unit consistency

#### Data Structure
```python
data = {
    'scope_1': {
        'value': float,
        'unit': str
    },
    'scope_2_market_based': {
        'value': float,
        'unit': str
    },
    'scope_2_location_based': {
        'value': float,
        'unit': str
    }
}
```

## API Documentation

### Endpoints

#### POST /analyze

Analyze emissions data for a company.

**Request:**
```json
{
  "identifier": "string",
  "id_type": "company|isin"
}
```

**Response:**
```json
{
  "company": "string",
  "original_isin": "string|null",
  "report_url": "string",
  "report_year": number,
  "emissions_data": {
    "scope_1": {
      "value": number,
      "unit": "string"
    },
    "scope_2_market_based": {
      "value": number,
      "unit": "string"
    },
    "scope_2_location_based": {
      "value": number,
      "unit": "string"
    }
  },
  "processed_at": "string (ISO datetime)"
}
```

#### GET /validate-isin/{isin}

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

2. **404 Not Found**
   - Company not found
   - No sustainability report found
   - No emissions data found

3. **500 Internal Server Error**
   - PDF processing errors
   - Network errors
   - Analysis errors

### Error Response Format
```json
{
  "error": "Error message description"
}
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
   - Complete data (both scopes)
   - Partial data (scope 1 only)
   - Missing data handling

## Deployment

### Requirements
- Python 3.8+
- Flask
- Required Python packages in requirements.txt

### Server Configuration
1. Set up virtual environment
2. Install dependencies
3. Configure environment variables
4. Set up web server (e.g., nginx + gunicorn)

## Performance Considerations

1. **Caching**
   - ISIN lookups cached
   - Company data cached where appropriate
   - PDF processing results cached

2. **Rate Limiting**
   - API requests throttled
   - ISIN validation rate limited
   - PDF downloads controlled

3. **Memory Management**
   - Large PDF handling
   - Cache size limits
   - Temporary file cleanup

## Security Considerations

1. **Input Validation**
   - All user inputs sanitized
   - ISIN format strictly validated
   - URL parameters checked

2. **Error Messages**
   - Limited detail in production
   - No sensitive data exposure
   - Logging properly configured

3. **API Protection**
   - Rate limiting
   - Input size limits
   - Security headers

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
