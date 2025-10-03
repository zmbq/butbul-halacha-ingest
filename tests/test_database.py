"""
Test database connectivity and operations.
"""

import pytest
import psycopg2
from src.config import config
from src.database import init_db, get_db, Video


def test_db_connection():
    """Test PostgreSQL database connectivity."""
    try:
        # Try to connect
        conn = psycopg2.connect(config.database_url)
        cursor = conn.cursor()
        
        # Execute a simple query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        assert version is not None
        assert "PostgreSQL" in version[0]
        
        cursor.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        pytest.skip(f"Database not accessible: {e}")


def test_database_table_creation():
    """Test that database tables can be created."""
    try:
        init_db()
        # If we get here without exception, table creation worked
        assert True
    except psycopg2.OperationalError as e:
        pytest.skip(f"Database not accessible: {e}")


def test_database_session():
    """Test that we can get a database session."""
    try:
        db = get_db()
        assert db is not None
        db.close()
    except psycopg2.OperationalError as e:
        pytest.skip(f"Database not accessible: {e}")


# Standalone script mode for manual testing
if __name__ == "__main__":
    print("Testing database connection...\n")
    print(f"Connecting to: {config._mask_value(config.database_url, 20)}...\n")
    
    try:
        conn = psycopg2.connect(config.database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        print("✓ Database connection successful!")
        print(f"PostgreSQL version: {version}\n")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Database connection failed!")
        print(f"Error: {e}\n")
