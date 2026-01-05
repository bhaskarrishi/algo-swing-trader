// Analytics page JavaScript
let symbolChart, sideChart;

async function loadAnalytics() {
    await loadPerformanceMetrics();
    await loadDistributionCharts();
    await loadRiskMetrics();
}

// Load performance metrics
async function loadPerformanceMetrics() {
    try {
        const response = await fetch('/api/dashboard/summary');
        const data = await response.json();
        
        document.getElementById('totalTrades').textContent = data.performance.total_trades;
        document.getElementById('winningTrades').textContent = data.performance.winning_trades;
        document.getElementById('losingTrades').textContent = data.performance.losing_trades;
        document.getElementById('profitFactor').textContent = data.performance.profit_factor.toFixed(2);
        document.getElementById('avgWin').textContent = formatCurrency(data.performance.avg_win);
        document.getElementById('avgLoss').textContent = formatCurrency(data.performance.avg_loss);
        
    } catch (error) {
        console.error('Error loading performance metrics:', error);
    }
}

// Load distribution charts
async function loadDistributionCharts() {
    try {
        const response = await fetch('/api/dashboard/chart-data');
        const data = await response.json();
        
        // Symbol distribution chart
        createSymbolChart(data.distribution.by_symbol);
        
        // Side distribution chart
        createSideChart(data.distribution.by_side);
        
    } catch (error) {
        console.error('Error loading distribution charts:', error);
    }
}

// Create symbol chart
function createSymbolChart(data) {
    const ctx = document.getElementById('symbolChart').getContext('2d');
    
    if (symbolChart) {
        symbolChart.destroy();
    }
    
    symbolChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.symbol),
            datasets: [{
                label: 'Total P&L',
                data: data.map(d => d.total_pnl),
                backgroundColor: data.map(d => d.total_pnl >= 0 ? '#10b981' : '#ef4444')
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Create side chart
function createSideChart(data) {
    const ctx = document.getElementById('sideChart').getContext('2d');
    
    if (sideChart) {
        sideChart.destroy();
    }
    
    sideChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.map(d => d.side),
            datasets: [{
                data: data.map(d => Math.abs(d.total_pnl)),
                backgroundColor: ['#667eea', '#764ba2']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true
        }
    });
}

// Load risk metrics
async function loadRiskMetrics() {
    try {
        const response = await fetch('/api/dashboard/summary');
        const data = await response.json();
        
        // Circuit breaker
        const cbElement = document.getElementById('circuitBreaker');
        cbElement.textContent = data.risk.circuit_breaker_active ? 'Active' : 'Inactive';
        cbElement.className = 'badge ' + (data.risk.circuit_breaker_active ? 'badge-danger' : 'badge-success');
        
        // Other metrics would be loaded here
        document.getElementById('positionLimits').textContent = 'OK';
        document.getElementById('dailyLossLimit').textContent = 'OK';
        document.getElementById('drawdownLimit').textContent = 'OK';
        
    } catch (error) {
        console.error('Error loading risk metrics:', error);
    }
}

// Utility function
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value || 0);
}

// Load analytics on page load
document.addEventListener('DOMContentLoaded', loadAnalytics);
