"""Trade schemas."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class TradeBase(BaseModel):
    """Base trade schema."""
    symbol: str
    side: str
    quantity: int
    entry_price: float
    stop_loss: float
    take_profit: float
    strategy_name: str


class TradeCreate(TradeBase):
    """Trade creation schema."""
    entry_signals: Optional[Dict[str, Any]] = None


class TradeUpdate(BaseModel):
    """Trade update schema."""
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    status: Optional[str] = None
    exit_reason: Optional[str] = None


class TradeResponse(TradeBase):
    """Trade response schema."""
    id: int
    entry_time: datetime
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    status: str
    entry_signals: Optional[Dict[str, Any]] = None
    exit_reason: Optional[str] = None
    
    class Config:
        """Pydantic config."""
        from_attributes = True
