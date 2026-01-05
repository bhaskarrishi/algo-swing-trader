"""Script to populate initial watchlist."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.strategy_service import strategy_service
from app.utils.logger import logger


def populate_watchlist():
    """Populate watchlist with popular US stocks."""
    # Popular US stocks for swing trading
    default_watchlist = [
        "AAPL",  # Apple
        "MSFT",  # Microsoft
        "GOOGL", # Alphabet
        "AMZN",  # Amazon
        "TSLA",  # Tesla
        "NVDA",  # NVIDIA
        "META",  # Meta
        "JPM",   # JPMorgan
        "V",     # Visa
        "WMT",   # Walmart
    ]
    
    strategy_service.set_watchlist(default_watchlist)
    
    logger.info(f"Watchlist populated with {len(default_watchlist)} symbols")
    logger.info(f"Symbols: {', '.join(default_watchlist)}")
    
    return default_watchlist


if __name__ == "__main__":
    populate_watchlist()
    logger.info("\n✅ Watchlist populated successfully!")
