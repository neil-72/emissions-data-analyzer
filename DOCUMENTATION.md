# Technical Documentation

## Project Structure

```
emissions-data-analyzer/
├── .env                  # API keys (not in repo)
├── .env.example         # API key template
├── .flaskenv            # Flask configuration
├── .gitignore           # Git ignore rules
├── README.md            # Project overview
├── DOCUMENTATION.md     # Technical details
├── requirements.txt     # Python dependencies
└── src/
    ├── __init__.py      # Makes src a package
    ├── main.py          # CLI entry point
    ├── web/             # Web interface
    │   ├── __init__.py  # Makes web a package
    │   ├── app.py       # Flask application
    │   ├── templates/   # HTML templates
    │   └── static/      # Static assets
    ├── search/          # Search functionality
    │   ├── __init__.py
    │   └── brave_search.py
    ├── extraction/      # PDF handling
    │   ├── __init__.py
    │   └── pdf_handler.py
    └── analysis/        # Data analysis
        ├── __init__.py
        └── claude_analyzer.py
```

## API Documentation

### POST /analyze

Analyzes emissions data for a specified company.

**Request Format:**
```json
{
  "identifier": "company_name"
}
```

**Success Response (200):**
```json
{
  "company": "string",
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

## Development Setup

### Environment Files

1. **.env**
   ```bash
   CLAUDE_API_KEY=your_claude_api_key
   BRAVE_API_KEY=your_brave_api_key
   ```

2. **.flaskenv**
   ```bash
   FLASK_APP=src.web.app
   FLASK_ENV=development
   ```

### Running Development Server
```bash
# From project root
flask run --debug
```

### Production Deployment

1. **Using Gunicorn**
   ```bash
   pip install gunicorn
   gunicorn -w 4 'src.web.app:app'
   ```

2. **Environment Variables**
   ```bash
   export FLASK_ENV=production
   export FLASK_DEBUG=0
   ```

## Data Processing

### Unit Conversions

Supported input units:
- Metric tons CO2e (tCO2e)
- Million metric tons CO2e (MtCO2e)
- Kilograms CO2e (kgCO2e)
- Short tons CO2e
- Kilowatts (converted using emission factors)

All values are converted to metric tons CO2e for consistency.

### Data Validation

1. **Range Validation**
   - Values must be positive
   - Upper limits based on company size
   - Year validation against report date

2. **Unit Consistency**
   - All final values in metric tons CO2e
   - Automatic unit detection and conversion
   - Validation of conversion accuracy

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