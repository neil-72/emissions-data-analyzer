# Emissions Data Analyzer

A tool to automatically extract Scope 1 and Scope 2 carbon emissions data from company sustainability reports using Brave Search and Claude APIs.

## Key Features

1. Extracts relevant sections of reports based on keywords like "Scope 1" and "Scope 2" and sends context-rich chunks to Claude for analysis
2. Removes duplicate lines for cleaner data processing
3. Outputs extracted data in JSON format with details on emissions values, years, and context
4. Saves intermediate files (claude_input_data.txt) for inspection of processed text
5. Validates and aggregates results across multiple chunks of text

## Setup

1. Clone the repository:
```bash
git clone https://github.com/neil-72/emissions-data-analyzer.git
cd emissions-data-analyzer
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a .env file:
```env
CLAUDE_API_KEY=your_claude_api_key
BRAVE_API_KEY=your_brave_api_key
```

5. Run the program:
```bash
python -m src.main
```

## How it Works

1. The tool searches for a company's latest sustainability report using Brave Search
2. It downloads and processes the PDF, extracting text content
3. Relevant sections about emissions are identified and sent to Claude for analysis
4. Results are aggregated and saved in JSON format

## Output Format

```json
{
  "company": "Company Name",
  "sector": "Industry Sector or null",
  "current_year": {
    "year": 2023,
    "scope_1": {
      "value": 144960,
      "unit": "metric tons CO2e"
    },
    "scope_2_market_based": {
      "value": 393134,
      "unit": "metric tons CO2e"
    },
    "scope_2_location_based": {
      "value": 6381250,
      "unit": "metric tons CO2e"
    }
  },
  "previous_years": [
    {
      "year": 2022,
      "scope_1": {
        "value": 139413,
        "unit": "metric tons CO2e"
      },
      "scope_2_market_based": {
        "value": 288029,
        "unit": "metric tons CO2e"
      },
      "scope_2_location_based": {
        "value": 6381250,
        "unit": "metric tons CO2e"
      }
    }
  ],
  "source_details": {
    "location": "Page 25",
    "context": "Found in Environmental Metrics section"
  },
  "processed_at": "2024-12-18T10:30:00Z"
}
```

## Notes

1. The tool assumes all emissions values are in metric tons CO2e
2. Sector identification is based on report context and may be null if unclear
3. Both market-based and location-based Scope 2 emissions are captured when available
4. Historical data for up to 2 previous years is included when found

## Limitations

- Requires valid API keys for both Brave Search and Claude
- Works best with PDFs that have machine-readable text
- May miss data in complex tables or images
- Accuracy depends on the clarity and structure of the source report

See DOCUMENTATION.md for technical details.