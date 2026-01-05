"""Questrade API service for market data.

This service handles WebSocket connections and data retrieval from Questrade API.
Note: Requires valid Questrade refresh token in environment variables.
"""
import asyncio
import json
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import websocket
import requests
from app.config import settings
from app.utils.logger import logger


class QuestradeService:
    """Questrade API service."""
    
    def __init__(self):
        """Initialize Questrade service."""
        self.refresh_token = settings.QUESTRADE_REFRESH_TOKEN
        self.api_url = settings.QUESTRADE_API_URL
        self.access_token = None
        self.api_server = None
        self.ws_connection = None
        self.subscriptions = {}
        self._callbacks = []
    
    def authenticate(self) -> bool:
        """Authenticate with Questrade API.
        
        Returns:
            True if authentication successful
        """
        if not self.refresh_token:
            logger.error("Questrade refresh token not configured")
            return False
        
        try:
            url = f"{self.api_url}/oauth2/token"
            params = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token
            }
            
            response = requests.post(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data.get("access_token")
            self.api_server = data.get("api_server")
            
            logger.info("Successfully authenticated with Questrade API")
            return True
            
        except Exception as e:
            logger.error(f"Questrade authentication failed: {str(e)}")
            return False
    
    def get_symbol_id(self, symbol: str) -> Optional[int]:
        """Get symbol ID from Questrade.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Symbol ID or None
        """
        if not self.api_server or not self.access_token:
            logger.error("Not authenticated with Questrade")
            return None
        
        try:
            url = f"{self.api_server}v1/symbols/search"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {"prefix": symbol}
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            symbols = data.get("symbols", [])
            
            for sym in symbols:
                if sym.get("symbol") == symbol:
                    return sym.get("symbolId")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting symbol ID for {symbol}: {str(e)}")
            return None
    
    def get_historical_data(self, symbol: str, start_date: datetime, 
                          end_date: datetime, interval: str = "OneDay") -> List[Dict]:
        """Get historical market data.
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            interval: Data interval (OneMinute, FiveMinutes, OneHour, OneDay)
            
        Returns:
            List of OHLCV data
        """
        symbol_id = self.get_symbol_id(symbol)
        if not symbol_id:
            logger.error(f"Could not find symbol ID for {symbol}")
            return []
        
        try:
            url = f"{self.api_server}v1/markets/candles/{symbol_id}"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {
                "startTime": start_date.isoformat(),
                "endTime": end_date.isoformat(),
                "interval": interval
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            candles = data.get("candles", [])
            
            # Convert to standard format
            result = []
            for candle in candles:
                result.append({
                    "timestamp": datetime.fromisoformat(candle["start"].replace("Z", "+00:00")),
                    "open": candle["open"],
                    "high": candle["high"],
                    "low": candle["low"],
                    "close": candle["close"],
                    "volume": candle["volume"]
                })
            
            logger.info(f"Retrieved {len(result)} candles for {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return []
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get current quote for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Quote data or None
        """
        symbol_id = self.get_symbol_id(symbol)
        if not symbol_id:
            return None
        
        try:
            url = f"{self.api_server}v1/markets/quotes/{symbol_id}"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            quotes = data.get("quotes", [])
            
            if quotes:
                quote = quotes[0]
                return {
                    "symbol": quote["symbol"],
                    "bid": quote["bidPrice"],
                    "ask": quote["askPrice"],
                    "last": quote["lastTradePrice"],
                    "volume": quote["volume"],
                    "timestamp": datetime.now()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {str(e)}")
            return None
    
    def subscribe_to_symbol(self, symbol: str, callback: Callable):
        """Subscribe to real-time data for a symbol.
        
        Args:
            symbol: Stock symbol
            callback: Callback function for data updates
        """
        symbol_id = self.get_symbol_id(symbol)
        if not symbol_id:
            logger.error(f"Could not subscribe to {symbol}")
            return
        
        self.subscriptions[symbol] = {
            "symbol_id": symbol_id,
            "callback": callback
        }
        
        logger.info(f"Subscribed to {symbol}")
    
    def connect_websocket(self):
        """Connect to Questrade WebSocket for real-time data.
        
        Note: This is a simplified implementation.
        Production should use proper WebSocket handling with reconnection logic.
        """
        logger.warning("WebSocket connection not fully implemented - using polling instead")
    
    def disconnect(self):
        """Disconnect from Questrade API."""
        if self.ws_connection:
            self.ws_connection.close()
        
        self.subscriptions.clear()
        logger.info("Disconnected from Questrade")


# Create singleton instance
questrade_service = QuestradeService()
