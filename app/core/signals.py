"""Signal generation logic for trading strategy.

This module implements the battle-tested swing trading strategy
with multi-timeframe analysis and confluence-based entry signals.
"""
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.config import settings
from app.utils.logger import logger


class SignalGenerator:
    """Generate trading signals based on technical analysis."""
    
    def __init__(self):
        """Initialize signal generator."""
        self.min_confluence = settings.MIN_INDICATOR_CONFLUENCE
        self.adx_threshold = settings.ADX_THRESHOLD
    
    def check_long_entry_conditions(self, indicators: pd.Series) -> Tuple[bool, List[str], int]:
        """Check if long entry conditions are met.
        
        Args:
            indicators: Series containing all calculated indicators
            
        Returns:
            Tuple of (signal_valid, reasons, confluence_score)
        """
        reasons = []
        score = 0
        
        # 1. Price above 50 EMA and 200 EMA (uptrend confirmation)
        if indicators['close'] > indicators['ema_50'] and indicators['close'] > indicators['ema_200']:
            reasons.append("Price above 50 EMA and 200 EMA (uptrend)")
            score += 1
        
        # 2. RSI between 40-60 (not overbought/oversold)
        if 40 <= indicators['rsi'] <= 60:
            reasons.append(f"RSI in neutral zone ({indicators['rsi']:.1f})")
            score += 1
        
        # 3. MACD crossover (bullish) or histogram growing
        if indicators['macd'] > indicators['macd_signal']:
            reasons.append("MACD bullish crossover")
            score += 1
        elif indicators['macd_histogram'] > 0:
            reasons.append("MACD histogram positive")
            score += 0.5
        
        # 4. Price near support or bouncing off lower Bollinger Band
        bb_position = (indicators['close'] - indicators['bb_lower']) / (indicators['bb_upper'] - indicators['bb_lower'])
        if bb_position < 0.3:  # Near lower band
            reasons.append("Price near lower Bollinger Band (support)")
            score += 1
        
        # 5. Volume above average (confirmation)
        if indicators['volume'] > indicators['volume_sma']:
            reasons.append("Volume above average")
            score += 1
        
        # 6. ADX > 25 (strong trend)
        if indicators['adx'] > self.adx_threshold:
            reasons.append(f"Strong trend (ADX={indicators['adx']:.1f})")
            score += 1
        
        # Additional confluence checks
        # Stochastic oversold recovery
        if indicators['stoch_k'] > indicators['stoch_d'] and indicators['stoch_k'] < 50:
            reasons.append("Stochastic bullish cross in oversold zone")
            score += 0.5
        
        # CCI recovery from oversold
        if -100 < indicators['cci'] < 0:
            reasons.append("CCI recovering from oversold")
            score += 0.5
        
        signal_valid = score >= self.min_confluence
        
        return signal_valid, reasons, int(score)
    
    def check_short_entry_conditions(self, indicators: pd.Series) -> Tuple[bool, List[str], int]:
        """Check if short entry conditions are met.
        
        Args:
            indicators: Series containing all calculated indicators
            
        Returns:
            Tuple of (signal_valid, reasons, confluence_score)
        """
        reasons = []
        score = 0
        
        # 1. Price below 50 EMA and 200 EMA (downtrend confirmation)
        if indicators['close'] < indicators['ema_50'] and indicators['close'] < indicators['ema_200']:
            reasons.append("Price below 50 EMA and 200 EMA (downtrend)")
            score += 1
        
        # 2. RSI between 40-60
        if 40 <= indicators['rsi'] <= 60:
            reasons.append(f"RSI in neutral zone ({indicators['rsi']:.1f})")
            score += 1
        
        # 3. MACD crossover (bearish)
        if indicators['macd'] < indicators['macd_signal']:
            reasons.append("MACD bearish crossover")
            score += 1
        elif indicators['macd_histogram'] < 0:
            reasons.append("MACD histogram negative")
            score += 0.5
        
        # 4. Price near resistance or touching upper Bollinger Band
        bb_position = (indicators['close'] - indicators['bb_lower']) / (indicators['bb_upper'] - indicators['bb_lower'])
        if bb_position > 0.7:  # Near upper band
            reasons.append("Price near upper Bollinger Band (resistance)")
            score += 1
        
        # 5. Volume above average
        if indicators['volume'] > indicators['volume_sma']:
            reasons.append("Volume above average")
            score += 1
        
        # 6. ADX > 25 (strong trend)
        if indicators['adx'] > self.adx_threshold:
            reasons.append(f"Strong trend (ADX={indicators['adx']:.1f})")
            score += 1
        
        # Additional confluence checks
        # Stochastic overbought reversal
        if indicators['stoch_k'] < indicators['stoch_d'] and indicators['stoch_k'] > 50:
            reasons.append("Stochastic bearish cross in overbought zone")
            score += 0.5
        
        # CCI reversal from overbought
        if 0 < indicators['cci'] < 100:
            reasons.append("CCI reversing from overbought")
            score += 0.5
        
        signal_valid = score >= self.min_confluence
        
        return signal_valid, reasons, int(score)
    
    def check_exit_conditions(self, trade_data: Dict, current_indicators: pd.Series) -> Tuple[bool, Optional[str]]:
        """Check if exit conditions are met for an open trade.
        
        Args:
            trade_data: Dictionary containing trade information
            current_indicators: Current market indicators
            
        Returns:
            Tuple of (should_exit, exit_reason)
        """
        side = trade_data['side']
        entry_price = trade_data['entry_price']
        entry_time = trade_data['entry_time']
        stop_loss = trade_data['stop_loss']
        take_profit = trade_data['take_profit']
        current_price = current_indicators['close']
        
        # Stop loss hit
        if side == 'BUY' and current_price <= stop_loss:
            return True, "Stop loss triggered"
        elif side == 'SELL' and current_price >= stop_loss:
            return True, "Stop loss triggered"
        
        # Take profit hit
        if side == 'BUY' and current_price >= take_profit:
            return True, "Take profit target reached"
        elif side == 'SELL' and current_price <= take_profit:
            return True, "Take profit target reached"
        
        # Time-based exit (position held too long)
        days_held = (datetime.now() - entry_time).days
        if days_held >= settings.TIME_BASED_EXIT_DAYS:
            return True, f"Time-based exit (held for {days_held} days)"
        
        # Technical exit - opposite signal
        if side == 'BUY':
            # Check for short signal
            short_signal, reasons, score = self.check_short_entry_conditions(current_indicators)
            if short_signal and score >= self.min_confluence:
                return True, "Opposite signal generated (SHORT)"
        else:  # SELL
            # Check for long signal
            long_signal, reasons, score = self.check_long_entry_conditions(current_indicators)
            if long_signal and score >= self.min_confluence:
                return True, "Opposite signal generated (LONG)"
        
        return False, None
    
    def calculate_stop_loss_take_profit(self, entry_price: float, side: str, 
                                       atr: float) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels.
        
        Args:
            entry_price: Entry price of the trade
            side: Trade side (BUY/SELL)
            atr: Average True Range value
            
        Returns:
            Tuple of (stop_loss, take_profit)
        """
        stop_loss_pct = settings.STOP_LOSS_PCT / 100
        take_profit_mult = settings.TAKE_PROFIT_MULTIPLIER
        
        if side == 'BUY':
            stop_loss = entry_price * (1 - stop_loss_pct)
            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * take_profit_mult)
        else:  # SELL
            stop_loss = entry_price * (1 + stop_loss_pct)
            risk = stop_loss - entry_price
            take_profit = entry_price - (risk * take_profit_mult)
        
        return stop_loss, take_profit
    
    def calculate_trailing_stop(self, entry_price: float, current_price: float, 
                               side: str, atr: float) -> Optional[float]:
        """Calculate trailing stop based on ATR.
        
        Args:
            entry_price: Entry price of the trade
            current_price: Current market price
            side: Trade side (BUY/SELL)
            atr: Average True Range value
            
        Returns:
            Trailing stop price or None if not yet triggered
        """
        trailing_mult = settings.TRAILING_STOP_ATR_MULTIPLIER
        
        if side == 'BUY':
            # Only activate trailing stop after 1:1 profit
            if current_price >= entry_price * 1.02:  # At least 2% profit
                trailing_stop = current_price - (atr * trailing_mult)
                return trailing_stop
        else:  # SELL
            if current_price <= entry_price * 0.98:  # At least 2% profit
                trailing_stop = current_price + (atr * trailing_mult)
                return trailing_stop
        
        return None
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> Optional[Dict]:
        """Generate trading signal for a symbol.
        
        Args:
            df: DataFrame with OHLCV data and calculated indicators
            symbol: Stock symbol
            
        Returns:
            Signal dictionary or None
        """
        if len(df) < 200:  # Need enough data for indicators
            logger.warning(f"Insufficient data for {symbol}")
            return None
        
        latest = df.iloc[-1]
        
        # Check long entry
        long_signal, long_reasons, long_score = self.check_long_entry_conditions(latest)
        
        # Check short entry
        short_signal, short_reasons, short_score = self.check_short_entry_conditions(latest)
        
        # Prioritize stronger signal
        if long_signal and short_signal:
            if long_score > short_score:
                short_signal = False
            else:
                long_signal = False
        
        if long_signal:
            stop_loss, take_profit = self.calculate_stop_loss_take_profit(
                latest['close'], 'BUY', latest['atr']
            )
            
            return {
                'symbol': symbol,
                'side': 'BUY',
                'price': latest['close'],
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'reasons': long_reasons,
                'confluence_score': long_score,
                'timestamp': datetime.now(),
                'indicators': {
                    'rsi': latest['rsi'],
                    'macd': latest['macd'],
                    'adx': latest['adx'],
                    'atr': latest['atr']
                }
            }
        
        elif short_signal:
            stop_loss, take_profit = self.calculate_stop_loss_take_profit(
                latest['close'], 'SELL', latest['atr']
            )
            
            return {
                'symbol': symbol,
                'side': 'SELL',
                'price': latest['close'],
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'reasons': short_reasons,
                'confluence_score': short_score,
                'timestamp': datetime.now(),
                'indicators': {
                    'rsi': latest['rsi'],
                    'macd': latest['macd'],
                    'adx': latest['adx'],
                    'atr': latest['atr']
                }
            }
        
        return None


# Create singleton instance
signal_generator = SignalGenerator()
