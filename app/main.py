"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.config import settings
from app.database import init_db
from app.routers import trades, positions, dashboard, strategy
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Algo Trading System")
    logger.info(f"Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Algo Trading System")


# Create FastAPI app
app = FastAPI(
    title="Algorithmic Swing Trading System",
    description="Professional trading platform for swing trading US equity stocks",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(dashboard.router)
app.include_router(trades.router)
app.include_router(positions.router)
app.include_router(strategy.router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "debug": settings.DEBUG
    }


@app.get("/api/config")
def get_config():
    """Get application configuration (non-sensitive)."""
    return {
        "max_concurrent_positions": settings.MAX_CONCURRENT_POSITIONS,
        "max_position_risk_pct": settings.MAX_POSITION_RISK_PCT,
        "max_daily_loss_pct": settings.MAX_DAILY_LOSS_PCT,
        "max_drawdown_pct": settings.MAX_DRAWDOWN_PCT,
        "stop_loss_pct": settings.STOP_LOSS_PCT,
        "take_profit_multiplier": settings.TAKE_PROFIT_MULTIPLIER,
        "rsi_period": settings.RSI_PERIOD,
        "adx_threshold": settings.ADX_THRESHOLD
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
