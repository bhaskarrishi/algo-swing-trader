"""Order management system.

This module handles order creation, submission, and tracking.
"""
from typing import Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.order import Order, OrderType, OrderStatus
from app.models.trade import Trade, TradeStatus, TradeSide
from app.utils.logger import logger
from app.utils.helpers import calculate_pnl, calculate_pnl_percent


class OrderManager:
    """Order management system."""
    
    def __init__(self):
        """Initialize order manager."""
        pass
    
    def create_entry_order(self, db: Session, trade: Trade, order_type: str = "MARKET") -> Order:
        """Create entry order for a trade.
        
        Args:
            db: Database session
            trade: Trade object
            order_type: Order type (MARKET, LIMIT, etc.)
            
        Returns:
            Created Order object
        """
        order = Order(
            trade_id=trade.id,
            order_type=OrderType(order_type),
            status=OrderStatus.PENDING,
            symbol=trade.symbol,
            quantity=trade.quantity,
            price=trade.entry_price if order_type == "LIMIT" else None
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        logger.info(f"Created entry order {order.id} for trade {trade.id} ({trade.symbol})")
        
        return order
    
    def create_exit_order(self, db: Session, trade: Trade, exit_price: float, 
                         order_type: str = "MARKET") -> Order:
        """Create exit order for a trade.
        
        Args:
            db: Database session
            trade: Trade object
            exit_price: Exit price
            order_type: Order type
            
        Returns:
            Created Order object
        """
        # Determine side (opposite of entry)
        exit_side = "SELL" if trade.side == TradeSide.BUY else "BUY"
        
        order = Order(
            trade_id=trade.id,
            order_type=OrderType(order_type),
            status=OrderStatus.PENDING,
            symbol=trade.symbol,
            quantity=trade.quantity,
            price=exit_price if order_type == "LIMIT" else None
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        logger.info(f"Created exit order {order.id} for trade {trade.id} ({trade.symbol})")
        
        return order
    
    def create_stop_loss_order(self, db: Session, trade: Trade) -> Order:
        """Create stop loss order for a trade.
        
        Args:
            db: Database session
            trade: Trade object
            
        Returns:
            Created Order object
        """
        order = Order(
            trade_id=trade.id,
            order_type=OrderType.STOP,
            status=OrderStatus.PENDING,
            symbol=trade.symbol,
            quantity=trade.quantity,
            price=trade.stop_loss
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        logger.info(f"Created stop loss order {order.id} for trade {trade.id} at ${trade.stop_loss:.2f}")
        
        return order
    
    def create_take_profit_order(self, db: Session, trade: Trade) -> Order:
        """Create take profit order for a trade.
        
        Args:
            db: Database session
            trade: Trade object
            
        Returns:
            Created Order object
        """
        order = Order(
            trade_id=trade.id,
            order_type=OrderType.LIMIT,
            status=OrderStatus.PENDING,
            symbol=trade.symbol,
            quantity=trade.quantity,
            price=trade.take_profit
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        logger.info(f"Created take profit order {order.id} for trade {trade.id} at ${trade.take_profit:.2f}")
        
        return order
    
    def update_order_status(self, db: Session, order_id: int, status: str, 
                           filled_quantity: Optional[int] = None,
                           filled_price: Optional[float] = None,
                           ibkr_order_id: Optional[str] = None) -> Order:
        """Update order status.
        
        Args:
            db: Database session
            order_id: Order ID
            status: New status
            filled_quantity: Filled quantity (if applicable)
            filled_price: Filled price (if applicable)
            ibkr_order_id: IBKR order ID (if applicable)
            
        Returns:
            Updated Order object
        """
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            logger.error(f"Order {order_id} not found")
            return None
        
        order.status = OrderStatus(status)
        
        if status == "SUBMITTED":
            order.submitted_at = datetime.utcnow()
        
        if filled_quantity is not None:
            order.filled_quantity = filled_quantity
        
        if filled_price is not None:
            order.filled_price = filled_price
        
        if status == "FILLED":
            order.filled_at = datetime.utcnow()
            if order.filled_quantity == 0:
                order.filled_quantity = order.quantity
        
        if ibkr_order_id is not None:
            order.ibkr_order_id = ibkr_order_id
        
        db.commit()
        db.refresh(order)
        
        logger.info(f"Updated order {order_id} status to {status}")
        
        return order
    
    def close_trade(self, db: Session, trade_id: int, exit_price: float, 
                   exit_reason: str) -> Trade:
        """Close a trade.
        
        Args:
            db: Database session
            trade_id: Trade ID
            exit_price: Exit price
            exit_reason: Reason for exit
            
        Returns:
            Updated Trade object
        """
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        
        if not trade:
            logger.error(f"Trade {trade_id} not found")
            return None
        
        if trade.status == TradeStatus.CLOSED:
            logger.warning(f"Trade {trade_id} is already closed")
            return trade
        
        # Update trade
        trade.exit_price = exit_price
        trade.exit_time = datetime.utcnow()
        trade.status = TradeStatus.CLOSED
        trade.exit_reason = exit_reason
        
        # Calculate P&L
        trade.pnl = calculate_pnl(
            trade.entry_price, 
            exit_price, 
            trade.quantity, 
            trade.side.value
        )
        trade.pnl_percent = calculate_pnl_percent(
            trade.entry_price, 
            exit_price, 
            trade.side.value
        )
        
        db.commit()
        db.refresh(trade)
        
        logger.info(
            f"Closed trade {trade_id} ({trade.symbol}) - "
            f"P&L: ${trade.pnl:.2f} ({trade.pnl_percent:.2f}%) - "
            f"Reason: {exit_reason}"
        )
        
        return trade
    
    def cancel_order(self, db: Session, order_id: int) -> Order:
        """Cancel an order.
        
        Args:
            db: Database session
            order_id: Order ID
            
        Returns:
            Updated Order object
        """
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            logger.error(f"Order {order_id} not found")
            return None
        
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            logger.warning(f"Order {order_id} cannot be cancelled (status: {order.status})")
            return order
        
        order.status = OrderStatus.CANCELLED
        db.commit()
        db.refresh(order)
        
        logger.info(f"Cancelled order {order_id}")
        
        return order
    
    def get_open_orders(self, db: Session, symbol: Optional[str] = None) -> list:
        """Get open orders.
        
        Args:
            db: Database session
            symbol: Filter by symbol (optional)
            
        Returns:
            List of open orders
        """
        query = db.query(Order).filter(
            Order.status.in_([OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL])
        )
        
        if symbol:
            query = query.filter(Order.symbol == symbol)
        
        return query.all()
    
    def check_duplicate_order(self, db: Session, symbol: str, side: str) -> bool:
        """Check if there's already an open order for this symbol and side.
        
        Args:
            db: Database session
            symbol: Stock symbol
            side: Order side
            
        Returns:
            True if duplicate exists
        """
        # Check for open trades
        existing_trade = db.query(Trade).filter(
            Trade.symbol == symbol,
            Trade.status == TradeStatus.OPEN
        ).first()
        
        if existing_trade:
            return True
        
        # Check for pending entry orders
        existing_order = db.query(Order).filter(
            Order.symbol == symbol,
            Order.status.in_([OrderStatus.PENDING, OrderStatus.SUBMITTED])
        ).first()
        
        if existing_order:
            return True
        
        return False


# Create singleton instance
order_manager = OrderManager()
