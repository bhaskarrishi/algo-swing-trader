"""Analytics service for performance tracking and reporting."""
from typing import Dict, List
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.trade import Trade, TradeStatus
from app.models.account import AccountState
from app.utils.logger import logger


class AnalyticsService:
    """Analytics and performance tracking service."""
    
    def __init__(self):
        """Initialize analytics service."""
        pass
    
    def get_performance_summary(self, db: Session) -> Dict:
        """Get overall performance summary.
        
        Args:
            db: Database session
            
        Returns:
            Performance summary dictionary
        """
        # Get all closed trades
        closed_trades = db.query(Trade).filter(
            Trade.status == TradeStatus.CLOSED
        ).all()
        
        if not closed_trades:
            return self._empty_summary()
        
        total_trades = len(closed_trades)
        winning_trades = [t for t in closed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl and t.pnl < 0]
        
        total_pnl = sum(t.pnl for t in closed_trades if t.pnl)
        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = abs(sum(t.pnl for t in losing_trades))
        
        win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
        avg_win = total_wins / len(winning_trades) if winning_trades else 0
        avg_loss = total_losses / len(losing_trades) if losing_trades else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Get account info
        latest_account = db.query(AccountState).order_by(
            AccountState.timestamp.desc()
        ).first()
        
        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_wins': total_wins,
            'total_losses': total_losses,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'largest_win': max((t.pnl for t in winning_trades), default=0),
            'largest_loss': min((t.pnl for t in losing_trades), default=0),
            'current_equity': latest_account.total_equity if latest_account else 0,
            'max_drawdown': latest_account.max_drawdown_pct if latest_account else 0
        }
    
    def get_daily_pnl(self, db: Session, days: int = 30) -> List[Dict]:
        """Get daily P&L for the last N days.
        
        Args:
            db: Database session
            days: Number of days to retrieve
            
        Returns:
            List of daily P&L data
        """
        start_date = datetime.now() - timedelta(days=days)
        
        trades = db.query(Trade).filter(
            Trade.exit_time >= start_date,
            Trade.status == TradeStatus.CLOSED
        ).all()
        
        # Group by date
        daily_pnl = {}
        for trade in trades:
            if trade.exit_time and trade.pnl:
                date_key = trade.exit_time.date()
                if date_key not in daily_pnl:
                    daily_pnl[date_key] = 0
                daily_pnl[date_key] += trade.pnl
        
        # Convert to list
        result = []
        for date, pnl in sorted(daily_pnl.items()):
            result.append({
                'date': date.isoformat(),
                'pnl': pnl
            })
        
        return result
    
    def get_equity_curve(self, db: Session) -> List[Dict]:
        """Get equity curve data.
        
        Args:
            db: Database session
            
        Returns:
            List of equity curve points
        """
        account_states = db.query(AccountState).order_by(
            AccountState.timestamp
        ).all()
        
        result = []
        for state in account_states:
            result.append({
                'timestamp': state.timestamp.isoformat(),
                'equity': state.total_equity,
                'pnl': state.total_pnl
            })
        
        return result
    
    def get_trade_distribution(self, db: Session) -> Dict:
        """Get trade distribution by symbol and strategy.
        
        Args:
            db: Database session
            
        Returns:
            Trade distribution data
        """
        # By symbol
        symbol_dist = db.query(
            Trade.symbol,
            func.count(Trade.id).label('count'),
            func.sum(Trade.pnl).label('total_pnl')
        ).filter(
            Trade.status == TradeStatus.CLOSED
        ).group_by(Trade.symbol).all()
        
        by_symbol = []
        for symbol, count, pnl in symbol_dist:
            by_symbol.append({
                'symbol': symbol,
                'count': count,
                'total_pnl': float(pnl) if pnl else 0
            })
        
        # By side
        side_dist = db.query(
            Trade.side,
            func.count(Trade.id).label('count'),
            func.sum(Trade.pnl).label('total_pnl')
        ).filter(
            Trade.status == TradeStatus.CLOSED
        ).group_by(Trade.side).all()
        
        by_side = []
        for side, count, pnl in side_dist:
            by_side.append({
                'side': side.value,
                'count': count,
                'total_pnl': float(pnl) if pnl else 0
            })
        
        return {
            'by_symbol': by_symbol,
            'by_side': by_side
        }
    
    def get_recent_trades(self, db: Session, limit: int = 10) -> List[Dict]:
        """Get recent closed trades.
        
        Args:
            db: Database session
            limit: Number of trades to return
            
        Returns:
            List of recent trades
        """
        trades = db.query(Trade).filter(
            Trade.status == TradeStatus.CLOSED
        ).order_by(Trade.exit_time.desc()).limit(limit).all()
        
        result = []
        for trade in trades:
            result.append({
                'id': trade.id,
                'symbol': trade.symbol,
                'side': trade.side.value,
                'quantity': trade.quantity,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'pnl': trade.pnl,
                'pnl_percent': trade.pnl_percent,
                'entry_time': trade.entry_time.isoformat() if trade.entry_time else None,
                'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                'exit_reason': trade.exit_reason
            })
        
        return result
    
    def _empty_summary(self) -> Dict:
        """Return empty performance summary."""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'total_wins': 0,
            'total_losses': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'profit_factor': 0,
            'largest_win': 0,
            'largest_loss': 0,
            'current_equity': 0,
            'max_drawdown': 0
        }


# Create singleton instance
analytics_service = AnalyticsService()
