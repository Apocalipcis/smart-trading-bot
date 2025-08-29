"""Database migration system for schema updates."""

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class DatabaseMigration:
    """Handles database schema migrations."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.migrations_table = "schema_migrations"
    
    async def run_migrations(self) -> None:
        """Run all pending migrations."""
        try:
            # Create migrations table if it doesn't exist
            await self._create_migrations_table()
            
            # Get current schema version
            current_version = await self._get_current_version()
            
            # Get all available migrations
            available_migrations = self._get_available_migrations()
            
            # Run pending migrations
            for version, migration_func in available_migrations:
                if version > current_version:
                    logger.info(f"Running migration {version}: {migration_func.__name__}")
                    await migration_func()
                    await self._update_version(version)
                    logger.info(f"Migration {version} completed successfully")
            
            logger.info("All migrations completed successfully")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    async def _create_migrations_table(self) -> None:
        """Create the migrations tracking table."""
        conn = await self._get_connection()
        try:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            conn.close()
    
    async def _get_current_version(self) -> int:
        """Get the current schema version."""
        try:
            conn = await self._get_connection()
            try:
                cursor = conn.execute(f"SELECT MAX(version) FROM {self.migrations_table}")
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else 0
            finally:
                conn.close()
        except Exception:
            return 0
    
    async def _update_version(self, version: int) -> None:
        """Update the schema version."""
        conn = await self._get_connection()
        try:
            conn.execute(
                f"INSERT INTO {self.migrations_table} (version, name) VALUES (?, ?)",
                (version, f"migration_{version}")
            )
            conn.commit()
        finally:
            conn.close()
    
    def _get_available_migrations(self) -> List[Tuple[int, callable]]:
        """Get all available migrations in order."""
        return [
            (1, self._migration_001_update_pairs_table),
            (2, self._migration_002_add_missing_columns),
            (3, self._migration_003_verify_schema),
        ]
    
    async def _migration_001_update_pairs_table(self) -> None:
        """Migration 1: Update pairs table schema to match expected structure."""
        conn = await self._get_connection()
        try:
            # Check current table structure
            cursor = conn.execute("PRAGMA table_info(pairs)")
            columns = {col[1] for col in cursor.fetchall()}
            
            # If the table has the old schema (exchange column), recreate it completely
            if 'exchange' in columns or 'id' not in columns:
                logger.info("Detected old pairs table schema, recreating table")
                await self._recreate_pairs_table()
            else:
                logger.info("Pairs table already has correct schema")
            
            conn.commit()
        finally:
            conn.close()
    
    async def _migration_002_add_missing_columns(self) -> None:
        """Migration 2: Add missing columns to pairs table."""
        conn = await self._get_connection()
        try:
            cursor = conn.execute("PRAGMA table_info(pairs)")
            columns = {col[1] for col in cursor.fetchall()}
            
            # Add strategy column if missing
            if 'strategy' not in columns:
                conn.execute("ALTER TABLE pairs ADD COLUMN strategy TEXT DEFAULT 'SMC'")
                logger.info("Added strategy column to pairs table")
            
            # Add is_active column if missing
            if 'is_active' not in columns:
                conn.execute("ALTER TABLE pairs ADD COLUMN is_active BOOLEAN DEFAULT 1")
                logger.info("Added is_active column to pairs table")
            
            # Update existing rows to have sensible defaults
            conn.execute("UPDATE pairs SET strategy = 'SMC' WHERE strategy IS NULL")
            conn.execute("UPDATE pairs SET is_active = 1 WHERE is_active IS NULL")
            
            conn.commit()
        finally:
            conn.close()
    
    async def _recreate_pairs_table(self) -> None:
        """Recreate the pairs table with proper schema."""
        conn = await self._get_connection()
        try:
            # Create new table with correct schema
            conn.execute("""
                CREATE TABLE pairs_new (
                    id TEXT PRIMARY KEY,
                    symbol TEXT UNIQUE NOT NULL,
                    base_asset TEXT,
                    quote_asset TEXT,
                    strategy TEXT NOT NULL DEFAULT 'SMC',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Copy data from old table, handling both old and new schemas
            try:
                conn.execute("""
                    INSERT INTO pairs_new (id, symbol, base_asset, quote_asset, strategy, is_active, created_at, updated_at)
                    SELECT id, symbol, base_asset, quote_asset, 
                           COALESCE(strategy, 'SMC') as strategy,
                           COALESCE(is_active, 1) as is_active,
                           created_at, updated_at
                    FROM pairs
                """)
            except sqlite3.OperationalError:
                # If the old table doesn't have these columns, use defaults
                conn.execute("""
                    INSERT INTO pairs_new (id, symbol, base_asset, quote_asset, strategy, is_active, created_at, updated_at)
                    SELECT 
                        COALESCE(id, symbol) as id,
                        symbol,
                        COALESCE(base_asset, '') as base_asset,
                        COALESCE(quote_asset, '') as quote_asset,
                        'SMC' as strategy,
                        1 as is_active,
                        COALESCE(created_at, CURRENT_TIMESTAMP) as created_at,
                        COALESCE(updated_at, CURRENT_TIMESTAMP) as updated_at
                    FROM pairs
                """)
            
            # Drop old table and rename new one
            conn.execute("DROP TABLE pairs")
            conn.execute("ALTER TABLE pairs_new RENAME TO pairs")
            
            conn.commit()
            logger.info("Pairs table recreated with correct schema")
        finally:
            conn.close()
    
    async def _migration_003_verify_schema(self) -> None:
        """Migration 3: Verify that the pairs table has the correct schema."""
        conn = await self._get_connection()
        try:
            cursor = conn.execute("PRAGMA table_info(pairs)")
            columns = {col[1] for col in cursor.fetchall()}
            
            required_columns = {'id', 'symbol', 'base_asset', 'quote_asset', 'strategy', 'is_active', 'created_at', 'updated_at'}
            missing_columns = required_columns - columns
            
            if missing_columns:
                logger.warning(f"Missing columns in pairs table: {missing_columns}")
                # Recreate the table if any required columns are missing
                await self._recreate_pairs_table()
            else:
                logger.info("Pairs table schema verification passed")
            
            conn.commit()
        finally:
            conn.close()
    
    async def _get_connection(self):
        """Get a database connection for migrations."""
        # For migrations, we need a direct connection
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn


async def run_database_migrations(db_path: Path) -> None:
    """Run database migrations for the given database path."""
    migration = DatabaseMigration(db_path)
    await migration.run_migrations()
