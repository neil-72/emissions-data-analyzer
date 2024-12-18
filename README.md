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
source venv/bin/activate # On Windows: venv\Scripts\activate
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

Example output when analyzing NVIDIA's sustainability report:

```json
{
  "company": "nvidia",
  "report_url": "https://images.nvidia.com/aem-dam/Solutions/documents/FY2024-NVIDIA-Corporate-Sustainability-Report.pdf",
  "report_year": 2024,
  "emissions_data": {
    "company": "nvidia",
    "sector": null,
    "current_year": {
      "year": 2024,
      "scope_1": {
        "value": 14390,
        "unit": "metric tons CO2e"
      },
      "scope_2_market_based": {
        "value": 40555,
        "unit": "metric tons CO2e"
      },
      "scope_2_location_based": {
        "value": 178087,
        "unit": "metric tons CO2e"
      }
    },
    "previous_years": [
      {
        "year": 2023,
        "scope_1": {
          "value": 12346,
          "unit": "metric tons CO2e"
        },
        "scope_2_market_based": {
          "value": 60671,
          "unit": "metric tons CO2e"
        },
        "scope_2_location_based": {
          "value": 142909,
          "unit": "metric tons CO2e"
        }
      },
      {
        "year": 2022,
        "scope_1": {
          "value": 4612,
          "unit": "metric tons CO2e"
        },
        "scope_2_market_based": {
          "value": 78210,
          "unit": "metric tons CO2e"
        },
        "scope_2_location_based": {
          "value": 133569,
          "unit": "metric tons CO2e"
        }
      }
    ],
    "source_details": {
      "location": "Pages 29-30",
      "context": "The emissions data was found in tables on pages 29-30 of the sustainability report."
    }
  },
  "processed_at": "2024-12-18T14:50:26.282104"
}
```

## Notes

1. The tool assumes all emissions values are in metric tons CO2e
2. Both market-based and location-based Scope 2 emissions are captured when available
3. Historical data for up to two previous years is included when found
4. Source details provide page numbers and context where data was found

## Limitations

* Requires valid API keys for both Brave Search and Claude
* Works best with PDFs that have machine-readable text
* May miss data in complex tables or images
* Accuracy depends on the clarity and structure of the source report

See DOCUMENTATION.md for technical details.