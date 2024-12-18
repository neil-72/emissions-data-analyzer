from flask import Flask, render_template, request, jsonify
from src.search.brave_search import BraveSearchClient
from src.analysis.claude_analyzer import EmissionsAnalyzer
from src.extraction.pdf_handler import DocumentHandler
from src.isin.isin_lookup import ISINLookup
import json
from datetime import datetime

app = Flask(__name__)

# Initialize components
search_client = BraveSearchClient()
analyzer = EmissionsAnalyzer()
document_handler = DocumentHandler()
isin_lookup = ISINLookup()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/validate-isin/<isin>')
def validate_isin(isin):
    """Validate ISIN and return company info"""
    if not isin_lookup.validate_isin(isin):
        return jsonify({
            'valid': False,
            'error': 'Invalid ISIN format'
        }), 400

    company_info = isin_lookup.get_company_info(isin)
    if not company_info:
        return jsonify({
            'valid': True,
            'error': 'Company not found'
        }), 404

    return jsonify({
        'valid': True,
        'company_name': company_info['name'],
        'sector': company_info.get('sector'),
        'country': company_info.get('country')
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        identifier = data.get('identifier')
        id_type = data.get('id_type', 'company')  # 'company' or 'isin'
        
        if not identifier:
            return jsonify({'error': 'Identifier required'}), 400

        # Handle ISIN input
        company_name = None
        original_isin = None
        company_info = None

        if id_type == 'isin':
            if not isin_lookup.validate_isin(identifier):
                return jsonify({'error': 'Invalid ISIN format'}), 400
            company_info = isin_lookup.get_company_info(identifier)
            if not company_info:
                return jsonify({'error': 'Company not found for ISIN'}), 404
            company_name = company_info['name']
            original_isin = identifier
        else:
            company_name = identifier
            # Try to resolve ISIN from company name
            resolved_isin = isin_lookup.resolve_company_name(company_name)
            if resolved_isin:
                company_info = isin_lookup.get_company_info(resolved_isin)
                original_isin = resolved_isin

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

        # Add company info if available
        if company_info:
            emissions_data['sector'] = company_info.get('sector')
            emissions_data['country'] = company_info.get('country')

        result = {
            'company': company_name,
            'original_isin': original_isin,
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