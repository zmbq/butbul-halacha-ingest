"""
Run script for the ingestion pipeline.
This script sets up the Python path correctly and runs the main ingestion.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import and run
from src.main import main

if __name__ == "__main__":
    main()
