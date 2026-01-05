"""Trades router for trade management endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.trade import Trade, TradeStatus
from app.schemas.trade import TradeResponse
from app.utils.logger import logger

router = APIRouter(prefix="/api/trades", tags=["trades"])


@router.get("/", response_model=List[TradeResponse])
def get_trades(
    status: str = None,
    symbol: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of trades with optional filters."""
    query = db.query(Trade)
    
    if status:
        try:
            query = query.filter(Trade.status == TradeStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status value")
    
    if symbol:
        query = query.filter(Trade.symbol == symbol)
    
    trades = query.order_by(Trade.entry_time.desc()).limit(limit).all()
    return trades


@router.get("/{trade_id}", response_model=TradeResponse)
def get_trade(trade_id: int, db: Session = Depends(get_db)):
    """Get a specific trade by ID."""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return trade


@router.get("/symbol/{symbol}", response_model=List[TradeResponse])
def get_trades_by_symbol(symbol: str, db: Session = Depends(get_db)):
    """Get all trades for a specific symbol."""
    trades = db.query(Trade).filter(
        Trade.symbol == symbol
    ).order_by(Trade.entry_time.desc()).all()
    
    return trades


@router.delete("/{trade_id}")
def delete_trade(trade_id: int, db: Session = Depends(get_db)):
    """Delete a trade (admin only)."""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade.status == TradeStatus.OPEN:
        raise HTTPException(status_code=400, detail="Cannot delete open trade")
    
    db.delete(trade)
    db.commit()
    
    logger.info(f"Deleted trade {trade_id}")
    return {"message": "Trade deleted successfully"}
