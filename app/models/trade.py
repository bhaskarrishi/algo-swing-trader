"""Trade model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum
from sqlalchemy.dialects.mysql import JSON
from app.database import Base
import enum


class TradeStatus(str, enum.Enum):
    """Trade status enum."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class TradeSide(str, enum.Enum):
    """Trade side enum."""
    BUY = "BUY"
    SELL = "SELL"


class Trade(Base):
    """Trade model."""
    
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(Enum(TradeSide), nullable=False)
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    entry_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    pnl = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)
    status = Column(Enum(TradeStatus), nullable=False, default=TradeStatus.OPEN)
    strategy_name = Column(String(100), nullable=False)
    entry_signals = Column(JSON, nullable=True)
    exit_reason = Column(String(200), nullable=True)
    
    def __repr__(self):
        """String representation."""
        return f"<Trade {self.id} {self.symbol} {self.side} {self.status}>"
