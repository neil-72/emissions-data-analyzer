# Emissions Data Analyzer

## Overview
This tool automatically extracts Scope 1 and Scope 2 carbon emissions data from company sustainability reports. It uses the Brave Search API to find reports and Claude AI to analyze them.

## Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/neil-72/emissions-data-analyzer.git
cd emissions-data-analyzer
```

2. **Set up Python environment**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

3. **Configure API keys**
Create a .env file with your API keys:
```env
CLAUDE_API_KEY=your_claude_api_key
BRAVE_API_KEY=your_brave_api_key
```

4. **Run the program**
```bash
python -m src.main
```

## Features
- Automatic discovery of sustainability reports
- PDF and webpage text extraction
- Intelligent emissions data parsing
- Structured data output

## Documentation
See [DOCUMENTATION.md](DOCUMENTATION.md) for detailed technical documentation.

## Example Output
```json
{
    "company": "Example Corp",
    "report_url": "https://example.com/sustainability-2024.pdf",
    "report_year": 2024,
    "emissions_data": {
        "scope_1": {
            "value": 1000000,
            "unit": "metric tons CO2e",
            "year": 2023
        },
        "scope_2": {
            "value": 2000000,
            "unit": "metric tons CO2e",
            "year": 2023
        },
        "context": "5% reduction from previous year"
    }
}
```

## Troubleshooting
- Check that your API keys are correctly set in .env
- Ensure you're running Python 3.8 or higher
- Look for detailed error messages in the console output

## Contributing
Contributions are welcome! Please see our contribution guidelines.

## License
MIT License - see LICENSE file for details.