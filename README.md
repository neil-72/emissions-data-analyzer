# Emissions Data Analyzer

A tool to automatically extract Scope 1 and Scope 2 carbon emissions data from company sustainability reports using Brave Search and Claude APIs.

## Prerequisites

- Python 3.8 or higher
- Git
- Brave Search API key (get from [Brave API Portal](https://brave.com/search/api/))
- Claude API key (get from [Anthropic Console](https://console.anthropic.com/))

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/neil-72/emissions-data-analyzer.git
   cd emissions-data-analyzer
   ```

2. **Create Required Files**
   ```bash
   # Create Python package structure
   touch src/__init__.py
   touch src/web/__init__.py
   touch src/search/__init__.py
   touch src/analysis/__init__.py
   touch src/extraction/__init__.py

   # Create environment files
   cp .env.example .env
   cp .flaskenv.example .flaskenv
   ```

3. **Set Up Virtual Environment**
   ```bash
   python3 -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   .\venv\Scripts\activate
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Environment**
   Edit `.env` file with your API keys:
   ```bash
   CLAUDE_API_KEY=your_claude_api_key
   BRAVE_API_KEY=your_brave_api_key
   ```

## Running the Application

### Web Interface (Recommended)

1. **Start from Project Root**
   ```bash
   # Ensure you're in the project root directory
   cd emissions-data-analyzer  # if not already there
   flask run
   ```

2. Open http://localhost:5000 in your browser
3. Enter a company name and submit
4. View and download the results

### Command Line Interface

```bash
# From project root
python -m src.main
```

## Troubleshooting

1. **Import Errors**
   - Ensure you're running flask from the project root
   - Verify all __init__.py files exist
   - Check virtual environment is activated

2. **API Key Errors**
   - Verify .env file exists and has correct keys
   - Check API key format matches example
   - Ensure keys are active and have sufficient credits

3. **Flask Errors**
   - Confirm .flaskenv exists with correct content
   - Verify you're in project root directory
   - Check Python version compatibility

## Output Format

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

## Features

1. Smart detection and extraction of emissions data using Claude AI
2. Data extraction from sustainability reports (PDFs)
3. Automatic unit conversion to metric tons CO2e
4. Web interface for easy access and data visualization
5. Download options in JSON format

## Limitations

* Requires valid API keys for both Brave Search and Claude
* Works best with PDFs that have machine-readable text
* May need assistance with complex table layouts
* Accuracy depends on the clarity of the source report
* Network access required for API calls and PDF downloads

See [Technical Documentation](DOCUMENTATION.md) for detailed information.