# Emissions Data Analyzer

Extract and analyze carbon emissions data from company sustainability reports automatically. This tool uses AI to find and process Scope 1 and Scope 2 emissions data from company sustainability reports.

## 🚀 Quick Start

```bash
# Clone and enter the repository
git clone https://github.com/neil-72/emissions-data-analyzer.git
cd emissions-data-analyzer

# Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up your .env file (IMPORTANT!)
cp .env.example .env
# Edit .env with your API keys from Brave and Anthropic

# Start the web interface
flask run
```

Then open http://localhost:5000 in your browser!

## 🔑 Before You Start: Get API Keys

You'll need two API keys:

1. **Brave Search API Key**
   - Go to [Brave API Portal](https://brave.com/search/api/)
   - Sign up and create an API key
   - Free tier available

2. **Claude API Key**
   - Go to [Anthropic Console](https://console.anthropic.com/)
   - Sign up and create an API key
   - Credit card required

## 📋 Common Issues & Solutions

1. **"Could not import 'app'"**
   ```bash
   # Make sure you're in the project root directory, not src/web
   cd emissions-data-analyzer  # Go to root directory
   flask run
   ```

2. **Import errors**
   ```bash
   # Create these empty files:
   touch src/__init__.py
   touch src/web/__init__.py
   touch src/search/__init__.py
   touch src/analysis/__init__.py
   touch src/extraction/__init__.py
   ```

3. **Environment variables not found**
   - Create a `.env` file in the root directory
   - Copy the format from `.env.example`
   - Never commit your actual API keys to Git

## 💻 Using the Tool

1. **Web Interface** (Recommended)
   ```bash
   flask run
   # Open http://localhost:5000
   # Enter company name and click Analyze
   ```

2. **Command Line**
   ```bash
   python -m src.main
   # Follow the prompts
   ```

## 📊 Sample Output

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
  }
}
```

## 📚 More Information

- [Technical Documentation](DOCUMENTATION.md) - Detailed technical guide
- [Issue Tracker](https://github.com/neil-72/emissions-data-analyzer/issues) - Report bugs or request features

## ⚠️ Important Notes

- The tool works best with PDFs that have machine-readable text
- All data is converted to metric tons CO2e automatically
- Processes both market-based and location-based Scope 2 emissions
- Network access is required for API calls and PDF downloads
