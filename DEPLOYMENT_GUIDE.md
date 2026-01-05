# Deployment Guide

This guide provides detailed instructions for deploying the Algorithmic Swing Trading System.

## Prerequisites

- Python 3.10 or higher
- MySQL 8.0 or higher
- Docker and Docker Compose (for containerized deployment)
- Questrade account with API access
- Interactive Brokers account (paper or live trading)
- TA-Lib library installed

## Installation Methods

### Method 1: Docker Deployment (Recommended)

This is the easiest method and handles all dependencies automatically.

#### 1. Clone the Repository

```bash
git clone https://github.com/bhaskarrishi/algo-swing-trader.git
cd algo-swing-trader
```

#### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` file with your credentials:
- MySQL database credentials
- Questrade refresh token and API URL
- Interactive Brokers connection details
- Risk management parameters
- Strategy settings

#### 3. Start Services

```bash
docker-compose up -d
```

This will start:
- MySQL database
- Trading application

#### 4. Initialize Database

```bash
docker-compose exec app python scripts/init_db.py
```

#### 5. Access the Application

- Dashboard: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

### Method 2: Manual Installation

For development or custom deployment scenarios.

#### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y gcc g++ python3-dev libmysqlclient-dev pkg-config wget
```

**macOS:**
```bash
brew install mysql-client pkg-config
```

#### 2. Install TA-Lib

**Linux:**
```bash
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ..
rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
```

**macOS:**
```bash
brew install ta-lib
```

#### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 4. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Setup MySQL Database

Create database and user:

```sql
CREATE DATABASE algo_trader;
CREATE USER 'trader'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON algo_trader.* TO 'trader'@'localhost';
FLUSH PRIVILEGES;
```

#### 6. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

#### 7. Initialize Database

```bash
python scripts/init_db.py
```

#### 8. Start Application

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Configuration

### Environment Variables

Key configuration parameters in `.env`:

#### Database Configuration
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=algo_trader
MYSQL_USER=trader
MYSQL_PASSWORD=your_secure_password
```

#### Questrade API
```
QUESTRADE_REFRESH_TOKEN=your_token_here
QUESTRADE_API_URL=https://api01.iq.questrade.com
```

#### Interactive Brokers
```
IBKR_HOST=127.0.0.1
IBKR_PORT=7497  # 7497 for paper trading, 7496 for live
IBKR_CLIENT_ID=1
IBKR_ACCOUNT=your_account_id
```

#### Risk Management
```
MAX_POSITION_RISK_PCT=2.0
MAX_PORTFOLIO_RISK_PCT=10.0
MAX_DAILY_LOSS_PCT=3.0
MAX_DRAWDOWN_PCT=10.0
MAX_CONCURRENT_POSITIONS=5
```

#### Strategy Parameters
```
STOP_LOSS_PCT=2.0
TAKE_PROFIT_MULTIPLIER=3.0
RSI_PERIOD=14
ADX_THRESHOLD=25
```

## Getting Questrade Credentials

1. Log in to your Questrade account
2. Go to Account Management
3. Navigate to API Settings
4. Generate a refresh token
5. Copy the token to your `.env` file

**Important:** 
- Refresh tokens expire after 3 days if not used
- Keep your refresh token secure
- Never commit it to version control

## Setting Up Interactive Brokers

1. Download and install IB TWS or IB Gateway
2. Configure API settings:
   - Enable ActiveX and Socket Clients
   - Set Socket port to 7497 (paper) or 7496 (live)
   - Add 127.0.0.1 to trusted IPs
3. Start TWS/Gateway
4. The application will connect automatically

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_indicators.py -v
```

## Monitoring and Maintenance

### Logs

Logs are stored in `logs/algo_trader.log` with rotation (max 10MB per file, 5 backups).

View logs:
```bash
tail -f logs/algo_trader.log
```

### Database Backups

Create backup:
```bash
mysqldump -u trader -p algo_trader > backup_$(date +%Y%m%d).sql
```

Restore backup:
```bash
mysql -u trader -p algo_trader < backup_20240101.sql
```

### Monitoring Endpoints

- Health Check: `GET /health`
- Strategy Status: `GET /api/strategy/status`
- Account Summary: `GET /api/dashboard/summary`

## Production Deployment

### Security Considerations

1. **Use HTTPS**: Configure a reverse proxy (nginx) with SSL
2. **Firewall**: Restrict database and application ports
3. **Strong Passwords**: Use complex passwords for all services
4. **API Authentication**: Implement JWT or OAuth2 authentication
5. **Rate Limiting**: Configure rate limiting on API endpoints
6. **Monitoring**: Set up monitoring and alerting

### Nginx Reverse Proxy

Example nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Systemd Service

Create `/etc/systemd/system/algo-trader.service`:

```ini
[Unit]
Description=Algorithmic Trading System
After=network.target mysql.service

[Service]
Type=simple
User=trader
WorkingDirectory=/home/trader/algo-swing-trader
Environment="PATH=/home/trader/algo-swing-trader/venv/bin"
ExecStart=/home/trader/algo-swing-trader/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable algo-trader
sudo systemctl start algo-trader
sudo systemctl status algo-trader
```

## Troubleshooting

### Database Connection Issues

- Verify MySQL is running: `systemctl status mysql`
- Check credentials in `.env`
- Test connection: `mysql -u trader -p`

### TA-Lib Import Error

- Reinstall TA-Lib system library
- Reinstall Python package: `pip install --upgrade TA-Lib`

### IBKR Connection Failed

- Ensure TWS/Gateway is running
- Check API settings in TWS
- Verify port number (7497 vs 7496)
- Check firewall settings

### Questrade Authentication Failed

- Refresh token may be expired
- Generate new token from Questrade account
- Update `.env` file

## Support

For issues and questions:
- GitHub Issues: https://github.com/bhaskarrishi/algo-swing-trader/issues
- Documentation: README.md

## Disclaimer

This software is for educational purposes only. Trading involves risk and you can lose money. Always do your own research and test thoroughly before live trading.
