"""Strategy router for strategy management endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.strategy_service import strategy_service
from app.services.risk_service import risk_service
from app.services.questrade_service import questrade_service
from app.services.ibkr_service import ibkr_service
from app.utils.logger import logger

router = APIRouter(prefix="/api/strategy", tags=["strategy"])


class WatchlistRequest(BaseModel):
    """Watchlist request model."""
    symbols: List[str]


class ExecuteSignalRequest(BaseModel):
    """Execute signal request model."""
    symbol: str
    side: str
    price: float
    stop_loss: float
    take_profit: float


@router.post("/start")
def start_strategy(db: Session = Depends(get_db)):
    """Start the trading strategy."""
    if strategy_service.is_running():
        raise HTTPException(status_code=400, detail="Strategy is already running")
    
    # Authenticate with APIs
    if not questrade_service.access_token:
        auth_success = questrade_service.authenticate()
        if not auth_success:
            logger.warning("Questrade authentication failed, continuing without market data")
    
    if not ibkr_service.connected:
        conn_success = ibkr_service.connect()
        if not conn_success:
            logger.warning("IBKR connection failed, continuing without order execution")
    
    strategy_service.start()
    logger.info("Trading strategy started")
    
    return {"message": "Strategy started successfully", "status": "running"}


@router.post("/stop")
def stop_strategy():
    """Stop the trading strategy."""
    if not strategy_service.is_running():
        raise HTTPException(status_code=400, detail="Strategy is not running")
    
    strategy_service.stop()
    logger.info("Trading strategy stopped")
    
    return {"message": "Strategy stopped successfully", "status": "stopped"}


@router.get("/status")
def get_strategy_status():
    """Get strategy status."""
    return {
        'running': strategy_service.is_running(),
        'watchlist': strategy_service.watchlist,
        'questrade_connected': questrade_service.access_token is not None,
        'ibkr_connected': ibkr_service.connected
    }


@router.post("/watchlist")
def update_watchlist(request: WatchlistRequest):
    """Update the watchlist."""
    if not request.symbols:
        raise HTTPException(status_code=400, detail="Watchlist cannot be empty")
    
    # Validate symbols
    valid_symbols = [s.upper().strip() for s in request.symbols if s.strip()]
    
    strategy_service.set_watchlist(valid_symbols)
    
    return {
        "message": "Watchlist updated successfully",
        "watchlist": valid_symbols
    }


@router.get("/watchlist")
def get_watchlist():
    """Get current watchlist."""
    return {"watchlist": strategy_service.watchlist}


@router.post("/scan")
def scan_for_signals(db: Session = Depends(get_db)):
    """Manually trigger a signal scan."""
    if not strategy_service.is_running():
        raise HTTPException(status_code=400, detail="Strategy is not running")
    
    signals = strategy_service.scan_for_signals(db)
    
    return {
        "message": f"Scan complete - found {len(signals)} signals",
        "signals": signals
    }


@router.post("/execute-signal")
def execute_signal(request: ExecuteSignalRequest, db: Session = Depends(get_db)):
    """Manually execute a trading signal."""
    # Get account equity
    account_state = risk_service.get_current_account_state(db)
    account_equity = account_state.get('total_equity', 100000)  # Default if not set
    
    # Create signal dict
    signal = {
        'symbol': request.symbol,
        'side': request.side,
        'price': request.price,
        'stop_loss': request.stop_loss,
        'take_profit': request.take_profit,
        'confluence_score': 3,  # Manual execution
        'indicators': {}
    }
    
    # Execute signal
    trade = strategy_service.execute_signal(db, signal, account_equity)
    
    if not trade:
        raise HTTPException(status_code=400, detail="Failed to execute signal")
    
    return {
        "message": "Signal executed successfully",
        "trade_id": trade.id,
        "symbol": trade.symbol,
        "side": trade.side.value,
        "quantity": trade.quantity
    }


@router.post("/circuit-breaker/activate")
def activate_circuit_breaker(reason: str):
    """Manually activate circuit breaker."""
    risk_service.activate_circuit_breaker(reason)
    return {"message": "Circuit breaker activated", "reason": reason}


@router.post("/circuit-breaker/deactivate")
def deactivate_circuit_breaker():
    """Deactivate circuit breaker."""
    risk_service.deactivate_circuit_breaker()
    return {"message": "Circuit breaker deactivated"}
