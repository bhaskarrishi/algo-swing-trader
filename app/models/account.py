"""Account state model."""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime
from app.database import Base


class AccountState(Base):
    """Account state model."""
    
    __tablename__ = "account_state"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    total_equity = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    total_pnl = Column(Float, nullable=False)
    daily_pnl = Column(Float, nullable=False)
    open_positions_count = Column(Integer, nullable=False, default=0)
    max_drawdown_pct = Column(Float, nullable=False, default=0.0)
    
    def __repr__(self):
        """String representation."""
        return f"<AccountState equity={self.total_equity} pnl={self.total_pnl}>"
