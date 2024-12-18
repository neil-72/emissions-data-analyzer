from flask import Flask, render_template, request, jsonify, send_file
from ..search.brave_search import BraveSearchClient
from ..analysis.claude_analyzer import EmissionsAnalyzer
from ..extraction.pdf_handler import DocumentHandler
from ..search.isin_lookup import ISINLookup
import json
import os
from datetime import datetime

app = Flask(__name__)

# Initialize our components
search_client = BraveSearchClient()
analyzer = EmissionsAnalyzer()
document_handler = DocumentHandler()
isin_lookup = ISINLookup()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        identifier = data.get('identifier')
        id_type = data.get('id_type', 'company')  # 'company' or 'isin'
        
        if not identifier:
            return jsonify({'error': 'Company name or ISIN required'}), 400

        # Convert ISIN to company name if needed
        company_name = identifier
        if id_type == 'isin':
            company_name = isin_lookup.get_company_name(identifier)
            if not company_name:
                return jsonify({'error': 'Could not find company name for given ISIN'}), 404

        # Use existing functionality with company name
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
            'original_isin': identifier if id_type == 'isin' else None,
            'report_url': report_data['url'],
            'report_year': report_data['year'],
            'emissions_data': emissions_data,
            'processed_at': datetime.utcnow().isoformat()
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/validate-isin/<isin>')
def validate_isin(isin):
    """Endpoint to validate ISIN and return company name if found."""
    try:
        company_name = isin_lookup.get_company_name(isin)
        if company_name:
            return jsonify({
                'valid': True,
                'company_name': company_name
            })
        return jsonify({
            'valid': False,
            'error': 'Company not found for ISIN'
        })
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': str(e)
        })

@app.route('/download/<format>')
def download(format):
    try:
        data = request.args.get('data')
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        data = json.loads(data)
        company_name = data['company'].lower().replace(' ', '_')
        
        if format == 'json':
            filename = f"{company_name}_emissions.json"
            return send_file(
                filename,
                as_attachment=True,
                download_name=filename,
                mimetype='application/json'
            )
        else:
            return jsonify({'error': 'Unsupported format'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
