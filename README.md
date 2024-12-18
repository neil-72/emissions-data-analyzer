# Emissions Data Analyzer

A tool to automatically extract Scope 1 and Scope 2 carbon emissions data from company sustainability reports using Brave Search and Claude APIs.

## Key Features
	1.	Extracts relevant sections of reports based on keywords like “Scope 1” and “Scope 2” and sends context-rich chunks to Claude for analysis.
	2.	Removes duplicate lines for cleaner data processing.
	3.	Outputs extracted data in JSON format with details on emissions values, years, and context.
	4.	Saves intermediate files (claude_input_data.txt) for inspection of processed text.
	5.	Validates and aggregates results across multiple chunks of text.

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

4. Set up environment variables
Create a .env file:
```env
CLAUDE_API_KEY=your_claude_api_key
BRAVE_API_KEY=your_brave_api_key
```

5. Run the program:
```bash
python -m src.main
```

Data Extraction Process
	1.	Preprocessing:
	•	Extracts lines around relevant keywords (Scope 1 or Scope 2) with configurable context (default: 15 lines above and below).
	•	Saves processed text to claude_input_data.txt for verification.
	2.	Analysis:
	•	Breaks down long text into manageable chunks (30,000 characters).
	•	Sends each chunk to Claude for extracting emissions data.
	3.	Output:
	•	Aggregates results into a single JSON file in the output directory.

Output Format

{
    "company": "Company Name",
    "report_url": "URL to sustainability report",
    "report_year": 2024,
    "emissions_data": {
        "current_year": {
            "year": 2023,
            "scope_1": {
                "value": 144960,
                "unit": "metric tons CO2e",
                "measurement": "market-based"
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
            "context": "The emissions data was found in the environmental metrics section."
        }
    }
}Notes
	1.	Does not convert units automatically; the tool assumes values are in metric tons CO2e.
	2.	Sector identification is derived using keywords or left as null if insufficient information is present.
	3.	The tool works only with official sustainability reports in PDF format.

Limitations
	•	Requires valid API keys for Brave Search and Claude.
	•	Text extraction depends on report formatting and may miss complex tabular data.
	•	Sector identification may not always be accurate and relies on report context.

See DOCUMENTATION.md for technical details.




