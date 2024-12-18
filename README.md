# Emissions Data Analyzer

A tool to automatically extract Scope 1 and Scope 2 carbon emissions data from company sustainability reports using Brave Search and Claude APIs.

## Key Features

1. Smart detection and extraction of emissions data from sustainability reports using Claude AI
2. Intelligent context preservation around emissions data
3. Automatic unit conversion to metric tons CO2e
4. Multi-year data tracking with both current and historical emissions
5. Detailed source context preservation
6. Automatic validation and deduplication of results

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
   venv\\Scripts\\activate
   ```

   After activation, your prompt should show (venv) at the beginning.

3. **Install Dependencies**
   ```bash
   # Upgrade pip first
   pip install --upgrade pip
   
   # Install required packages
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**

   Create a .env file in the project root:
   ```bash
   # Method 1: Using cat (macOS/Linux)
   cat > .env <<EOL
   CLAUDE_API_KEY=your_claude_api_key
   BRAVE_API_KEY=your_brave_api_key
   EOL

   # Method 2: Using echo (Windows)
   echo CLAUDE_API_KEY=your_claude_api_key > .env
   echo BRAVE_API_KEY=your_brave_api_key >> .env
   
   # Method 3: Manually create .env in your text editor with:
   CLAUDE_API_KEY=your_claude_api_key
   BRAVE_API_KEY=your_brave_api_key
   ```

   Replace `your_claude_api_key` and `your_brave_api_key` with your actual API keys.

5. **Verify Installation**
   ```bash
   # Should show the virtual environment activated
   which python  # On Windows: where python
   
   # Should show all required packages
   pip list
   
   # Test environment variables
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(bool(os.getenv('CLAUDE_API_KEY'))); print(bool(os.getenv('BRAVE_API_KEY')))"
   ```

6. **Run the Program**
   ```bash
   python -m src.main
   ```

### Troubleshooting

1. **Virtual Environment Issues**
   - If `venv` creation fails, try: `python -m pip install --user virtualenv`
   - If activation shows errors, check Python installation
   - On Windows, if activation is blocked, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

2. **Package Installation Issues**
   - If pip install fails, try: `pip install --upgrade pip setuptools wheel`
   - For SSL errors, check Python's SSL certificates
   - For build errors, install your OS's build tools

3. **Environment Variables**
   - If .env isn't loading, check file location and format
   - No quotes needed around API keys
   - No spaces around the = sign
   - Each variable on a new line

4. **Common Error Messages**
   - "ModuleNotFoundError": Check virtual environment activation
   - "ImportError": Verify all requirements are installed
   - "KeyError": Check .env file configuration
   - "Permission denied": Check file/directory permissions

## How it Works

1. The tool searches for a company's latest sustainability report using Brave Search
2. It downloads and processes the PDF, extracting text content while preserving structure
3. Relevant sections about emissions are identified with surrounding context
4. Claude AI analyzes the text to extract and normalize emissions data
5. Results are validated, aggregated, and saved in JSON format

## Data Processing Features

1. **Unit Handling**
   - Automatic unit detection and conversion to metric tons CO2e using Claude AI
   - Built-in conversion logic framework for additional unit handling
   - Validation of unit consistency across data points

2. **Data Validation**
   - Duplicate removal and data aggregation
   - Consistency checks across years
   - Source context preservation
   - Structured data validation

3. **Emissions Coverage**
   - Complete Scope 1 emissions data
   - Both market-based and location-based Scope 2 emissions
   - Historical data tracking for trend analysis
   - Detailed source documentation

## Output Format

Example output when analyzing a sustainability report:

```json
{
  "company": "example_company",
  "report_url": "https://example.com/sustainability-report-2024.pdf",
  "report_year": 2024,
  "emissions_data": {
    "company": "example_company",
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
      }
    ],
    "source_details": {
      "location": "Pages 29-30",
      "context": "Data extracted from environmental performance tables"
    }
  },
  "processed_at": "2024-12-18T14:50:26.282104"
}
```

## Notes

1. The tool uses Claude AI to intelligently convert various unit formats to metric tons CO2e
2. Both market-based and location-based Scope 2 emissions are captured when available
3. Historical data for previous years is included when found
4. Source details preserve the exact location and context of the data

## Limitations

* Requires valid API keys for both Brave Search and Claude
* Works best with PDFs that have machine-readable text
* May need assistance with complex table layouts or non-standard units
* Accuracy depends on the clarity and structure of the source report
* Network access required for API calls and PDF downloads

See DOCUMENTATION.md for technical details.