# Emissions Data Analyzer

A tool to automatically extract Scope 1 and Scope 2 carbon emissions data from company sustainability reports using Brave Search and Claude APIs.

## Key Features

1. Smart detection and extraction of emissions data using Claude AI
2. Data extraction from sustainability reports (PDFs)
3. Automatic unit conversion to metric tons CO2e
4. Web interface for easy access and data visualization
5. Download options in JSON format

## Installation Guide

### Prerequisites
- Python 3.8 or higher
- Git
- Text editor of your choice
- Brave Search API key (get from [Brave API Portal](https://brave.com/search/api/))
- Claude API key (get from [Anthropic Console](https://console.anthropic.com/))

### Step-by-Step Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/neil-72/emissions-data-analyzer.git
   cd emissions-data-analyzer
   ```

2. **Set Up Virtual Environment**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**

   Create a .env file in the project root:
   ```bash
   CLAUDE_API_KEY=your_claude_api_key
   BRAVE_API_KEY=your_brave_api_key
   ```

## Usage

### Web Interface

1. Start the Flask server:
   ```bash
   cd src/web
   flask run
   ```

2. Open http://localhost:5000 in your browser
3. Enter a company name
4. View and download the results

### Command Line Interface

1. Run the main script:
   ```bash
   python -m src.main
   ```

2. Enter company names when prompted
3. Results will be saved to JSON files

## Output Format

Example output:
```json
{
  "company": "example_company",
  "report_url": "https://example.com/sustainability-report-2024.pdf",
  "report_year": 2024,
  "emissions_data": {
    "scope_1": {
      "value": 14390,
      "unit": "metric tons CO2e"
    },
    "scope_2_market_based": {
      "value": 40555,
      "unit": "metric tons CO2e"
    }
  },
  "processed_at": "2024-12-18T14:50:26.282104"
}
```

## Notes

1. The tool intelligently converts various unit formats to metric tons CO2e
2. Both market-based and location-based Scope 2 emissions are captured when available
3. Historical data is included when found
4. Source details preserve the exact location and context of the data

## Limitations

* Requires valid API keys for both Brave Search and Claude
* Works best with PDFs that have machine-readable text
* May need assistance with complex table layouts
* Accuracy depends on the clarity of the source report
* Network access required for API calls and PDF downloads

See DOCUMENTATION.md for technical details.