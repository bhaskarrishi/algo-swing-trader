# Professional Algorithmic Swing Trading System

A production-ready algorithmic trading platform for swing trading US equity stocks with emphasis on capital preservation, consistent profits, and minimal drawdown.

## 🎯 Features

- **Real-time Market Data**: WebSocket integration with Questrade API
- **Advanced Technical Analysis**: 15+ technical indicators (RSI, MACD, Bollinger Bands, etc.)
- **Battle-Tested Strategy**: Multi-timeframe analysis with confluence-based signals
- **Risk Management**: Position sizing, drawdown protection, portfolio limits
- **Order Execution**: Interactive Brokers API integration
- **Web Dashboard**: Real-time monitoring, P&L tracking, performance analytics
- **Backtesting Engine**: Historical strategy validation
- **MySQL Database**: Persistent storage of trades, positions, and market data

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Questrade API  │────▶│  Market Data     │────▶│  Technical      │
│  (WebSocket)    │     │  Pipeline        │     │  Indicators     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  FastAPI        │◀────│  Trading         │◀────│  Signal         │
│  Dashboard      │     │  Strategy        │     │  Generation     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │                          │
                                ▼                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  IBKR API       │◀────│  Risk            │◀────│  Position       │
│  (Orders)       │     │  Management      │     │  Sizing         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │  MySQL Database  │
                        └──────────────────┘
```

## 📁 Project Structure

```
algo-swing-trader/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connection
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── routers/                # API routes
│   ├── services/               # Business logic
│   ├── core/                   # Core functionality
│   └── utils/                  # Utilities
├── static/                     # Frontend assets
├── templates/                  # HTML templates
├── tests/                      # Unit tests
├── backtest/                   # Backtesting module
├── scripts/                    # Utility scripts
├── requirements.txt
├── docker-compose.yml
└── Dockerfile
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- MySQL 8.0 or higher
- Docker and Docker Compose (optional)
- Questrade account with API access
- Interactive Brokers account (paper or live)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/bhaskarrishi/algo-swing-trader.git
   cd algo-swing-trader
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**
   ```bash
   python scripts/init_db.py
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Access the dashboard**
   ```
   Open browser: http://localhost:8000
   ```

### Docker Installation (Recommended)

1. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

2. **Start the services**
   ```bash
   docker-compose up -d
   ```

3. **Initialize database**
   ```bash
   docker-compose exec app python scripts/init_db.py
   ```

4. **Access the dashboard**
   ```
   Open browser: http://localhost:8000
   ```

## 📊 Trading Strategy

### Entry Conditions (LONG)
1. Price above 50 EMA and 200 EMA (uptrend confirmation)
2. RSI between 40-60 (not overbought/oversold)
3. MACD crossover (bullish) or histogram growing
4. Price near support level or bouncing off lower Bollinger Band
5. Volume above average (confirmation)
6. ADX > 25 (strong trend)

### Entry Conditions (SHORT)
1. Price below 50 EMA and 200 EMA (downtrend confirmation)
2. RSI between 40-60
3. MACD crossover (bearish)
4. Price near resistance or touching upper Bollinger Band
5. Volume above average
6. ADX > 25

### Exit Conditions
- **Stop Loss**: 2% below entry (LONG) or above entry (SHORT)
- **Take Profit**: 2:1 or 3:1 risk-reward ratio
- **Trailing Stop**: ATR-based trailing stop after 1:1 profit reached
- **Time-based**: Close position after 10 days if no movement
- **Technical**: Opposite signal generated

## 🛡️ Risk Management

- **Position Sizing**: Maximum 2% risk per trade
- **Portfolio Limits**: Maximum 10% in single position, 30% total deployed
- **Concurrent Positions**: Maximum 5 positions
- **Daily Loss Limit**: Stop trading if down 3% in one day
- **Maximum Drawdown**: 10% from peak equity
- **Circuit Breaker**: Pause trading and alert if limits hit

## 📈 API Endpoints

### Dashboard
- `GET /` - Main dashboard
- `GET /trades` - Trade history page
- `GET /analytics` - Performance analytics page

### API Routes
- `GET /api/positions` - Current positions
- `GET /api/trades` - Trade history
- `GET /api/orders` - Order history
- `GET /api/account` - Account status
- `POST /api/strategy/start` - Start trading
- `POST /api/strategy/stop` - Stop trading
- `GET /api/alerts` - Active alerts

## 🧪 Testing

Run unit tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```

## 🔐 Security

- **Never commit credentials** - Use `.env` file (already in `.gitignore`)
- **API key encryption** at rest
- **Input validation** on all endpoints
- **Rate limiting** on API calls
- **Comprehensive logging** for audit trail

## 📝 Configuration

Edit `.env` file to configure:
- Database connection
- Questrade API credentials
- Interactive Brokers connection
- Risk management parameters
- Strategy parameters
- Alert settings

## 🔧 Backtesting

Run backtests:
```bash
python backtest/backtester.py --start 2023-01-01 --end 2023-12-31
```

## 📚 Documentation

- API Documentation: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## ⚠️ Disclaimer

This software is for educational purposes only. Trading stocks involves risk and you can lose money. Past performance does not guarantee future results. Always do your own research and consult with a licensed financial advisor before trading.

## 📄 License

MIT License - See LICENSE file for details

## 👤 Author

Bhaskar Rishi

## 🙏 Acknowledgments

- Questrade API for market data
- Interactive Brokers for order execution
- FastAPI framework
- TA-Lib for technical indicators
