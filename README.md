# Emissions Data Analyzer

A tool to automatically extract Scope 1 and Scope 2 carbon emissions data from company sustainability reports using Brave Search and Claude APIs.

## Key Features

1. Extracts relevant sections of reports based on keywords like "Scope 1" and "Scope 2" and sends context-rich chunks to Claude for analysis
2. Removes duplicate lines for cleaner data processing
3. Outputs extracted data in JSON format with details on emissions values, years, and context
4. Saves intermediate files (claude_input_data.txt) for inspection of processed text 
5. Validates and aggregates results across multiple chunks of text

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
   
   # Method 3: Manually create .env in your text editor
   # Add these lines:
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