"""Alert schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AlertResponse(BaseModel):
    """Alert response schema."""
    id: int
    timestamp: datetime
    alert_type: str
    severity: str
    symbol: Optional[str] = None
    message: str
    acknowledged: bool
    
    class Config:
        """Pydantic config."""
        from_attributes = True
