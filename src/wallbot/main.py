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
from .wallapop.search_monitor import check_saved_searches


def main():
    logging.info("JanJanJan starting...")

    db = DBHelper()
    db.setup(read_version())

    bot = create_bot()

    TelegramHandlers(bot, db)

    monitor = WallapopMonitor(db)
    threading.Thread(target=monitor.start, daemon=True).start()

    # Start the search monitor in a separate thread
    threading.Thread(target=check_saved_searches, daemon=True).start()

    recovery(bot, 1)


if __name__ == '__main__':
    main()
