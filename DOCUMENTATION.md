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

### POST /analyze

Analyze emissions data for a company.

**Request:**
```json
{
  "identifier": "company_name"
}
```

**Response:**
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
    }
  },
  "processed_at": "string (ISO datetime)"
}
```

## Error Handling

### Common Error Codes

1. **400 Bad Request**
   - Missing company name

2. **404 Not Found**
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
# Using gunicorn (if installed)
gunicorn -w 4 'src.web.app:app'
```

## Performance Considerations

1. **Caching**
   - PDF processing results cached
   - API responses cached where appropriate

2. **Memory Management**
   - Large PDF handling
   - Temporary file cleanup

## Security Considerations

1. **Input Validation**
   - All user inputs sanitized
   - URL parameters checked

2. **Error Messages**
   - Limited detail in production
   - No sensitive data exposure

## Project Structure

```
.
├── src/
│   ├── web/                    # Web interface
│   │   ├── app.py              # Flask application
│   │   ├── templates/          # HTML templates
│   │   │   └── index.html      # Main page
│   │   └── static/             # Static assets
│   │       └── js/             # JavaScript files
│   │           └── app.js      # Frontend logic
│   ├── search/                 # Search functionality
│   ├── extraction/             # PDF extraction
│   └── analysis/               # Data analysis
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables
```