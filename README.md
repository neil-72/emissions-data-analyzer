# Emissions Data Analyzer

Extract and analyze Scope 1 and Scope 2 carbon emissions data from company sustainability reports. Uses AI to find and process emissions data from publicly available reports, with support for company name or ISIN lookup.

## What It Does

- 🔍 **Find Reports**: Automatically finds latest sustainability reports using Brave Search
- 📊 **Extract Data**: Uses Claude AI to extract Scope 1 and Scope 2 emissions data
- 🏢 **Company Lookup**: Search by company name or ISIN (International Securities Identification Number)
- 📈 **Historical Data**: Captures historical emissions data when available
- 🔄 **Unit Conversion**: Automatically converts to metric tons CO2e

## Prerequisites

- Python 3.8+
- [Brave Search API key](https://brave.com/search/api/)
- [Claude API key](https://console.anthropic.com/)

## Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/neil-72/emissions-data-analyzer.git
cd emissions-data-analyzer
```

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Configure Environment
Create a `.env` file in the project root:
```bash
echo "CLAUDE_API_KEY=your_claude_api_key
BRAVE_API_KEY=your_brave_api_key" > .env
```

### 4. Running the Tool

#### Option 1: Command Line Interface (Recommended for First Use)
Run directly with Python to see detailed processing logs:
```bash
python -m src.main
```
Then enter company names when prompted.

#### Option 2: Web Interface
```bash
# Kill any existing Flask processes if needed
pkill -f flask

# Start Flask with a specific port
flask run --port=5002
```
Then open http://localhost:5002 in your browser.

### Common Issues & Solutions

#### Port Already in Use
```bash
# Check what's using the port (on macOS/Linux)
lsof -i :5000

# Kill the process
pkill -f flask

# Or simply try a different port
flask run --port=5003
```

#### Environment Not Found
If you get module not found errors:
```bash
# Make sure you're in the project directory
cd emissions-data-analyzer

# Reactivate the environment
source venv/bin/activate
```

#### Need a Clean Start?
If you want to reset everything:
```bash
# Deactivate current environment
deactivate

# Remove old environment
rm -rf venv

# Create fresh environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Example Output

```json
{
  "company": "Nvidia",
  "emissions_data": {
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
      "context": "Data extracted from sustainability report",
      "location": "Pages 29-32, 39-40"
    }
  }
}
```

## Main Components

### 1. Search (src/search/brave_search.py)
- Uses Brave Search API to find sustainability reports
- Filters for PDFs and relevant documents
- Handles rate limiting and retries

### 2. PDF Processing (src/extraction/pdf_handler.py)
- Extracts text and tables from PDFs
- Handles different document formats
- Preserves document structure

### 3. Analysis (src/analysis/claude_analyzer.py)
- Uses Claude AI to find emissions data
- Extracts both current and historical data
- Validates and standardizes units

### 4. ISIN Support (src/isin/isin_lookup.py)
- Validates ISIN format using Luhn algorithm
- Looks up company info via Yahoo Finance
- Real-time validation in web interface

## Web Interface

- Simple search by company name or ISIN
- Real-time ISIN validation
- Visual charts for emissions data
- Historical data tracking
- Download results as JSON

## Known Limitations

- Only processes publicly available reports
- Best with machine-readable PDFs
- Rate limits on API usage
- Some scanned PDFs may not work

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_isin_lookup.py
```

## License

MIT License - see LICENSE file

## Contributing

Contributions welcome! Please check our issues page.