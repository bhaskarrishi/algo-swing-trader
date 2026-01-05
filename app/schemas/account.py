"""Account state schemas."""
from datetime import datetime
from pydantic import BaseModel


class AccountStateResponse(BaseModel):
    """Account state response schema."""
    id: int
    timestamp: datetime
    total_equity: float
    cash_balance: float
    total_pnl: float
    daily_pnl: float
    open_positions_count: int
    max_drawdown_pct: float
    
    class Config:
        """Pydantic config."""
        from_attributes = True
