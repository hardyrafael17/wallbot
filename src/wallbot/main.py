import logging
import threading
import asyncio

from src.wallbot.telegram.handlers import TelegramHandlers
from .database.db_helper import DBHelper
from .telegram.bot import create_application
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

    application = create_application()

    TelegramHandlers(application, db)

    monitor = WallapopMonitor(db)
    threading.Thread(target=monitor.start, daemon=True).start()

    # Start the search monitor in a separate thread
    threading.Thread(target=lambda: asyncio.run(check_saved_searches()), daemon=True).start()

    application.run_polling()


if __name__ == '__main__':
    main()