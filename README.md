# Emissions Data Analyzer

A tool to automatically extract and analyze company carbon emissions data from sustainability reports.

## Features

- Search for company sustainability reports using Brave Search API
- Extract Scope 1 and Scope 2 emissions data
- Process both PDF and web-based reports
- Generate analysis using Claude API

## Setup

1. Clone the repository:
```bash
git clone https://github.com/neil-72/emissions-data-analyzer.git
cd emissions-data-analyzer
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file with your API keys:
```
CLAUDE_API_KEY=your_claude_api_key
BRAVE_API_KEY=your_brave_api_key
```

## Usage

```python
from src.main import EmissionsTracker

tracker = EmissionsTracker()
result = tracker.process_company("Apple")
print(result)
```

## Project Structure

```
src/
├── search/       # Brave Search integration
├── extraction/   # Document processing
├── analysis/     # Claude analysis
└── utils/        # Helper utilities
```