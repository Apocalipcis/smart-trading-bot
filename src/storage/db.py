"""Database management for the trading bot."""

import asyncio
import json
import logging
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import structlog

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """Manages SQLite database connections and operations."""
    
    def __init__(self, db_path: str = "/data/app.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize the database with schema and indexes."""
        async with self._lock:
            try:
                # Create connection
                self._connection = sqlite3.connect(
                    str(self.db_path),
                    check_same_thread=False,
                    timeout=30.0
                )
                
                # Enable WAL mode for better concurrency
                self._connection.execute("PRAGMA journal_mode=WAL")
                self._connection.execute("PRAGMA synchronous=NORMAL")
                self._connection.execute("PRAGMA cache_size=10000")
                self._connection.execute("PRAGMA temp_store=MEMORY")
                
                # Create tables
                await self._create_tables()
                
                # Run migrations to update schema if needed
                from .migrations import run_database_migrations
                await run_database_migrations(self.db_path)
                
                # Create indexes
                await self._create_indexes()
                
                # Insert default settings
                await self._insert_default_settings()
                
                logger.info("Database initialized successfully", db_path=str(self.db_path))
                
            except Exception as e:
                logger.error("Failed to initialize database", error=str(e))
                raise
    
    async def close(self) -> None:
        """Close the database connection."""
        async with self._lock:
            if self._connection:
                try:
                    # Close WAL mode files first
                    self._connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    self._connection.commit()
                    
                    # Close the connection
                    self._connection.close()
                    self._connection = None
                    
                    # Give Windows time to release file handles
                    import asyncio
                    await asyncio.sleep(0.1)
                    
                    logger.info("Database connection closed")
                except Exception as e:
                    logger.warning("Error during database close", error=str(e))
                    # Force close even if there's an error
                    try:
                        self._connection.close()
                    except:
                        pass
                    self._connection = None
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection with proper error handling."""
        if not self._connection:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        try:
            yield self._connection
        except sqlite3.Error as e:
            logger.error("Database error", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected database error", error=str(e))
            raise
    
    async def _create_tables(self) -> None:
        """Create database tables."""
        async with self.get_connection() as conn:
            # Settings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Pairs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pairs (
                    id TEXT PRIMARY KEY,
                    symbol TEXT UNIQUE NOT NULL,
                    base_asset TEXT,
                    quote_asset TEXT,
                    strategy TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Signals table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id TEXT PRIMARY KEY,
                    pair TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    side TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    confidence REAL NOT NULL,
                    metadata TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Orders table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    signal_id TEXT,
                    pair TEXT NOT NULL,
                    side TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL,
                    status TEXT NOT NULL,
                    exchange_order_id TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Backtest metadata table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backtest_metadata (
                    id TEXT PRIMARY KEY,
                    pair TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    file_path TEXT NOT NULL,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("Database tables created successfully")
    
    async def _create_indexes(self) -> None:
        """Create database indexes for fast queries."""
        async with self.get_connection() as conn:
            # Signals indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_pair ON signals(pair)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_strategy ON signals(strategy)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_side ON signals(side)")
            
            # Orders indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_pair ON orders(pair)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_signal_id ON orders(signal_id)")
            
            # Backtest metadata indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_backtest_pair ON backtest_metadata(pair)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_backtest_strategy ON backtest_metadata(strategy)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_backtest_created_at ON backtest_metadata(created_at)")
            
            # Pairs indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pairs_symbol ON pairs(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pairs_strategy ON pairs(strategy)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pairs_is_active ON pairs(is_active)")
            
            conn.commit()
            logger.info("Database indexes created successfully")
    
    async def _insert_default_settings(self) -> None:
        """Insert default settings if they don't exist."""
        default_settings = [
            ("TRADING_ENABLED", "false", "bool", "Enable/disable live trading"),
            ("ORDER_CONFIRMATION_REQUIRED", "true", "bool", "Require manual confirmation for orders"),
            ("MAX_OPEN_POSITIONS", "5", "int", "Maximum number of open positions"),
            ("MAX_RISK_PER_TRADE", "2.0", "float", "Maximum risk per trade as percentage"),
            ("MIN_RISK_REWARD_RATIO", "3.0", "float", "Minimum risk-reward ratio required"),
            ("DEFAULT_COMMISSION", "0.001", "float", "Default commission rate for backtests"),
            ("DEFAULT_SLIPPAGE", "0.0001", "float", "Default slippage for backtests"),
            ("DEFAULT_INITIAL_CAPITAL", "10000.0", "float", "Default initial capital for backtests"),
            ("DATA_STORAGE_FORMAT", "parquet", "string", "Historical data storage format"),
            ("DATA_RETENTION_DAYS", "365", "int", "Data retention in days"),
            ("DATA_COMPRESSION", "true", "bool", "Enable data compression"),
            ("LOG_LEVEL", "INFO", "string", "Logging level"),
            ("DEBUG_MODE", "false", "bool", "Debug mode for verbose logging"),
        ]
        
        async with self.get_connection() as conn:
            for key, value, type_name, description in default_settings:
                conn.execute("""
                    INSERT OR IGNORE INTO settings (key, value, type, description)
                    VALUES (?, ?, ?, ?)
                """, (key, value, type_name, description))
            
            conn.commit()
            logger.info("Default settings inserted successfully")
    
    async def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries."""
        async with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            columns = [description[0] for description in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
    
    async def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an update query and return number of affected rows."""
        async with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    async def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute an insert query and return the last row ID."""
        async with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            async with self.get_connection() as conn:
                # Check if database is accessible
                cursor = conn.execute("SELECT COUNT(*) FROM settings")
                settings_count = cursor.fetchone()[0]
                
                # Check database file size
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    "status": "healthy",
                    "settings_count": settings_count,
                    "db_size_bytes": db_size,
                    "db_path": str(self.db_path),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        raise RuntimeError("Database manager not initialized")
    return _db_manager


async def initialize_database(db_path: str = "/data/app.db") -> DatabaseManager:
    """Initialize the global database manager."""
    global _db_manager
    _db_manager = DatabaseManager(db_path)
    await _db_manager.initialize()
    return _db_manager


async def close_database() -> None:
    """Close the global database manager."""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None
