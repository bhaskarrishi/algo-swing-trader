"""Helper utilities."""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd


def calculate_pnl(entry_price: float, exit_price: float, quantity: int, side: str) -> float:
    """Calculate profit/loss for a trade."""
    if side == "BUY":
        return (exit_price - entry_price) * quantity
    else:  # SELL (short)
        return (entry_price - exit_price) * quantity


def calculate_pnl_percent(entry_price: float, exit_price: float, side: str) -> float:
    """Calculate profit/loss percentage."""
    if side == "BUY":
        return ((exit_price - entry_price) / entry_price) * 100
    else:  # SELL (short)
        return ((entry_price - exit_price) / entry_price) * 100


def is_market_hours() -> bool:
    """Check if current time is within US market hours (9:30 AM - 4:00 PM ET)."""
    # This is a simplified version - production should use proper timezone handling
    now = datetime.now()
    if now.weekday() >= 5:  # Weekend
        return False
    
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_open <= now <= market_close


def format_currency(value: float) -> str:
    """Format value as currency."""
    return f"${value:,.2f}"


def format_percent(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.2f}%"


def get_trading_days_ago(days: int) -> datetime:
    """Get datetime N trading days ago (excludes weekends)."""
    current = datetime.now()
    trading_days = 0
    
    while trading_days < days:
        current -= timedelta(days=1)
        if current.weekday() < 5:  # Monday = 0, Friday = 4
            trading_days += 1
    
    return current


def validate_symbol(symbol: str) -> bool:
    """Validate stock symbol format."""
    if not symbol:
        return False
    if not symbol.isalpha():
        return False
    if len(symbol) > 5:
        return False
    return True


def create_bar_data(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Create pandas DataFrame from bar data."""
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
    
    return df
