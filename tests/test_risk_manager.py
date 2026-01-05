"""Tests for risk manager."""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from app.core.risk_manager import RiskManager
from app.models.trade import Trade, TradeStatus, TradeSide


@pytest.fixture
def risk_manager():
    """Create risk manager instance."""
    return RiskManager()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return Mock()


def test_calculate_position_size(risk_manager):
    """Test position size calculation."""
    account_equity = 100000
    entry_price = 100
    stop_loss = 98
    
    position_size = risk_manager.calculate_position_size(
        account_equity, entry_price, stop_loss
    )
    
    # With 2% risk and $2 risk per share, should be 1000 shares
    assert position_size == 1000


def test_calculate_position_size_zero_risk(risk_manager):
    """Test position size with zero risk (invalid stop loss)."""
    account_equity = 100000
    entry_price = 100
    stop_loss = 100  # Same as entry
    
    position_size = risk_manager.calculate_position_size(
        account_equity, entry_price, stop_loss
    )
    
    assert position_size == 0


def test_check_position_limits_max_positions(risk_manager, mock_db):
    """Test max concurrent positions limit."""
    # Mock 5 open positions
    mock_db.query().filter().count.return_value = 5
    mock_db.query().filter().all.return_value = []
    
    can_trade, reason = risk_manager.check_position_limits(mock_db, 100000)
    
    assert not can_trade
    assert "Maximum concurrent positions" in reason


def test_circuit_breaker(risk_manager):
    """Test circuit breaker activation."""
    assert not risk_manager.is_circuit_breaker_active()
    
    risk_manager.activate_circuit_breaker("Test reason")
    
    assert risk_manager.is_circuit_breaker_active()
    
    risk_manager.deactivate_circuit_breaker()
    
    assert not risk_manager.is_circuit_breaker_active()


def test_validate_trade_success(risk_manager, mock_db):
    """Test successful trade validation."""
    # Mock no open positions
    mock_db.query().filter().count.return_value = 0
    mock_db.query().filter().all.return_value = []
    mock_db.query().filter().order_by().first.return_value = None
    
    signal = {
        'symbol': 'AAPL',
        'side': 'BUY',
        'price': 150,
        'stop_loss': 147,
        'take_profit': 159
    }
    
    can_trade, reason, position_size = risk_manager.validate_trade(
        mock_db, signal, 100000
    )
    
    assert can_trade
    assert position_size > 0


def test_reset_daily_tracking(risk_manager):
    """Test resetting daily tracking."""
    equity = 100000
    risk_manager.reset_daily_tracking(equity)
    
    assert risk_manager._daily_start_equity == equity
