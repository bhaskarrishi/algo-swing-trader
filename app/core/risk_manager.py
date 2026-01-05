"""Risk management system.

This module implements comprehensive risk management rules
to preserve capital and prevent excessive losses.
"""
from typing import Optional, Dict, List, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.config import settings
from app.models.trade import Trade, TradeStatus
from app.models.account import AccountState
from app.utils.logger import logger


class RiskManager:
    """Risk management system."""
    
    def __init__(self):
        """Initialize risk manager."""
        self.max_position_risk_pct = settings.MAX_POSITION_RISK_PCT
        self.max_portfolio_risk_pct = settings.MAX_PORTFOLIO_RISK_PCT
        self.max_daily_loss_pct = settings.MAX_DAILY_LOSS_PCT
        self.max_drawdown_pct = settings.MAX_DRAWDOWN_PCT
        self.max_concurrent_positions = settings.MAX_CONCURRENT_POSITIONS
        self.max_position_size_pct = settings.MAX_POSITION_SIZE_PCT
        self.max_total_deployed_pct = settings.MAX_TOTAL_DEPLOYED_PCT
        
        self._circuit_breaker_active = False
        self._daily_start_equity = None
    
    def calculate_position_size(self, account_equity: float, entry_price: float, 
                               stop_loss: float, risk_pct: Optional[float] = None) -> int:
        """Calculate position size based on risk parameters.
        
        Args:
            account_equity: Total account equity
            entry_price: Intended entry price
            stop_loss: Stop loss price
            risk_pct: Risk percentage (defaults to MAX_POSITION_RISK_PCT)
            
        Returns:
            Number of shares to trade
        """
        if risk_pct is None:
            risk_pct = self.max_position_risk_pct
        
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share == 0:
            logger.error("Risk per share is zero - invalid stop loss")
            return 0
        
        # Calculate position size based on risk
        risk_amount = account_equity * (risk_pct / 100)
        position_size = int(risk_amount / risk_per_share)
        
        # Apply maximum position size constraint
        max_position_value = account_equity * (self.max_position_size_pct / 100)
        max_shares = int(max_position_value / entry_price)
        
        position_size = min(position_size, max_shares)
        
        return max(position_size, 0)
    
    def check_position_limits(self, db: Session, account_equity: float) -> Tuple[bool, str]:
        """Check if we can open a new position.
        
        Args:
            db: Database session
            account_equity: Current account equity
            
        Returns:
            Tuple of (can_trade, reason)
        """
        # Check circuit breaker
        if self._circuit_breaker_active:
            return False, "Circuit breaker active - trading paused"
        
        # Check number of open positions
        open_positions = db.query(Trade).filter(
            Trade.status == TradeStatus.OPEN
        ).count()
        
        if open_positions >= self.max_concurrent_positions:
            return False, f"Maximum concurrent positions reached ({open_positions}/{self.max_concurrent_positions})"
        
        # Check total capital deployed
        open_trades = db.query(Trade).filter(
            Trade.status == TradeStatus.OPEN
        ).all()
        
        total_deployed = sum(t.quantity * t.entry_price for t in open_trades)
        deployed_pct = (total_deployed / account_equity) * 100 if account_equity > 0 else 0
        
        if deployed_pct >= self.max_total_deployed_pct:
            return False, f"Maximum capital deployment reached ({deployed_pct:.1f}%/{self.max_total_deployed_pct}%)"
        
        return True, "OK"
    
    def check_daily_loss_limit(self, db: Session, account_equity: float) -> Tuple[bool, str]:
        """Check if daily loss limit has been exceeded.
        
        Args:
            db: Database session
            account_equity: Current account equity
            
        Returns:
            Tuple of (can_trade, reason)
        """
        # Get today's start equity
        if self._daily_start_equity is None:
            # Try to get from database
            today = date.today()
            account_state = db.query(AccountState).filter(
                AccountState.timestamp >= datetime.combine(today, datetime.min.time())
            ).order_by(AccountState.timestamp).first()
            
            if account_state:
                self._daily_start_equity = account_state.total_equity
            else:
                self._daily_start_equity = account_equity
        
        # Calculate daily P&L
        daily_pnl = account_equity - self._daily_start_equity
        daily_pnl_pct = (daily_pnl / self._daily_start_equity) * 100 if self._daily_start_equity > 0 else 0
        
        if daily_pnl_pct <= -self.max_daily_loss_pct:
            self.activate_circuit_breaker("Daily loss limit exceeded")
            return False, f"Daily loss limit exceeded ({daily_pnl_pct:.2f}%)"
        
        return True, "OK"
    
    def check_drawdown_limit(self, db: Session, account_equity: float) -> Tuple[bool, str]:
        """Check if maximum drawdown has been exceeded.
        
        Args:
            db: Database session
            account_equity: Current account equity
            
        Returns:
            Tuple of (can_trade, reason)
        """
        # Get peak equity
        peak_equity_record = db.query(AccountState).order_by(
            AccountState.total_equity.desc()
        ).first()
        
        if not peak_equity_record:
            return True, "OK"
        
        peak_equity = peak_equity_record.total_equity
        
        # Calculate drawdown
        drawdown = ((peak_equity - account_equity) / peak_equity) * 100 if peak_equity > 0 else 0
        
        if drawdown >= self.max_drawdown_pct:
            self.activate_circuit_breaker(f"Maximum drawdown exceeded ({drawdown:.2f}%)")
            return False, f"Maximum drawdown exceeded ({drawdown:.2f}%/{self.max_drawdown_pct}%)"
        
        return True, "OK"
    
    def validate_trade(self, db: Session, signal: Dict, account_equity: float) -> Tuple[bool, str, int]:
        """Validate if a trade can be executed.
        
        Args:
            db: Database session
            signal: Trading signal dictionary
            account_equity: Current account equity
            
        Returns:
            Tuple of (can_trade, reason, position_size)
        """
        # Check position limits
        can_trade, reason = self.check_position_limits(db, account_equity)
        if not can_trade:
            return False, reason, 0
        
        # Check daily loss limit
        can_trade, reason = self.check_daily_loss_limit(db, account_equity)
        if not can_trade:
            return False, reason, 0
        
        # Check drawdown limit
        can_trade, reason = self.check_drawdown_limit(db, account_equity)
        if not can_trade:
            return False, reason, 0
        
        # Calculate position size
        position_size = self.calculate_position_size(
            account_equity,
            signal['price'],
            signal['stop_loss']
        )
        
        if position_size == 0:
            return False, "Position size is zero", 0
        
        # Validate position size doesn't exceed limits
        position_value = position_size * signal['price']
        position_pct = (position_value / account_equity) * 100 if account_equity > 0 else 0
        
        if position_pct > self.max_position_size_pct:
            return False, f"Position size exceeds limit ({position_pct:.1f}%)", 0
        
        return True, "OK", position_size
    
    def activate_circuit_breaker(self, reason: str):
        """Activate circuit breaker to stop trading.
        
        Args:
            reason: Reason for activation
        """
        self._circuit_breaker_active = True
        logger.critical(f"CIRCUIT BREAKER ACTIVATED: {reason}")
    
    def deactivate_circuit_breaker(self):
        """Deactivate circuit breaker."""
        self._circuit_breaker_active = False
        logger.info("Circuit breaker deactivated")
    
    def is_circuit_breaker_active(self) -> bool:
        """Check if circuit breaker is active."""
        return self._circuit_breaker_active
    
    def reset_daily_tracking(self, current_equity: float):
        """Reset daily tracking (call at start of trading day).
        
        Args:
            current_equity: Current account equity
        """
        self._daily_start_equity = current_equity
        logger.info(f"Daily tracking reset - Starting equity: ${current_equity:,.2f}")
    
    def calculate_risk_metrics(self, db: Session) -> Dict:
        """Calculate risk metrics for monitoring.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary of risk metrics
        """
        # Get all closed trades
        closed_trades = db.query(Trade).filter(
            Trade.status == TradeStatus.CLOSED
        ).all()
        
        if not closed_trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'average_win': 0.0,
                'average_loss': 0.0,
                'expectancy': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0
            }
        
        # Calculate metrics
        total_trades = len(closed_trades)
        winning_trades = [t for t in closed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl and t.pnl < 0]
        
        win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
        
        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = abs(sum(t.pnl for t in losing_trades))
        
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        average_win = total_wins / len(winning_trades) if winning_trades else 0
        average_loss = total_losses / len(losing_trades) if losing_trades else 0
        
        expectancy = (win_rate / 100 * average_win) - ((100 - win_rate) / 100 * average_loss)
        
        # Calculate max drawdown
        equity_curve = []
        running_equity = 0
        for trade in sorted(closed_trades, key=lambda t: t.exit_time or datetime.now()):
            running_equity += trade.pnl or 0
            equity_curve.append(running_equity)
        
        peak = equity_curve[0] if equity_curve else 0
        max_dd = 0
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = ((peak - value) / peak) * 100 if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        
        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'average_win': average_win,
            'average_loss': average_loss,
            'expectancy': expectancy,
            'max_drawdown': max_dd,
            'circuit_breaker_active': self._circuit_breaker_active
        }


# Create singleton instance
risk_manager = RiskManager()
