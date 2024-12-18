// Handle search type changes
document.getElementById('searchType').addEventListener('change', function(e) {
    const isISIN = e.target.value === 'isin';
    const label = document.getElementById('identifierLabel');
    const validation = document.getElementById('isinValidation');
    
    label.textContent = isISIN ? 'ISIN' : 'Company Name';
    validation.classList.toggle('hidden', !isISIN);
});

// Real-time ISIN validation
document.getElementById('identifier').addEventListener('input', async function(e) {
    const searchType = document.getElementById('searchType').value;
    const validation = document.getElementById('isinValidation');
    
    if (searchType !== 'isin') {
        validation.classList.add('hidden');
        return;
    }

    const isin = e.target.value.trim();
    if (!isin) {
        validation.classList.add('hidden');
        return;
    }

    try {
        const response = await fetch(`/validate-isin/${isin}`);
        const data = await response.json();
        
        if (data.valid) {
            validation.textContent = data.company_name ? 
                `Valid ISIN for ${data.company_name}` : 
                'Valid ISIN format';
            validation.classList.remove('text-red-500');
            validation.classList.add('text-green-500');
        } else {
            validation.textContent = data.error || 'Invalid ISIN';
            validation.classList.remove('text-green-500');
            validation.classList.add('text-red-500');
        }
        validation.classList.remove('hidden');
        
    } catch (error) {
        console.error('ISIN validation error:', error);
    }
});

// Form submission
document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const identifier = document.getElementById('identifier').value.trim();
    const searchType = document.getElementById('searchType').value;
    
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
                id_type: searchType
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze emissions data');
        }
        
        // Update results display
        updateResults(data);
        document.getElementById('results').classList.remove('hidden');
        
    } catch (error) {
        document.getElementById('error-message').textContent = error.message;
        document.getElementById('error').classList.remove('hidden');
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
});

// Update results with charts
function updateResults(data) {
    // Update company info
    const companyInfo = document.getElementById('companyInfo');
    companyInfo.innerHTML = `
        <div><strong>Company:</strong> ${data.company}</div>
        ${data.original_isin ? `<div><strong>ISIN:</strong> ${data.original_isin}</div>` : ''}
        ${data.emissions_data.sector ? `<div><strong>Sector:</strong> ${data.emissions_data.sector}</div>` : ''}
        <div><strong>Report Year:</strong> ${data.report_year}</div>
    `;

    // Update raw data display
    document.getElementById('json-display').textContent = JSON.stringify(data, null, 2);

    // Create emissions overview chart
    const currentYear = data.emissions_data.current_year;
    createEmissionsChart(currentYear);

    // Create historical chart if data available
    if (data.emissions_data.previous_years && data.emissions_data.previous_years.length > 0) {
        document.getElementById('historicalData').classList.remove('hidden');
        createHistoricalChart(data.emissions_data);
    } else {
        document.getElementById('historicalData').classList.add('hidden');
    }
}

// Create current year emissions chart
function createEmissionsChart(data) {
    const ctx = document.getElementById('emissionsChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Scope 1', 'Scope 2 (Market)', 'Scope 2 (Location)'],
            datasets: [{
                label: 'Emissions (tCO2e)',
                data: [
                    data.scope_1.value,
                    data.scope_2_market_based.value,
                    data.scope_2_location_based.value
                ],
                backgroundColor: [
                    'rgba(54, 162, 235, 0.5)',
                    'rgba(75, 192, 192, 0.5)',
                    'rgba(153, 102, 255, 0.5)'
                ],
                borderColor: [
                    'rgb(54, 162, 235)',
                    'rgb(75, 192, 192)',
                    'rgb(153, 102, 255)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Current Year Emissions'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Metric Tons CO2e'
                    }
                }
            }
        }
    });
}

// Create historical emissions chart
function createHistoricalChart(data) {
    const years = [data.current_year, ...data.previous_years].map(d => d.year);
    const scope1Data = [data.current_year, ...data.previous_years].map(d => d.scope_1.value);
    const scope2MarketData = [data.current_year, ...data.previous_years].map(d => d.scope_2_market_based.value);
    const scope2LocationData = [data.current_year, ...data.previous_years].map(d => d.scope_2_location_based.value);

    const ctx = document.getElementById('historicalChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [
                {
                    label: 'Scope 1',
                    data: scope1Data,
                    borderColor: 'rgb(54, 162, 235)',
                    tension: 0.1
                },
                {
                    label: 'Scope 2 (Market)',
                    data: scope2MarketData,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                },
                {
                    label: 'Scope 2 (Location)',
                    data: scope2LocationData,
                    borderColor: 'rgb(153, 102, 255)',
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Historical Emissions Trends'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Metric Tons CO2e'
                    }
                }
            }
        }
    });
}

// Download functionality
function downloadData() {
    const data = JSON.parse(document.getElementById('json-display').textContent);
    const company = data.company.toLowerCase().replace(/\s+/g, '_');
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${company}_emissions.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}