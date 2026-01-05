"""Database initialization script."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.models import (
    Trade, Position, Order, MarketData, Indicator,
    AccountState, StrategyParameter, Alert
)
from app.utils.logger import logger


def init_database():
    """Initialize database tables."""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        
        # Print created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Created tables: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        return False


def drop_all_tables():
    """Drop all database tables (use with caution!)."""
    response = input("Are you sure you want to drop all tables? (yes/no): ")
    if response.lower() != "yes":
        logger.info("Operation cancelled")
        return
    
    try:
        logger.info("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully!")
        
    except Exception as e:
        logger.error(f"Failed to drop tables: {str(e)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop all tables before creating (WARNING: deletes all data)"
    )
    
    args = parser.parse_args()
    
    if args.drop:
        drop_all_tables()
    
    success = init_database()
    
    if success:
        logger.info("\n✅ Database is ready!")
        logger.info("You can now start the application with: uvicorn app.main:app --reload")
    else:
        logger.error("\n❌ Database initialization failed!")
        sys.exit(1)
