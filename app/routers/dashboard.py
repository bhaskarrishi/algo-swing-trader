"""Dashboard router for dashboard and analytics endpoints."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics_service import analytics_service
from app.services.risk_service import risk_service
from app.services.strategy_service import strategy_service

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page."""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/trades", response_class=HTMLResponse)
def trades_page(request: Request):
    """Trades page."""
    return templates.TemplateResponse("trades.html", {"request": request})


@router.get("/analytics", response_class=HTMLResponse)
def analytics_page(request: Request):
    """Analytics page."""
    return templates.TemplateResponse("analytics.html", {"request": request})


@router.get("/api/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get dashboard summary data."""
    # Performance metrics
    performance = analytics_service.get_performance_summary(db)
    
    # Risk metrics
    risk_metrics = risk_service.get_risk_metrics(db)
    
    # Account state
    account_state = risk_service.get_current_account_state(db)
    
    # Strategy status
    strategy_status = {
        'running': strategy_service.is_running(),
        'watchlist': strategy_service.watchlist
    }
    
    return {
        'performance': performance,
        'risk': risk_metrics,
        'account': account_state,
        'strategy': strategy_status
    }


@router.get("/api/dashboard/chart-data")
def get_chart_data(db: Session = Depends(get_db)):
    """Get chart data for dashboard."""
    # Equity curve
    equity_curve = analytics_service.get_equity_curve(db)
    
    # Daily P&L
    daily_pnl = analytics_service.get_daily_pnl(db, days=30)
    
    # Trade distribution
    distribution = analytics_service.get_trade_distribution(db)
    
    return {
        'equity_curve': equity_curve,
        'daily_pnl': daily_pnl,
        'distribution': distribution
    }


@router.get("/api/dashboard/recent-trades")
def get_recent_trades(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent trades for dashboard."""
    return analytics_service.get_recent_trades(db, limit)
