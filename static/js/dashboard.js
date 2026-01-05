// Dashboard JavaScript
let equityChart, pnlChart;

// Initialize dashboard
async function initDashboard() {
    await loadDashboardData();
    await loadChartData();
    await loadRecentTrades();
    await loadOpenPositions();
    checkStrategyStatus();
    
    // Refresh data every 10 seconds
    setInterval(loadDashboardData, 10000);
    setInterval(loadOpenPositions, 10000);
}

// Load dashboard summary data
async function loadDashboardData() {
    try {
        const response = await fetch('/api/dashboard/summary');
        const data = await response.json();
        
        // Update account metrics
        document.getElementById('totalEquity').textContent = formatCurrency(data.account.total_equity);
        document.getElementById('dailyPnl').textContent = formatCurrency(data.account.daily_pnl);
        document.getElementById('dailyPnl').className = 'metric ' + (data.account.daily_pnl >= 0 ? 'positive' : 'negative');
        
        document.getElementById('totalPnl').textContent = formatCurrency(data.account.total_pnl);
        document.getElementById('totalPnl').className = 'metric ' + (data.account.total_pnl >= 0 ? 'positive' : 'negative');
        
        document.getElementById('winRate').textContent = data.performance.win_rate.toFixed(1) + '%';
        document.getElementById('openPositions').textContent = data.account.open_positions_count;
        document.getElementById('maxDrawdown').textContent = data.account.max_drawdown_pct.toFixed(2) + '%';
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Load chart data
async function loadChartData() {
    try {
        const response = await fetch('/api/dashboard/chart-data');
        const data = await response.json();
        
        // Equity curve chart
        createEquityChart(data.equity_curve);
        
        // Daily P&L chart
        createPnlChart(data.daily_pnl);
        
    } catch (error) {
        console.error('Error loading chart data:', error);
    }
}

// Create equity curve chart
function createEquityChart(data) {
    const ctx = document.getElementById('equityChart').getContext('2d');
    
    if (equityChart) {
        equityChart.destroy();
    }
    
    equityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => new Date(d.timestamp).toLocaleDateString()),
            datasets: [{
                label: 'Equity',
                data: data.map(d => d.equity),
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

// Create daily P&L chart
function createPnlChart(data) {
    const ctx = document.getElementById('pnlChart').getContext('2d');
    
    if (pnlChart) {
        pnlChart.destroy();
    }
    
    pnlChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => new Date(d.date).toLocaleDateString()),
            datasets: [{
                label: 'Daily P&L',
                data: data.map(d => d.pnl),
                backgroundColor: data.map(d => d.pnl >= 0 ? '#10b981' : '#ef4444')
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

// Load recent trades
async function loadRecentTrades() {
    try {
        const response = await fetch('/api/dashboard/recent-trades?limit=10');
        const trades = await response.json();
        
        const tbody = document.getElementById('tradesTableBody');
        
        if (trades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No trades yet</td></tr>';
            return;
        }
        
        tbody.innerHTML = trades.map(trade => `
            <tr>
                <td>${trade.symbol}</td>
                <td>${trade.side}</td>
                <td>${trade.quantity}</td>
                <td>$${trade.entry_price.toFixed(2)}</td>
                <td>${trade.exit_price ? '$' + trade.exit_price.toFixed(2) : '-'}</td>
                <td class="${trade.pnl >= 0 ? 'positive' : 'negative'}">${formatCurrency(trade.pnl)}</td>
                <td class="${trade.pnl_percent >= 0 ? 'positive' : 'negative'}">${trade.pnl_percent ? trade.pnl_percent.toFixed(2) + '%' : '-'}</td>
                <td>${trade.exit_reason || '-'}</td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading recent trades:', error);
    }
}

// Load open positions
async function loadOpenPositions() {
    try {
        const response = await fetch('/api/positions/open-trades/all');
        const positions = await response.json();
        
        const tbody = document.getElementById('positionsTableBody');
        
        if (positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No open positions</td></tr>';
            return;
        }
        
        tbody.innerHTML = positions.map(pos => `
            <tr>
                <td>${pos.symbol}</td>
                <td>${pos.side}</td>
                <td>${pos.quantity}</td>
                <td>$${pos.entry_price.toFixed(2)}</td>
                <td>$${pos.current_price.toFixed(2)}</td>
                <td class="${pos.unrealized_pnl >= 0 ? 'positive' : 'negative'}">${formatCurrency(pos.unrealized_pnl)}</td>
                <td>$${pos.stop_loss.toFixed(2)}</td>
                <td>$${pos.take_profit.toFixed(2)}</td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading open positions:', error);
    }
}

// Check strategy status
async function checkStrategyStatus() {
    try {
        const response = await fetch('/api/strategy/status');
        const data = await response.json();
        
        const statusBadge = document.getElementById('strategyStatus');
        statusBadge.textContent = data.running ? 'Running' : 'Stopped';
        statusBadge.className = 'status-badge ' + (data.running ? 'status-running' : 'status-stopped');
        
    } catch (error) {
        console.error('Error checking strategy status:', error);
    }
}

// Start strategy
document.getElementById('startBtn').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/strategy/start', { method: 'POST' });
        const data = await response.json();
        alert(data.message);
        checkStrategyStatus();
    } catch (error) {
        alert('Error starting strategy: ' + error.message);
    }
});

// Stop strategy
document.getElementById('stopBtn').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/strategy/stop', { method: 'POST' });
        const data = await response.json();
        alert(data.message);
        checkStrategyStatus();
    } catch (error) {
        alert('Error stopping strategy: ' + error.message);
    }
});

// Utility function to format currency
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value || 0);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initDashboard);
