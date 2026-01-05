"""Risk service for managing risk-related operations."""
from typing import Dict
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.account import AccountState
from app.core.risk_manager import risk_manager
from app.utils.logger import logger


class RiskService:
    """Risk management service."""
    
    def __init__(self):
        """Initialize risk service."""
        self.risk_manager = risk_manager
    
    def update_account_state(self, db: Session, equity: float, cash: float, 
                           daily_pnl: float, total_pnl: float, 
                           open_positions: int) -> AccountState:
        """Update account state in database.
        
        Args:
            db: Database session
            equity: Total equity
            cash: Cash balance
            daily_pnl: Daily P&L
            total_pnl: Total P&L
            open_positions: Number of open positions
            
        Returns:
            Created AccountState object
        """
        # Calculate max drawdown
        peak_equity = db.query(AccountState).order_by(
            AccountState.total_equity.desc()
        ).first()
        
        if peak_equity:
            max_dd = ((peak_equity.total_equity - equity) / peak_equity.total_equity) * 100
        else:
            max_dd = 0.0
        
        account_state = AccountState(
            total_equity=equity,
            cash_balance=cash,
            total_pnl=total_pnl,
            daily_pnl=daily_pnl,
            open_positions_count=open_positions,
            max_drawdown_pct=max_dd
        )
        
        db.add(account_state)
        db.commit()
        db.refresh(account_state)
        
        return account_state
    
    def get_current_account_state(self, db: Session) -> Dict:
        """Get current account state.
        
        Args:
            db: Database session
            
        Returns:
            Account state dictionary
        """
        latest = db.query(AccountState).order_by(
            AccountState.timestamp.desc()
        ).first()
        
        if not latest:
            return {
                'total_equity': 0.0,
                'cash_balance': 0.0,
                'total_pnl': 0.0,
                'daily_pnl': 0.0,
                'open_positions_count': 0,
                'max_drawdown_pct': 0.0
            }
        
        return {
            'total_equity': latest.total_equity,
            'cash_balance': latest.cash_balance,
            'total_pnl': latest.total_pnl,
            'daily_pnl': latest.daily_pnl,
            'open_positions_count': latest.open_positions_count,
            'max_drawdown_pct': latest.max_drawdown_pct
        }
    
    def get_risk_metrics(self, db: Session) -> Dict:
        """Get risk metrics.
        
        Args:
            db: Database session
            
        Returns:
            Risk metrics dictionary
        """
        return self.risk_manager.calculate_risk_metrics(db)
    
    def check_risk_limits(self, db: Session, account_equity: float) -> Dict:
        """Check all risk limits.
        
        Args:
            db: Database session
            account_equity: Current account equity
            
        Returns:
            Dictionary with risk checks
        """
        results = {}
        
        # Position limits
        can_trade, reason = self.risk_manager.check_position_limits(db, account_equity)
        results['position_limits'] = {'ok': can_trade, 'message': reason}
        
        # Daily loss limit
        can_trade, reason = self.risk_manager.check_daily_loss_limit(db, account_equity)
        results['daily_loss'] = {'ok': can_trade, 'message': reason}
        
        # Drawdown limit
        can_trade, reason = self.risk_manager.check_drawdown_limit(db, account_equity)
        results['drawdown'] = {'ok': can_trade, 'message': reason}
        
        # Circuit breaker status
        results['circuit_breaker'] = {
            'active': self.risk_manager.is_circuit_breaker_active()
        }
        
        return results
    
    def reset_daily_limits(self, equity: float):
        """Reset daily tracking limits.
        
        Args:
            equity: Current equity
        """
        self.risk_manager.reset_daily_tracking(equity)
        logger.info("Daily risk limits reset")
    
    def activate_circuit_breaker(self, reason: str):
        """Activate circuit breaker.
        
        Args:
            reason: Reason for activation
        """
        self.risk_manager.activate_circuit_breaker(reason)
    
    def deactivate_circuit_breaker(self):
        """Deactivate circuit breaker."""
        self.risk_manager.deactivate_circuit_breaker()


# Create singleton instance
risk_service = RiskService()
