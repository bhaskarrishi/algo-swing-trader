"""Strategy parameter model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base


class StrategyParameter(Base):
    """Strategy parameter model."""
    
    __tablename__ = "strategy_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    parameter_name = Column(String(100), nullable=False, unique=True, index=True)
    parameter_value = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        """String representation."""
        return f"<StrategyParameter {self.parameter_name}={self.parameter_value}>"
