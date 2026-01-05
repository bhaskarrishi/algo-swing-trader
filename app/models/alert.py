"""Alert model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, Text
from app.database import Base
import enum


class AlertType(str, enum.Enum):
    """Alert type enum."""
    TRADE_SIGNAL = "TRADE_SIGNAL"
    RISK_LIMIT = "RISK_LIMIT"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    CONNECTION_ISSUE = "CONNECTION_ISSUE"
    ORDER_EXECUTION = "ORDER_EXECUTION"


class AlertSeverity(str, enum.Enum):
    """Alert severity enum."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class Alert(Base):
    """Alert model."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    alert_type = Column(Enum(AlertType), nullable=False, index=True)
    severity = Column(Enum(AlertSeverity), nullable=False, index=True)
    symbol = Column(String(20), nullable=True, index=True)
    message = Column(Text, nullable=False)
    acknowledged = Column(Boolean, nullable=False, default=False)
    
    def __repr__(self):
        """String representation."""
        return f"<Alert {self.alert_type} {self.severity} {self.timestamp}>"
