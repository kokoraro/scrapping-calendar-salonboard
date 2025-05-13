import sys
import os
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from app.db.database import init_db
from app.core.config import settings

def main():
    """Initialize the database."""
    print("Initializing database...")
    init_db()
    print("Database initialization completed.")

if __name__ == "__main__":
    main() 