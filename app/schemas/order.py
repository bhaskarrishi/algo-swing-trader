"""Order schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class OrderBase(BaseModel):
    """Base order schema."""
    order_type: str
    symbol: str
    quantity: int
    price: Optional[float] = None


class OrderCreate(OrderBase):
    """Order creation schema."""
    trade_id: Optional[int] = None


class OrderResponse(OrderBase):
    """Order response schema."""
    id: int
    trade_id: Optional[int] = None
    status: str
    filled_quantity: int
    filled_price: Optional[float] = None
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    ibkr_order_id: Optional[str] = None
    
    class Config:
        """Pydantic config."""
        from_attributes = True
