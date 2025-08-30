"""Test configuration and fixtures for the trading bot."""

import asyncio
import os
import pytest
import tempfile
import shutil
import sqlite3
from pathlib import Path
from typing import AsyncGenerator, Generator

from fastapi.testclient import TestClient

from src.storage.db import DatabaseManager


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_path() -> AsyncGenerator[str, None]:
    """Create a temporary database path for testing."""
    # Create a temporary directory for test data in the project directory
    # to ensure it's completely isolated from any existing databases
    test_dir = Path(__file__).parent / "test_data"
    
    # Clean up any existing test data
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    test_dir.mkdir(exist_ok=True)
    
    db_path = str(test_dir / "test.db")
    
    # Set environment variable for the test database
    os.environ["DB_PATH"] = db_path
    os.environ["DATA_DIR"] = str(test_dir)
    
    yield db_path
    
    # Cleanup
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
        if test_dir.exists():
            shutil.rmtree(test_dir)
    except Exception:
        pass


@pytest.fixture(scope="session")
async def initialized_db(test_db_path: str) -> AsyncGenerator[None, None]:
    """Initialize the database for testing with correct schema."""
    # Create a test database manager that doesn't run migrations
    db_manager = DatabaseManager(test_db_path)
    
    # Initialize the database with the correct schema directly
    await db_manager.initialize()
    
    # Set the global database manager for the test session
    from src.storage.db import _db_manager
    import src.storage.db
    src.storage.db._db_manager = db_manager
    
    yield
    
    # Cleanup database
    await db_manager.close()
    src.storage.db._db_manager = None


@pytest.fixture
def test_app(initialized_db):
    """Create a test app with initialized database."""
    from src.api.main import app
    
    # The database is already initialized by the initialized_db fixture
    # and the app will use it through the global database manager
    return app


@pytest.fixture
def client(test_app) -> Generator[TestClient, None, None]:
    """Create a test client with initialized database."""
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
async def setup_test_environment(initialized_db):
    """Setup test environment before each test."""
    # This fixture runs automatically for each test
    # The database is already initialized by initialized_db fixture
    pass
