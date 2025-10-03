"""
Test database connectivity.
"""

import psycopg2
from config import config


def test_db_connection():
    """Test PostgreSQL database connectivity."""
    print("Testing database connection...\n")
    print(f"Connecting to: {config._mask_value(config.database_url, 20)}...\n")
    
    try:
        # Try to connect
        conn = psycopg2.connect(config.database_url)
        cursor = conn.cursor()
        
        # Execute a simple query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        print("✓ Database connection successful!")
        print(f"PostgreSQL version: {version}\n")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed!")
        print(f"Error: {e}\n")
        return False


if __name__ == "__main__":
    test_db_connection()
