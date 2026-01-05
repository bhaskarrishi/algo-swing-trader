"""Interactive Brokers API service for order execution.

This service handles order submission and position tracking via IBKR API.
Requires IBKR TWS or IB Gateway running.
"""
from typing import Optional, Dict, List
from datetime import datetime
from ib_insync import IB, Stock, MarketOrder, LimitOrder, StopOrder, Trade as IBTrade
from app.config import settings
from app.utils.logger import logger


class IBKRService:
    """Interactive Brokers API service."""
    
    def __init__(self):
        """Initialize IBKR service."""
        self.ib = IB()
        self.host = settings.IBKR_HOST
        self.port = settings.IBKR_PORT
        self.client_id = settings.IBKR_CLIENT_ID
        self.account = settings.IBKR_ACCOUNT
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to IBKR TWS/Gateway.
        
        Returns:
            True if connection successful
        """
        try:
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.connected = True
            logger.info(f"Connected to IBKR at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {str(e)}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from IBKR."""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")
    
    def get_account_summary(self) -> Dict:
        """Get account summary.
        
        Returns:
            Account summary data
        """
        if not self.connected:
            logger.error("Not connected to IBKR")
            return {}
        
        try:
            account_values = self.ib.accountSummary(self.account)
            
            summary = {}
            for item in account_values:
                summary[item.tag] = {
                    'value': item.value,
                    'currency': item.currency
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting account summary: {str(e)}")
            return {}
    
    def get_positions(self) -> List[Dict]:
        """Get current positions.
        
        Returns:
            List of positions
        """
        if not self.connected:
            logger.error("Not connected to IBKR")
            return []
        
        try:
            positions = self.ib.positions(self.account)
            
            result = []
            for pos in positions:
                result.append({
                    'symbol': pos.contract.symbol,
                    'position': pos.position,
                    'avg_cost': pos.avgCost,
                    'market_value': pos.position * pos.avgCost
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []
    
    def create_stock_contract(self, symbol: str, exchange: str = "SMART", 
                            currency: str = "USD") -> Stock:
        """Create stock contract.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange (default: SMART)
            currency: Currency (default: USD)
            
        Returns:
            Stock contract
        """
        return Stock(symbol, exchange, currency)
    
    def place_market_order(self, symbol: str, quantity: int, action: str) -> Optional[str]:
        """Place market order.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            action: BUY or SELL
            
        Returns:
            Order ID or None
        """
        if not self.connected:
            logger.error("Not connected to IBKR")
            return None
        
        try:
            contract = self.create_stock_contract(symbol)
            order = MarketOrder(action, quantity)
            
            trade = self.ib.placeOrder(contract, order)
            
            logger.info(f"Placed market order: {action} {quantity} {symbol}")
            return str(trade.order.orderId)
            
        except Exception as e:
            logger.error(f"Error placing market order: {str(e)}")
            return None
    
    def place_limit_order(self, symbol: str, quantity: int, action: str, 
                         limit_price: float) -> Optional[str]:
        """Place limit order.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            action: BUY or SELL
            limit_price: Limit price
            
        Returns:
            Order ID or None
        """
        if not self.connected:
            logger.error("Not connected to IBKR")
            return None
        
        try:
            contract = self.create_stock_contract(symbol)
            order = LimitOrder(action, quantity, limit_price)
            
            trade = self.ib.placeOrder(contract, order)
            
            logger.info(f"Placed limit order: {action} {quantity} {symbol} @ ${limit_price}")
            return str(trade.order.orderId)
            
        except Exception as e:
            logger.error(f"Error placing limit order: {str(e)}")
            return None
    
    def place_stop_order(self, symbol: str, quantity: int, action: str, 
                        stop_price: float) -> Optional[str]:
        """Place stop order.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            action: BUY or SELL
            stop_price: Stop price
            
        Returns:
            Order ID or None
        """
        if not self.connected:
            logger.error("Not connected to IBKR")
            return None
        
        try:
            contract = self.create_stock_contract(symbol)
            order = StopOrder(action, quantity, stop_price)
            
            trade = self.ib.placeOrder(contract, order)
            
            logger.info(f"Placed stop order: {action} {quantity} {symbol} @ ${stop_price}")
            return str(trade.order.orderId)
            
        except Exception as e:
            logger.error(f"Error placing stop order: {str(e)}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            True if successful
        """
        if not self.connected:
            logger.error("Not connected to IBKR")
            return False
        
        try:
            # Find the trade
            trades = self.ib.trades()
            for trade in trades:
                if str(trade.order.orderId) == order_id:
                    self.ib.cancelOrder(trade.order)
                    logger.info(f"Cancelled order {order_id}")
                    return True
            
            logger.warning(f"Order {order_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return False
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get order status.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order status data or None
        """
        if not self.connected:
            logger.error("Not connected to IBKR")
            return None
        
        try:
            trades = self.ib.trades()
            for trade in trades:
                if str(trade.order.orderId) == order_id:
                    return {
                        'order_id': order_id,
                        'status': trade.orderStatus.status,
                        'filled': trade.orderStatus.filled,
                        'remaining': trade.orderStatus.remaining,
                        'avg_fill_price': trade.orderStatus.avgFillPrice
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting order status: {str(e)}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current price or None
        """
        if not self.connected:
            logger.error("Not connected to IBKR")
            return None
        
        try:
            contract = self.create_stock_contract(symbol)
            ticker = self.ib.reqMktData(contract)
            self.ib.sleep(1)  # Wait for data
            
            if ticker.last and ticker.last > 0:
                return ticker.last
            elif ticker.close and ticker.close > 0:
                return ticker.close
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {str(e)}")
            return None


# Create singleton instance
ibkr_service = IBKRService()
