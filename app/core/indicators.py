"""Technical indicators calculations.

This module provides comprehensive technical indicator calculations
for the swing trading strategy using pandas-ta and custom implementations.
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional
from app.config import settings


class TechnicalIndicators:
    """Technical indicators calculator."""
    
    def __init__(self):
        """Initialize indicators calculator."""
        self.rsi_period = settings.RSI_PERIOD
        self.macd_fast = settings.MACD_FAST
        self.macd_slow = settings.MACD_SLOW
        self.macd_signal = settings.MACD_SIGNAL
        self.bb_period = settings.BOLLINGER_PERIOD
        self.bb_std = settings.BOLLINGER_STD
        self.atr_period = settings.ATR_PERIOD
        self.adx_period = settings.ADX_PERIOD
    
    def calculate_sma(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return data.rolling(window=period).mean()
    
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return data.ewm(span=period, adjust=False).mean()
    
    def calculate_rsi(self, data: pd.Series, period: int = None) -> pd.Series:
        """Calculate Relative Strength Index."""
        if period is None:
            period = self.rsi_period
        
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, data: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        ema_fast = self.calculate_ema(data, self.macd_fast)
        ema_slow = self.calculate_ema(data, self.macd_slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema(macd_line, self.macd_signal)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def calculate_bollinger_bands(self, data: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands."""
        sma = self.calculate_sma(data, self.bb_period)
        std = data.rolling(window=self.bb_period).std()
        
        upper_band = sma + (std * self.bb_std)
        lower_band = sma - (std * self.bb_std)
        
        return upper_band, sma, lower_band
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """Calculate Average True Range."""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        atr = true_range.rolling(window=self.atr_period).mean()
        return atr
    
    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """Calculate Average Directional Index."""
        # Calculate +DM and -DM
        up_move = high.diff()
        down_move = -low.diff()
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Calculate ATR
        atr = self.calculate_atr(high, low, close)
        
        # Calculate +DI and -DI
        plus_di = 100 * pd.Series(plus_dm).rolling(window=self.adx_period).mean() / atr
        minus_di = 100 * pd.Series(minus_dm).rolling(window=self.adx_period).mean() / atr
        
        # Calculate DX and ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=self.adx_period).mean()
        
        return adx
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                           k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Calculate Stochastic Oscillator."""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return k_percent, d_percent
    
    def calculate_cci(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                     period: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index."""
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.abs(x - x.mean()).mean()
        )
        
        cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
        return cci
    
    def calculate_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate On-Balance Volume."""
        obv = pd.Series(0, index=close.index, dtype=np.float64)
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    def calculate_vwap(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                      volume: pd.Series) -> pd.Series:
        """Calculate Volume Weighted Average Price."""
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap
    
    def calculate_parabolic_sar(self, high: pd.Series, low: pd.Series, 
                               acceleration: float = 0.02, maximum: float = 0.2) -> pd.Series:
        """Calculate Parabolic SAR."""
        sar = pd.Series(index=high.index, dtype=np.float64)
        ep = pd.Series(index=high.index, dtype=np.float64)
        af = pd.Series(index=high.index, dtype=np.float64)
        trend = pd.Series(1, index=high.index, dtype=np.int32)  # 1 for uptrend, -1 for downtrend
        
        # Initialize
        sar.iloc[0] = low.iloc[0]
        ep.iloc[0] = high.iloc[0]
        af.iloc[0] = acceleration
        
        for i in range(1, len(high)):
            # Calculate SAR
            sar.iloc[i] = sar.iloc[i-1] + af.iloc[i-1] * (ep.iloc[i-1] - sar.iloc[i-1])
            
            # Check for trend reversal
            if trend.iloc[i-1] == 1:  # Uptrend
                if low.iloc[i] < sar.iloc[i]:
                    trend.iloc[i] = -1
                    sar.iloc[i] = ep.iloc[i-1]
                    ep.iloc[i] = low.iloc[i]
                    af.iloc[i] = acceleration
                else:
                    trend.iloc[i] = 1
                    ep.iloc[i] = max(ep.iloc[i-1], high.iloc[i])
                    if ep.iloc[i] > ep.iloc[i-1]:
                        af.iloc[i] = min(af.iloc[i-1] + acceleration, maximum)
                    else:
                        af.iloc[i] = af.iloc[i-1]
            else:  # Downtrend
                if high.iloc[i] > sar.iloc[i]:
                    trend.iloc[i] = 1
                    sar.iloc[i] = ep.iloc[i-1]
                    ep.iloc[i] = high.iloc[i]
                    af.iloc[i] = acceleration
                else:
                    trend.iloc[i] = -1
                    ep.iloc[i] = min(ep.iloc[i-1], low.iloc[i])
                    if ep.iloc[i] < ep.iloc[i-1]:
                        af.iloc[i] = min(af.iloc[i-1] + acceleration, maximum)
                    else:
                        af.iloc[i] = af.iloc[i-1]
        
        return sar
    
    def find_support_resistance(self, high: pd.Series, low: pd.Series, close: pd.Series,
                               window: int = 20) -> Tuple[Optional[float], Optional[float]]:
        """Find recent support and resistance levels."""
        if len(close) < window:
            return None, None
        
        recent_high = high.rolling(window=window).max().iloc[-1]
        recent_low = low.rolling(window=window).min().iloc[-1]
        
        return recent_low, recent_high
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all indicators for a given DataFrame.
        
        Args:
            df: DataFrame with columns: open, high, low, close, volume
            
        Returns:
            DataFrame with all calculated indicators
        """
        result = df.copy()
        
        # Moving averages
        result['sma_20'] = self.calculate_sma(result['close'], 20)
        result['sma_50'] = self.calculate_sma(result['close'], 50)
        result['sma_200'] = self.calculate_sma(result['close'], 200)
        result['ema_20'] = self.calculate_ema(result['close'], 20)
        result['ema_50'] = self.calculate_ema(result['close'], 50)
        result['ema_200'] = self.calculate_ema(result['close'], 200)
        
        # RSI
        result['rsi'] = self.calculate_rsi(result['close'])
        
        # MACD
        macd_line, signal_line, histogram = self.calculate_macd(result['close'])
        result['macd'] = macd_line
        result['macd_signal'] = signal_line
        result['macd_histogram'] = histogram
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(result['close'])
        result['bb_upper'] = bb_upper
        result['bb_middle'] = bb_middle
        result['bb_lower'] = bb_lower
        
        # ATR
        result['atr'] = self.calculate_atr(result['high'], result['low'], result['close'])
        
        # ADX
        result['adx'] = self.calculate_adx(result['high'], result['low'], result['close'])
        
        # Stochastic
        k, d = self.calculate_stochastic(result['high'], result['low'], result['close'])
        result['stoch_k'] = k
        result['stoch_d'] = d
        
        # CCI
        result['cci'] = self.calculate_cci(result['high'], result['low'], result['close'])
        
        # Volume indicators
        result['volume_sma'] = self.calculate_sma(result['volume'], 20)
        result['obv'] = self.calculate_obv(result['close'], result['volume'])
        result['vwap'] = self.calculate_vwap(result['high'], result['low'], 
                                             result['close'], result['volume'])
        
        # Parabolic SAR
        result['psar'] = self.calculate_parabolic_sar(result['high'], result['low'])
        
        return result


# Create singleton instance
indicators = TechnicalIndicators()
