import logging
import threading

from src.wallbot.telegram.handlers import TelegramHandlers
from .database.db_helper import DBHelper
from .telegram.bot import create_bot, recovery
from .utils.logger import setup_logger
from .utils.version import read_version
from waitress import serve
from .web.app import create_web_app
from .wallapop.monitor import WallapopMonitor


def main():
    setup_logger()
    logging.info("JanJanJan starting...")

    db = DBHelper()
    db.setup(read_version())

    bot = create_bot()

    TelegramHandlers(bot, db)

    monitor = WallapopMonitor(db)
    threading.Thread(target=monitor.start, daemon=True).start()

    # Start the web server in a background thread
    # Use a production-ready WSGI server (Waitress) instead of Flask's development server
    web_app = create_web_app(db)
    logging.info("Starting web server on http://0.0.0.0:8080")
    threading.Thread(target=lambda: serve(web_app, host='0.0.0.0', port=8080), daemon=True).start()

    recovery(bot, 1)


if __name__ == '__main__':
    main()
