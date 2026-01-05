"""Position schemas."""
from datetime import datetime
from pydantic import BaseModel


class PositionResponse(BaseModel):
    """Position response schema."""
    id: int
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float
    market_value: float
    last_updated: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True
