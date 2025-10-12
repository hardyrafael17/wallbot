import logging
import os
import sys

# Add the project root to the Python path to allow imports from 'src'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.wallbot.database.db_helper import (
    get_all_saved_searches,
    setup_database,
)


def main():
    """Connects to the database and prints all saved searches."""
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info("Connecting to database to show saved searches...")
    setup_database()  # Ensures the database and tables exist
    searches = get_all_saved_searches()
    logging.info(f"Found {len(searches)} saved searches:")
    for search in searches:
        logging.info(f"- ID: {search.id}, Keywords: '{search.keywords}', Chat ID: {search.chat_id}")

if __name__ == "__main__":
    main()