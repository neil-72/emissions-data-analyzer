// ISIN validation timeout
let isinValidationTimeout = null;

// Update UI based on identifier type
document.getElementById('identifier-type').addEventListener('change', (e) => {
    const isISIN = e.target.value === 'isin';
    document.getElementById('identifier-label').textContent = isISIN ? 'Enter ISIN' : 'Enter Company Name';
    document.getElementById('company-preview').classList.add('hidden');
    document.getElementById('validation-message').classList.add('hidden');
    document.getElementById('identifier').value = '';
});

// Real-time ISIN validation
document.getElementById('identifier').addEventListener('input', async (e) => {
    if (document.getElementById('identifier-type').value !== 'isin') return;

    clearTimeout(isinValidationTimeout);
    const isin = e.target.value.trim().toUpperCase();

    if (isin.length === 12) {
        isinValidationTimeout = setTimeout(async () => {
            try {
                const response = await fetch(`/validate-isin/${isin}`);
                const data = await response.json();

                if (data.valid) {
                    document.getElementById('company-name-display').textContent = data.company_name;
                    document.getElementById('company-preview').classList.remove('hidden');
                    document.getElementById('validation-message').classList.add('hidden');
                } else {
                    document.getElementById('validation-message').textContent = data.error;
                    document.getElementById('validation-message').classList.remove('hidden');
                    document.getElementById('company-preview').classList.add('hidden');
                }
            } catch (error) {
                document.getElementById('validation-message').textContent = 'Error validating ISIN';
                document.getElementById('validation-message').classList.remove('hidden');
                document.getElementById('company-preview').classList.add('hidden');
            }
        }, 500);
    } else {
        document.getElementById('company-preview').classList.add('hidden');
        if (isin.length > 0) {
            document.getElementById('validation-message').textContent = 'ISIN must be exactly 12 characters';
            document.getElementById('validation-message').classList.remove('hidden');
        } else {
            document.getElementById('validation-message').classList.add('hidden');
        }
    }
});

// Form submission
document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const identifier = document.getElementById('identifier').value.trim();
    const idType = document.getElementById('identifier-type').value;
    
    if (!identifier) return;

    // Show loading, hide results and error
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
    document.getElementById('error').classList.add('hidden');
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                identifier: identifier,
                id_type: idType
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze emissions data');
        }
        
        // Update company info
        document.getElementById('company-details').innerHTML = `
            <p><strong>Company:</strong> ${data.company}</p>
            ${data.original_isin ? `<p><strong>ISIN:</strong> ${data.original_isin}</p>` : ''}
            <p><strong>Report Year:</strong> ${data.report_year}</p>
        `;

        // Update results display
        document.getElementById('json-display').textContent = JSON.stringify(data.emissions_data, null, 2);
        document.getElementById('results').classList.remove('hidden');
        
    } catch (error) {
        document.getElementById('error-message').textContent = error.message;
        document.getElementById('error').classList.remove('hidden');
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
});

// Download functionality
function downloadData(format) {
    const data = JSON.parse(document.getElementById('json-display').textContent);
    const company = document.getElementById('company-details').querySelector('p').textContent.split(':')[1].trim();
    
    if (format === 'json') {
        downloadJson(data, company);
    } else if (format === 'csv') {
        downloadCsv(data, company);
    }
}

function downloadJson(data, company) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${company.toLowerCase().replace(/\s+/g, '_')}_emissions.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function downloadCsv(data, company) {
    // Convert emissions data to CSV format
    const rows = [];
    rows.push(['Metric', 'Value', 'Unit']);
    
    if (data.scope_1) {
        rows.push(['Scope 1', data.scope_1.value, data.scope_1.unit]);
    }
    if (data.scope_2) {
        rows.push(['Scope 2', data.scope_2.value, data.scope_2.unit]);
    }
    if (data.scope_2_market_based) {
        rows.push(['Scope 2 (Market-based)', data.scope_2_market_based.value, data.scope_2_market_based.unit]);
    }
    if (data.scope_2_location_based) {
        rows.push(['Scope 2 (Location-based)', data.scope_2_location_based.value, data.scope_2_location_based.unit]);
    }

    const csvContent = rows.map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${company.toLowerCase().replace(/\s+/g, '_')}_emissions.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}