"""Positions router for position management endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.position import Position
from app.models.trade import Trade, TradeStatus
from app.schemas.position import PositionResponse
from app.services.ibkr_service import ibkr_service

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.get("/", response_model=List[PositionResponse])
def get_positions(db: Session = Depends(get_db)):
    """Get all current positions."""
    positions = db.query(Position).all()
    return positions


@router.get("/{symbol}", response_model=PositionResponse)
def get_position(symbol: str, db: Session = Depends(get_db)):
    """Get position for a specific symbol."""
    position = db.query(Position).filter(Position.symbol == symbol).first()
    
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    return position


@router.get("/open-trades/all")
def get_open_trades(db: Session = Depends(get_db)):
    """Get all open trades (positions)."""
    open_trades = db.query(Trade).filter(
        Trade.status == TradeStatus.OPEN
    ).all()
    
    result = []
    for trade in open_trades:
        # Get current price if IBKR is connected
        current_price = trade.entry_price
        if ibkr_service.connected:
            price = ibkr_service.get_current_price(trade.symbol)
            if price:
                current_price = price
        
        # Calculate unrealized P&L
        if trade.side.value == "BUY":
            unrealized_pnl = (current_price - trade.entry_price) * trade.quantity
        else:
            unrealized_pnl = (trade.entry_price - current_price) * trade.quantity
        
        result.append({
            'trade_id': trade.id,
            'symbol': trade.symbol,
            'side': trade.side.value,
            'quantity': trade.quantity,
            'entry_price': trade.entry_price,
            'current_price': current_price,
            'unrealized_pnl': unrealized_pnl,
            'stop_loss': trade.stop_loss,
            'take_profit': trade.take_profit,
            'entry_time': trade.entry_time.isoformat()
        })
    
    return result


@router.post("/sync-ibkr")
def sync_positions_from_ibkr(db: Session = Depends(get_db)):
    """Sync positions from IBKR."""
    if not ibkr_service.connected:
        raise HTTPException(status_code=400, detail="IBKR not connected")
    
    ibkr_positions = ibkr_service.get_positions()
    
    # Update database positions
    for ibkr_pos in ibkr_positions:
        position = db.query(Position).filter(
            Position.symbol == ibkr_pos['symbol']
        ).first()
        
        if position:
            position.quantity = ibkr_pos['position']
            position.avg_price = ibkr_pos['avg_cost']
            position.current_price = ibkr_pos['avg_cost']
            position.market_value = ibkr_pos['market_value']
            position.unrealized_pnl = 0  # Will be calculated
        else:
            position = Position(
                symbol=ibkr_pos['symbol'],
                quantity=ibkr_pos['position'],
                avg_price=ibkr_pos['avg_cost'],
                current_price=ibkr_pos['avg_cost'],
                market_value=ibkr_pos['market_value'],
                unrealized_pnl=0
            )
            db.add(position)
    
    db.commit()
    
    return {"message": f"Synced {len(ibkr_positions)} positions from IBKR"}
