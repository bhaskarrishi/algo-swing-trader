"""Tests for technical indicators."""
import pytest
import pandas as pd
import numpy as np
from app.core.indicators import TechnicalIndicators


@pytest.fixture
def sample_data():
    """Create sample market data for testing."""
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    data = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    # Ensure high is highest and low is lowest
    data['high'] = data[['open', 'high', 'close']].max(axis=1)
    data['low'] = data[['open', 'low', 'close']].min(axis=1)
    
    return data


def test_calculate_sma(sample_data):
    """Test SMA calculation."""
    indicators = TechnicalIndicators()
    sma = indicators.calculate_sma(sample_data['close'], 20)
    
    assert len(sma) == len(sample_data)
    assert not sma.iloc[-1] != sma.iloc[-1]  # Not NaN


def test_calculate_ema(sample_data):
    """Test EMA calculation."""
    indicators = TechnicalIndicators()
    ema = indicators.calculate_ema(sample_data['close'], 20)
    
    assert len(ema) == len(sample_data)
    assert not ema.iloc[-1] != ema.iloc[-1]  # Not NaN


def test_calculate_rsi(sample_data):
    """Test RSI calculation."""
    indicators = TechnicalIndicators()
    rsi = indicators.calculate_rsi(sample_data['close'], 14)
    
    assert len(rsi) == len(sample_data)
    # RSI should be between 0 and 100
    assert (rsi.dropna() >= 0).all()
    assert (rsi.dropna() <= 100).all()


def test_calculate_macd(sample_data):
    """Test MACD calculation."""
    indicators = TechnicalIndicators()
    macd, signal, histogram = indicators.calculate_macd(sample_data['close'])
    
    assert len(macd) == len(sample_data)
    assert len(signal) == len(sample_data)
    assert len(histogram) == len(sample_data)


def test_calculate_bollinger_bands(sample_data):
    """Test Bollinger Bands calculation."""
    indicators = TechnicalIndicators()
    upper, middle, lower = indicators.calculate_bollinger_bands(sample_data['close'])
    
    assert len(upper) == len(sample_data)
    assert len(middle) == len(sample_data)
    assert len(lower) == len(sample_data)
    
    # Upper should be greater than middle, middle greater than lower
    valid_data = ~(upper.isna() | middle.isna() | lower.isna())
    assert (upper[valid_data] >= middle[valid_data]).all()
    assert (middle[valid_data] >= lower[valid_data]).all()


def test_calculate_atr(sample_data):
    """Test ATR calculation."""
    indicators = TechnicalIndicators()
    atr = indicators.calculate_atr(
        sample_data['high'],
        sample_data['low'],
        sample_data['close']
    )
    
    assert len(atr) == len(sample_data)
    # ATR should be positive
    assert (atr.dropna() >= 0).all()


def test_calculate_all_indicators(sample_data):
    """Test calculating all indicators at once."""
    indicators = TechnicalIndicators()
    result = indicators.calculate_all_indicators(sample_data)
    
    # Check that all expected indicators are present
    expected_indicators = [
        'sma_20', 'sma_50', 'ema_20', 'ema_50',
        'rsi', 'macd', 'macd_signal', 'macd_histogram',
        'bb_upper', 'bb_middle', 'bb_lower',
        'atr', 'adx', 'obv', 'vwap'
    ]
    
    for indicator in expected_indicators:
        assert indicator in result.columns, f"{indicator} not found in result"
