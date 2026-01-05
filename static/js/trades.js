// Trades page JavaScript
async function loadTrades(status = '', symbol = '') {
    try {
        let url = '/api/trades/?limit=100';
        if (status) url += `&status=${status}`;
        if (symbol) url += `&symbol=${symbol}`;
        
        const response = await fetch(url);
        const trades = await response.json();
        
        const tbody = document.getElementById('tradesBody');
        
        if (trades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="12" style="text-align: center;">No trades found</td></tr>';
            return;
        }
        
        tbody.innerHTML = trades.map(trade => `
            <tr>
                <td>${trade.id}</td>
                <td>${trade.symbol}</td>
                <td>${trade.side}</td>
                <td>${trade.quantity}</td>
                <td>$${trade.entry_price.toFixed(2)}</td>
                <td>${trade.exit_price ? '$' + trade.exit_price.toFixed(2) : '-'}</td>
                <td>${new Date(trade.entry_time).toLocaleString()}</td>
                <td>${trade.exit_time ? new Date(trade.exit_time).toLocaleString() : '-'}</td>
                <td class="${trade.pnl && trade.pnl >= 0 ? 'positive' : 'negative'}">${trade.pnl ? formatCurrency(trade.pnl) : '-'}</td>
                <td class="${trade.pnl_percent && trade.pnl_percent >= 0 ? 'positive' : 'negative'}">${trade.pnl_percent ? trade.pnl_percent.toFixed(2) + '%' : '-'}</td>
                <td><span class="badge badge-${trade.status === 'OPEN' ? 'success' : 'secondary'}">${trade.status}</span></td>
                <td>${trade.exit_reason || '-'}</td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading trades:', error);
        alert('Failed to load trades');
    }
}

// Apply filters
document.getElementById('applyFilters').addEventListener('click', () => {
    const status = document.getElementById('statusFilter').value;
    const symbol = document.getElementById('symbolFilter').value.toUpperCase();
    loadTrades(status, symbol);
});

// Utility function
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value || 0);
}

// Load trades on page load
document.addEventListener('DOMContentLoaded', () => loadTrades());
