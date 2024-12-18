from flask import Flask, render_template, request, jsonify
from src.search.brave_search import BraveSearchClient
from src.analysis.claude_analyzer import EmissionsAnalyzer
from src.extraction.pdf_handler import DocumentHandler
import json
from datetime import datetime

app = Flask(__name__)

# Initialize our existing components
search_client = BraveSearchClient()
analyzer = EmissionsAnalyzer()
document_handler = DocumentHandler()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        company_name = data.get('identifier')
        
        if not company_name:
            return jsonify({'error': 'Company name required'}), 400

        # Use existing functionality
        report_data = search_client.search_sustainability_report(company_name)
        if not report_data:
            return jsonify({'error': 'No sustainability report found'}), 404

        text_content = document_handler.get_document_content(report_data['url'])
        if not text_content:
            return jsonify({'error': 'Failed to extract text from document'}), 500

        emissions_data = analyzer.extract_emissions_data(text_content, company_name)
        if not emissions_data:
            return jsonify({'error': 'No emissions data found'}), 404

        result = {
            'company': company_name,
            'report_url': report_data['url'],
            'report_year': report_data['year'],
            'emissions_data': emissions_data,
            'processed_at': datetime.utcnow().isoformat()
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)