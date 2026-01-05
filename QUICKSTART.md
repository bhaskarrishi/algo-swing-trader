# Quick Start Guide

Get up and running with the Algorithmic Swing Trading System in 5 minutes!

## 🚀 Quick Start (Docker)

### 1. Clone and Configure

```bash
git clone https://github.com/bhaskarrishi/algo-swing-trader.git
cd algo-swing-trader
cp .env.example .env
```

### 2. Edit Configuration

Edit `.env` file with your settings:
```bash
nano .env  # or use your favorite editor
```

**Minimum required settings:**
- MySQL password
- Questrade refresh token (if using market data)
- IBKR connection details (if using order execution)

### 3. Start Services

```bash
docker-compose up -d
```

### 4. Initialize Database

```bash
docker-compose exec app python scripts/init_db.py
```

### 5. Access Dashboard

Open your browser and navigate to:
- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📝 Basic Usage

### Starting the Trading Strategy

1. Go to the dashboard: http://localhost:8000
2. Click "Start Strategy" button
3. The system will begin scanning for trading signals

### Setting Up Watchlist

By default, the system monitors these popular stocks:
- AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, JPM, V, WMT

To customize the watchlist:

**Via API:**
```bash
curl -X POST http://localhost:8000/api/strategy/watchlist \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "GOOGL", "TSLA"]}'
```

**Via Python Script:**
```python
# scripts/populate_watchlist.py
python scripts/populate_watchlist.py
```

### Monitoring Trades

- **Active Positions**: View on dashboard homepage
- **Trade History**: Navigate to /trades
- **Performance Analytics**: Navigate to /analytics

### Stopping the Strategy

1. Click "Stop Strategy" button on dashboard
2. Or via API:
```bash
curl -X POST http://localhost:8000/api/strategy/stop
```

## 🔧 Testing Without Real Trading

### Paper Trading Mode

1. Use IBKR Paper Trading account
2. Set port to 7497 in `.env`:
```
IBKR_PORT=7497
```

### Simulation Mode

Run without connecting to brokers:
1. Don't start IBKR TWS/Gateway
2. System will still generate signals and track performance
3. Orders won't be executed

## 📊 Backtesting

Test your strategy on historical data:

```python
from backtest.backtester import Backtester
import pandas as pd

# Load historical data
data = pd.read_csv('historical_data.csv')

# Run backtest
backtester = Backtester(initial_capital=100000)
results = backtester.run(data, 'AAPL')

print(f"Total Return: {results['total_return']:.2f}%")
print(f"Win Rate: {results['win_rate']:.2f}%")
```

## 🧪 Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html
```

## 📱 API Endpoints

### Strategy Control
- `POST /api/strategy/start` - Start trading
- `POST /api/strategy/stop` - Stop trading
- `GET /api/strategy/status` - Get status

### Data Access
- `GET /api/trades/` - List all trades
- `GET /api/positions/` - List positions
- `GET /api/dashboard/summary` - Get dashboard data

### Complete API Documentation
Visit http://localhost:8000/docs for interactive API documentation.

## 🔒 Security Notes

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Use strong passwords** - Especially for production databases
3. **Enable HTTPS** - For production deployments
4. **Restrict access** - Use firewall rules in production

## ❓ Common Issues

### "Database connection failed"
- Ensure MySQL is running: `docker-compose ps`
- Check credentials in `.env`

### "TA-Lib not found"
- For Docker: Rebuild image: `docker-compose build`
- For local: Install TA-Lib library (see DEPLOYMENT_GUIDE.md)

### "IBKR connection failed"
- Start IB TWS or Gateway
- Check port number (7497 for paper, 7496 for live)
- Verify API settings in TWS

## 📚 Learn More

- **Full Documentation**: See README.md
- **Deployment Guide**: See DEPLOYMENT_GUIDE.md
- **Trading Strategy**: See problem statement in README.md

## 🆘 Getting Help

- GitHub Issues: Report bugs or request features
- Documentation: Check README.md and DEPLOYMENT_GUIDE.md
- Logs: Check `logs/algo_trader.log` for error details

## ⚠️ Important Disclaimer

This software is for educational purposes only. Trading involves significant risk and you can lose money. Always:
- Test thoroughly with paper trading first
- Understand the risks involved
- Never invest more than you can afford to lose
- Consult with a licensed financial advisor

## 🎉 Next Steps

Once you're comfortable with the basics:

1. **Customize the Strategy** - Modify parameters in `.env`
2. **Add More Indicators** - Extend `app/core/indicators.py`
3. **Tune Risk Management** - Adjust limits in `.env`
4. **Monitor Performance** - Use the analytics dashboard
5. **Backtest Changes** - Validate improvements historically

Happy Trading! 📈
