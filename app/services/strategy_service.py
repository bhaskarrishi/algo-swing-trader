"""Strategy service for trading logic coordination."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.trade import Trade, TradeStatus, TradeSide
from app.models.alert import Alert, AlertType, AlertSeverity
from app.services.questrade_service import questrade_service
from app.services.ibkr_service import ibkr_service
from app.services.indicator_service import indicator_service
from app.core.signals import signal_generator
from app.core.risk_manager import risk_manager
from app.core.order_manager import order_manager
from app.utils.logger import logger


class StrategyService:
    """Trading strategy orchestration service."""
    
    def __init__(self):
        """Initialize strategy service."""
        self.running = False
        self.watchlist = []
    
    def set_watchlist(self, symbols: List[str]):
        """Set watchlist of symbols to monitor.
        
        Args:
            symbols: List of stock symbols
        """
        self.watchlist = symbols
        logger.info(f"Watchlist updated: {', '.join(symbols)}")
    
    def start(self):
        """Start the trading strategy."""
        self.running = True
        logger.info("Trading strategy started")
    
    def stop(self):
        """Stop the trading strategy."""
        self.running = False
        logger.info("Trading strategy stopped")
    
    def is_running(self) -> bool:
        """Check if strategy is running."""
        return self.running
    
    def scan_for_signals(self, db: Session) -> List[Dict]:
        """Scan watchlist for trading signals.
        
        Args:
            db: Database session
            
        Returns:
            List of trading signals
        """
        if not self.running:
            return []
        
        signals = []
        
        for symbol in self.watchlist:
            try:
                # Calculate indicators
                df = indicator_service.calculate_indicators_for_symbol(db, symbol)
                
                if df.empty:
                    logger.warning(f"No data available for {symbol}")
                    continue
                
                # Generate signal
                signal = signal_generator.generate_signal(df, symbol)
                
                if signal:
                    signals.append(signal)
                    logger.info(f"Signal generated for {symbol}: {signal['side']} @ ${signal['price']:.2f}")
                    
                    # Create alert
                    alert = Alert(
                        alert_type=AlertType.TRADE_SIGNAL,
                        severity=AlertSeverity.INFO,
                        symbol=symbol,
                        message=f"{signal['side']} signal for {symbol} at ${signal['price']:.2f} "
                               f"(Confluence: {signal['confluence_score']})"
                    )
                    db.add(alert)
                
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {str(e)}")
        
        db.commit()
        return signals
    
    def execute_signal(self, db: Session, signal: Dict, account_equity: float) -> Optional[Trade]:
        """Execute a trading signal.
        
        Args:
            db: Database session
            signal: Trading signal
            account_equity: Current account equity
            
        Returns:
            Created Trade object or None
        """
        symbol = signal['symbol']
        
        # Check for duplicate orders
        if order_manager.check_duplicate_order(db, symbol, signal['side']):
            logger.warning(f"Duplicate order for {symbol} - skipping")
            return None
        
        # Validate trade with risk manager
        can_trade, reason, position_size = risk_manager.validate_trade(
            db, signal, account_equity
        )
        
        if not can_trade:
            logger.warning(f"Trade validation failed for {symbol}: {reason}")
            
            # Create alert for risk limit
            alert = Alert(
                alert_type=AlertType.RISK_LIMIT,
                severity=AlertSeverity.WARNING,
                symbol=symbol,
                message=f"Trade rejected for {symbol}: {reason}"
            )
            db.add(alert)
            db.commit()
            
            return None
        
        # Create trade
        trade = Trade(
            symbol=symbol,
            side=TradeSide(signal['side']),
            quantity=position_size,
            entry_price=signal['price'],
            stop_loss=signal['stop_loss'],
            take_profit=signal['take_profit'],
            strategy_name="Swing Trading Strategy",
            entry_signals=signal.get('indicators'),
            status=TradeStatus.OPEN
        )
        
        db.add(trade)
        db.commit()
        db.refresh(trade)
        
        # Create entry order
        entry_order = order_manager.create_entry_order(db, trade)
        
        # Submit order to IBKR (if connected)
        if ibkr_service.connected:
            action = "BUY" if signal['side'] == "BUY" else "SELL"
            ibkr_order_id = ibkr_service.place_market_order(symbol, position_size, action)
            
            if ibkr_order_id:
                order_manager.update_order_status(
                    db, entry_order.id, "SUBMITTED", ibkr_order_id=ibkr_order_id
                )
        
        logger.info(f"Executed trade {trade.id}: {signal['side']} {position_size} {symbol} @ ${signal['price']:.2f}")
        
        # Create alert
        alert = Alert(
            alert_type=AlertType.ORDER_EXECUTION,
            severity=AlertSeverity.INFO,
            symbol=symbol,
            message=f"Trade executed: {signal['side']} {position_size} {symbol} @ ${signal['price']:.2f}"
        )
        db.add(alert)
        db.commit()
        
        return trade
    
    def monitor_open_trades(self, db: Session):
        """Monitor open trades for exit conditions.
        
        Args:
            db: Database session
        """
        if not self.running:
            return
        
        open_trades = db.query(Trade).filter(
            Trade.status == TradeStatus.OPEN
        ).all()
        
        for trade in open_trades:
            try:
                # Get current indicators
                df = indicator_service.calculate_indicators_for_symbol(db, trade.symbol)
                
                if df.empty:
                    continue
                
                current_indicators = df.iloc[-1]
                
                # Check exit conditions
                trade_data = {
                    'side': trade.side.value,
                    'entry_price': trade.entry_price,
                    'entry_time': trade.entry_time,
                    'stop_loss': trade.stop_loss,
                    'take_profit': trade.take_profit
                }
                
                should_exit, exit_reason = signal_generator.check_exit_conditions(
                    trade_data, current_indicators
                )
                
                if should_exit:
                    self.close_trade(db, trade, current_indicators['close'], exit_reason)
                
            except Exception as e:
                logger.error(f"Error monitoring trade {trade.id}: {str(e)}")
    
    def close_trade(self, db: Session, trade: Trade, exit_price: float, exit_reason: str):
        """Close a trade.
        
        Args:
            db: Database session
            trade: Trade object
            exit_price: Exit price
            exit_reason: Reason for exit
        """
        # Create exit order
        exit_order = order_manager.create_exit_order(db, trade, exit_price)
        
        # Submit order to IBKR (if connected)
        if ibkr_service.connected:
            action = "SELL" if trade.side == TradeSide.BUY else "BUY"
            ibkr_order_id = ibkr_service.place_market_order(
                trade.symbol, trade.quantity, action
            )
            
            if ibkr_order_id:
                order_manager.update_order_status(
                    db, exit_order.id, "SUBMITTED", ibkr_order_id=ibkr_order_id
                )
        
        # Close the trade
        order_manager.close_trade(db, trade.id, exit_price, exit_reason)
        
        logger.info(f"Closed trade {trade.id}: {trade.symbol} @ ${exit_price:.2f} - {exit_reason}")
        
        # Create alert
        alert = Alert(
            alert_type=AlertType.ORDER_EXECUTION,
            severity=AlertSeverity.INFO,
            symbol=trade.symbol,
            message=f"Trade closed: {trade.symbol} @ ${exit_price:.2f} - {exit_reason}"
        )
        db.add(alert)
        db.commit()


# Create singleton instance
strategy_service = StrategyService()
