"""Market data and indicator models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Index
from app.database import Base
import enum


class Timeframe(str, enum.Enum):
    """Timeframe enum."""
    ONE_MIN = "1min"
    FIVE_MIN = "5min"
    FIFTEEN_MIN = "15min"
    ONE_HOUR = "1hour"
    DAILY = "daily"


class MarketData(Base):
    """Market data model."""
    
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    timeframe = Column(Enum(Timeframe), nullable=False)
    
    __table_args__ = (
        Index('idx_symbol_timestamp_timeframe', 'symbol', 'timestamp', 'timeframe'),
    )
    
    def __repr__(self):
        """String representation."""
        return f"<MarketData {self.symbol} {self.timeframe} {self.timestamp}>"


class Indicator(Base):
    """Indicator model."""
    
    __tablename__ = "indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    indicator_name = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)
    timeframe = Column(Enum(Timeframe), nullable=False)
    
    __table_args__ = (
        Index('idx_indicator_lookup', 'symbol', 'indicator_name', 'timestamp', 'timeframe'),
    )
    
    def __repr__(self):
        """String representation."""
        return f"<Indicator {self.symbol} {self.indicator_name} {self.timestamp}>"
