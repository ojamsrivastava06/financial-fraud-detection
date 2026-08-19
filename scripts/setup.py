"""
Environment setup script to create directory structures and initialize database.
"""

from pathlib import Path
import sys

# Ensure root directory in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.database.connection import init_db
from src.utils.logger import get_logger

logger = get_logger(__name__)


def setup_environment():
    """Initializes project workspace folders and SQLite database schema."""
    logger.info("Setting up project environment and database schema...")
    init_db()
    logger.info("Setup complete. Architecture ready for Phase 2 execution.")


if __name__ == "__main__":
    setup_environment()
