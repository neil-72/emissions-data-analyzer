# Technical Documentation

This guide covers the technical details of the Emissions Data Analyzer tool.

## 🏗️ Project Structure

```
emissions-data-analyzer/
├── .env                 # Your API keys (don't commit!)
├── .env.example        # Template for .env
├── .flaskenv           # Flask configuration
├── requirements.txt    # Python dependencies
└── src/
    ├── web/           # Web interface
    │   ├── app.py     # Main Flask application
    │   ├── templates/ # HTML files
    │   └── static/    # CSS, JS, etc.
    ├── search/        # Brave Search integration
    ├── analysis/      # Claude analysis logic
    └── extraction/    # PDF processing
```

## 🛠️ Setup Guide

### 1. Development Environment

```bash
# Required files for Python packaging
touch src/__init__.py
touch src/web/__init__.py
touch src/search/__init__.py
touch src/analysis/__init__.py
touch src/extraction/__init__.py

# Required environment files
touch .env       # API keys
touch .flaskenv  # Flask config
```

### 2. Environment Files

**.env**
```bash
CLAUDE_API_KEY=your_claude_api_key_here
BRAVE_API_KEY=your_brave_api_key_here
```

**.flaskenv**
```bash
FLASK_APP=src.web.app
FLASK_ENV=development  # Change to 'production' for deployment
```

## 🌐 API Endpoints

### POST /analyze
Analyze emissions for a company.

**Request:**
```json
{
  "identifier": "company_name"  // Required
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
    }
  },
  "processed_at": "ISO datetime"
}
```

**Error Responses:**
- 400: Missing company name
- 404: No report/data found
- 500: Processing error

## 🚦 Error Handling

The application uses HTTP status codes and JSON responses for errors:

```python
# Example error response
{
  "error": "No sustainability report found for Company X"
}
```

Common error scenarios:
1. PDF not machine-readable
2. No emissions data found
3. Network timeout
4. API rate limits

## 🖥️ Running in Production

1. **Using Gunicorn** (Recommended)
   ```bash
   pip install gunicorn
   gunicorn -w 4 'src.web.app:app'
   ```

2. **Using Docker**
   ```bash
   docker build -t emissions-analyzer .
   docker run -p 5000:5000 emissions-analyzer
   ```

## 🔍 How It Works

1. **Search Phase**
   - Uses Brave Search API to find sustainability reports
   - Filters for PDF documents
   - Ranks by relevance and date

2. **Extraction Phase**
   - Downloads PDF
   - Converts to text
   - Preserves table structure

3. **Analysis Phase**
   - Claude AI identifies emissions data
   - Normalizes units
   - Validates data consistency

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_analyzer.py

# Run with coverage
python -m pytest --cov=src
```

## 📊 Data Handling

### Unit Conversions
All data is converted to metric tons CO2e. Supported input units:
- Metric tons (tonnes) CO2e
- Short tons CO2e
- Kilograms CO2e
- Million metric tons CO2e

### Data Validation
- Checks for realistic ranges
- Validates year consistency
- Verifies unit conversions

## 🔐 Security Notes

1. **API Keys**
   - Never commit .env files
   - Rotate keys regularly
   - Use environment variables

2. **Input Validation**
   - All user input is sanitized
   - URL parameters are validated
   - File uploads are restricted

3. **Error Messages**
   - Production errors hide implementation details
   - Logging excludes sensitive data

## 🚀 Performance Tips

1. **Memory Usage**
   - Large PDFs are processed in chunks
   - Temporary files are cleaned up
   - Results are cached when possible

2. **API Optimization**
   - Requests are rate-limited
   - Responses are cached
   - Batch operations where possible