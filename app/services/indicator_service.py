"""Indicator service for calculating and storing technical indicators."""
from typing import Dict, List
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from app.models.market_data import MarketData, Indicator, Timeframe
from app.core.indicators import indicators as tech_indicators
from app.utils.logger import logger


class IndicatorService:
    """Service for managing technical indicators."""
    
    def __init__(self):
        """Initialize indicator service."""
        self.calculator = tech_indicators
    
    def calculate_indicators_for_symbol(self, db: Session, symbol: str, 
                                       timeframe: Timeframe = Timeframe.DAILY,
                                       limit: int = 200) -> pd.DataFrame:
        """Calculate all indicators for a symbol.
        
        Args:
            db: Database session
            symbol: Stock symbol
            timeframe: Data timeframe
            limit: Number of bars to retrieve
            
        Returns:
            DataFrame with calculated indicators
        """
        # Get market data from database
        market_data = db.query(MarketData).filter(
            MarketData.symbol == symbol,
            MarketData.timeframe == timeframe
        ).order_by(MarketData.timestamp.desc()).limit(limit).all()
        
        if not market_data:
            logger.warning(f"No market data found for {symbol}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = []
        for bar in reversed(market_data):
            data.append({
                'timestamp': bar.timestamp,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        # Calculate all indicators
        df_with_indicators = self.calculator.calculate_all_indicators(df)
        
        return df_with_indicators
    
    def store_indicators(self, db: Session, symbol: str, df: pd.DataFrame, 
                        timeframe: Timeframe = Timeframe.DAILY):
        """Store calculated indicators to database.
        
        Args:
            db: Database session
            symbol: Stock symbol
            df: DataFrame with calculated indicators
            timeframe: Data timeframe
        """
        indicator_cols = [col for col in df.columns if col not in 
                         ['open', 'high', 'low', 'close', 'volume']]
        
        for timestamp, row in df.iterrows():
            for col in indicator_cols:
                if pd.notna(row[col]):
                    # Check if indicator already exists
                    existing = db.query(Indicator).filter(
                        Indicator.symbol == symbol,
                        Indicator.timestamp == timestamp,
                        Indicator.indicator_name == col,
                        Indicator.timeframe == timeframe
                    ).first()
                    
                    if not existing:
                        indicator = Indicator(
                            symbol=symbol,
                            timestamp=timestamp,
                            indicator_name=col,
                            value=float(row[col]),
                            timeframe=timeframe
                        )
                        db.add(indicator)
        
        db.commit()
        logger.info(f"Stored indicators for {symbol}")


# Create singleton instance
indicator_service = IndicatorService()
