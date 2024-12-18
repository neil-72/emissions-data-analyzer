// Form submission
document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const company = document.getElementById('company').value.trim();
    if (!company) return;

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
                identifier: company
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze emissions data');
        }
        
        // Update results display
        document.getElementById('json-display').textContent = JSON.stringify(data, null, 2);
        document.getElementById('results').classList.remove('hidden');
        
    } catch (error) {
        document.getElementById('error-message').textContent = error.message;
        document.getElementById('error').classList.remove('hidden');
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
});

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
