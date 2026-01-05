"""Configuration management for the algo trading system."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "algo_trader")
    MYSQL_USER: str = os.getenv("MYSQL_USER", "trader")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "password")
    
    # Questrade API
    QUESTRADE_REFRESH_TOKEN: str = os.getenv("QUESTRADE_REFRESH_TOKEN", "")
    QUESTRADE_API_URL: str = os.getenv("QUESTRADE_API_URL", "https://api01.iq.questrade.com")
    
    # Interactive Brokers
    IBKR_HOST: str = os.getenv("IBKR_HOST", "127.0.0.1")
    IBKR_PORT: int = int(os.getenv("IBKR_PORT", "7497"))
    IBKR_CLIENT_ID: int = int(os.getenv("IBKR_CLIENT_ID", "1"))
    IBKR_ACCOUNT: str = os.getenv("IBKR_ACCOUNT", "")
    
    # Risk Management
    MAX_POSITION_RISK_PCT: float = float(os.getenv("MAX_POSITION_RISK_PCT", "2.0"))
    MAX_PORTFOLIO_RISK_PCT: float = float(os.getenv("MAX_PORTFOLIO_RISK_PCT", "10.0"))
    MAX_DAILY_LOSS_PCT: float = float(os.getenv("MAX_DAILY_LOSS_PCT", "3.0"))
    MAX_DRAWDOWN_PCT: float = float(os.getenv("MAX_DRAWDOWN_PCT", "10.0"))
    MAX_CONCURRENT_POSITIONS: int = int(os.getenv("MAX_CONCURRENT_POSITIONS", "5"))
    MAX_POSITION_SIZE_PCT: float = float(os.getenv("MAX_POSITION_SIZE_PCT", "10.0"))
    MAX_TOTAL_DEPLOYED_PCT: float = float(os.getenv("MAX_TOTAL_DEPLOYED_PCT", "30.0"))
    
    # Strategy Parameters
    STOP_LOSS_PCT: float = float(os.getenv("STOP_LOSS_PCT", "2.0"))
    TAKE_PROFIT_MULTIPLIER: float = float(os.getenv("TAKE_PROFIT_MULTIPLIER", "3.0"))
    TRAILING_STOP_ATR_MULTIPLIER: float = float(os.getenv("TRAILING_STOP_ATR_MULTIPLIER", "2.0"))
    TIME_BASED_EXIT_DAYS: int = int(os.getenv("TIME_BASED_EXIT_DAYS", "10"))
    MIN_INDICATOR_CONFLUENCE: int = int(os.getenv("MIN_INDICATOR_CONFLUENCE", "3"))
    
    # Technical Indicators
    RSI_PERIOD: int = int(os.getenv("RSI_PERIOD", "14"))
    MACD_FAST: int = int(os.getenv("MACD_FAST", "12"))
    MACD_SLOW: int = int(os.getenv("MACD_SLOW", "26"))
    MACD_SIGNAL: int = int(os.getenv("MACD_SIGNAL", "9"))
    BOLLINGER_PERIOD: int = int(os.getenv("BOLLINGER_PERIOD", "20"))
    BOLLINGER_STD: float = float(os.getenv("BOLLINGER_STD", "2"))
    ATR_PERIOD: int = int(os.getenv("ATR_PERIOD", "14"))
    ADX_PERIOD: int = int(os.getenv("ADX_PERIOD", "14"))
    ADX_THRESHOLD: float = float(os.getenv("ADX_THRESHOLD", "25"))
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/algo_trader.log")
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Alert Settings
    ALERT_EMAIL: Optional[str] = os.getenv("ALERT_EMAIL")
    SMTP_SERVER: Optional[str] = os.getenv("SMTP_SERVER")
    SMTP_PORT: Optional[int] = int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else None
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    
    @property
    def database_url(self) -> str:
        """Get database connection URL."""
        return f"mysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


settings = Settings()
