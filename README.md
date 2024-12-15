# Emissions Data Analyzer

A tool to automatically extract Scope 1 and Scope 2 carbon emissions data from company sustainability reports using Brave Search and Claude APIs.

## Key Features
- Smart section targeting to find emissions data in complex reports
- Robust validation of extracted data with typical range checking
- Support for multiple report formats (PDF, web-based)
- Detailed logging for debugging and verification
- Fallback strategies when primary data extraction fails

## Setup

1. Clone the repository:
```bash
git clone https://github.com/neil-72/emissions-data-analyzer.git
cd emissions-data-analyzer
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
Create a .env file:
```env
CLAUDE_API_KEY=your_claude_api_key
BRAVE_API_KEY=your_brave_api_key
```

5. **Run the program**
```bash
python -m src.main
```

## Output Format
```json
{
    "company": "Company Name",
    "report_url": "URL to sustainability report",
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
        "context": "Data from latest sustainability report"
    }
}
```

## Notes
- Only searches for official company sustainability reports in PDF format
- Prioritizes most recent data (2024, then 2023)
- Results are saved to the `output` directory

See [DOCUMENTATION.md](DOCUMENTATION.md) for technical details.
