from flask import Flask, render_template, request, jsonify
import logging
from src.search.brave_search import BraveSearchClient
from src.analysis.claude_analyzer import EmissionsAnalyzer
from src.extraction.pdf_handler import DocumentHandler
from src.isin.isin_lookup import ISINLookup
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
    logging.info(f"Validating ISIN: {isin}")
    
    if not isin_lookup.validate_isin(isin):
        logging.warning(f"Invalid ISIN format: {isin}")
        return jsonify({
            'valid': False,
            'error': 'Invalid ISIN format'
        }), 400

    company_info = isin_lookup.get_company_info(isin)
    if not company_info:
        logging.warning(f"No company found for ISIN: {isin}")
        return jsonify({
            'valid': True,
            'error': 'Company not found'
        }), 404

    logging.info(f"Found company info for ISIN {isin}: {company_info['name']}")
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
        id_type = data.get('id_type', 'company')
        
        logging.info(f"\n{'='*50}")
        logging.info(f"New Analysis Request: {identifier} (Type: {id_type})")
        logging.info(f"{'='*50}")

        if not identifier:
            logging.error("Empty identifier provided")
            return jsonify({'error': 'Identifier required'}), 400

        # Handle ISIN input
        company_name = None
        original_isin = None
        company_info = None

        if id_type == 'isin':
            if not isin_lookup.validate_isin(identifier):
                logging.error(f"Invalid ISIN format: {identifier}")
                return jsonify({'error': 'Invalid ISIN format'}), 400
            company_info = isin_lookup.get_company_info(identifier)
            if not company_info:
                logging.error(f"Company not found for ISIN: {identifier}")
                return jsonify({'error': 'Company not found for ISIN'}), 404
            company_name = company_info['name']
            original_isin = identifier
            logging.info(f"Resolved ISIN {identifier} to company {company_name}")
        else:
            company_name = identifier
            resolved_isin = isin_lookup.resolve_company_name(company_name)
            if resolved_isin:
                company_info = isin_lookup.get_company_info(resolved_isin)
                original_isin = resolved_isin
                logging.info(f"Found ISIN {resolved_isin} for company {company_name}")

        # Search for sustainability report
        logging.info("\nStarting sustainability report search...")
        report_data = search_client.search_sustainability_report(company_name)
        
        if report_data:
            logging.info(f"\nReport found: {report_data['url']}")
            logging.info("Extracting text content...")
            
            text_content = document_handler.get_document_content(report_data['url'])
            if text_content:
                logging.info(f"Successfully extracted {len(text_content):,} characters")
                
                logging.info("\nAnalyzing emissions data...")
                emissions_data = analyzer.extract_emissions_data(text_content, company_name)
                
                if emissions_data:
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

                    logging.info("\nAnalysis complete ✓")
                    return jsonify(result)
                else:
                    logging.error("No emissions data found in report")
                    return jsonify({'error': 'No emissions data found'}), 404
            else:
                logging.error("Failed to extract text from document")
                return jsonify({'error': 'Failed to extract text'}), 500
        else:
            logging.error("No sustainability report found")
            return jsonify({'error': 'No report found'}), 404

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)